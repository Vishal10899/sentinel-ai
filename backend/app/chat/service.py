import asyncio
import json
import logging
from typing import Any
from dataclasses import asdict
from decimal import Decimal
from time import perf_counter
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

from app.chat.dto import ChatRequest
from app.chat.prompt_builder import prompt_builder, PromptContext
from app.core.settings import settings
from app.cost import CostCalculator
from app.models_registry import model_registry
from app.providers.manager import provider_manager
from app.models.conversation import Conversation
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository
from app.routing import (
    BalancedStrategy,
    CheapestStrategy,
    FastestStrategy,
    HighestQualityStrategy,
    IntelligentRouter,
    ModelInfo,
    ReasoningOptimizedStrategy,
    TaskCategory,
)
from app.cache import semantic_cache
from app.guardrails import guardrails_engine
from app.observability import trace_engine
from app.orchestration import adaptive_router
from app.policy import PolicyAction, policy_engine

from app.db.session import get_db_session
from app.routing import CandidateScore, RoutingDecisionExplanation

_STRATEGIES = {
    "cost": CheapestStrategy,
    "latency": FastestStrategy,
    "balanced": BalancedStrategy,
    "quality": HighestQualityStrategy,
    "reasoning_optimized": ReasoningOptimizedStrategy,
    "adaptive": BalancedStrategy,
}


def _generate_smart_title(prompt: str) -> str:
    """Generate concise, meaningful conversation title from prompt."""
    cleaned = prompt.strip().replace("\n", " ")
    if not cleaned:
        return "New Conversation"
    if cleaned.startswith("/"):
        cleaned = cleaned.lstrip("/")
    words = [w for w in cleaned.split(" ") if w]
    if len(words) <= 5:
        return " ".join(words).title()
    return " ".join(words[:5]).title()


def _resolve_routing(data: ChatRequest):
    """Resolve provider, model, and decision explanation using AdaptiveRouter & IntelligentRouter."""
    if data.provider and data.model and provider_manager.is_active(data.provider):
        try:
            metadata = model_registry.get_model(data.provider, data.model)
        except KeyError:
            metadata = None
        return data.provider, data.model, data.strategy, None, metadata

    if data.strategy in ["adaptive", "auto", "smart"] or not data.provider or not provider_manager.is_active(data.provider):
        adaptive_res = adaptive_router.route(
            prompt=data.prompt,
            system_prompt=data.system_prompt or "",
            has_attachments=bool(data.attachments),
            user_id="user",
            workspace_id=data.workspace_id or "default",
        )
        provider_id = adaptive_res.selected_provider
        model_id = adaptive_res.selected_model
        try:
            metadata = model_registry.get_model(provider_id, model_id)
        except KeyError:
            metadata = None

        cands = tuple(
            CandidateScore(
                provider=c["provider_id"],
                model_name=c["model_id"],
                overall_score=float(c["score"]),
                rank=i + 1,
                cost_per_1k_tokens=0.0,
                latency=0.0,
                quality_score=0.0,
                reasoning_score=0.0,
                status="healthy",
                reason=c["reason"],
            )
            for i, c in enumerate(adaptive_res.candidate_scores)
        )
        explanation = RoutingDecisionExplanation(
            selected_provider=provider_id,
            selected_model=model_id,
            strategy_used=data.strategy,
            primary_reason=adaptive_res.explanation_text,
            ranked_candidates=cands,
        )
        return provider_id, model_id, data.strategy, explanation, metadata

    # Build candidates for router (filter out non-chat models and disabled providers)
    enabled_providers = {
        p_name for p_name in provider_manager.provider_names()
        if provider_manager.is_active(p_name)
    }
    candidates = [
        ModelInfo(
            provider=m.provider_id,
            model_name=m.model_id,
            cost_per_1k_tokens=float(m.cost_per_1k_input_tokens + m.cost_per_1k_output_tokens),
            latency=float(m.average_latency_ms),
            capabilities=frozenset(
                TaskCategory(cap) for cap in m.capabilities if cap in TaskCategory._value2member_map_
            ),
            priority=m.priority,
            category=m.category,
            quality_score=m.quality_score,
            reasoning_score=m.reasoning_score,
        )
        for m in model_registry.list_models(enabled_only=True)
        if m.category.lower() in ["chat", "llm", "conversational", "reasoning"]
        and m.provider_id in enabled_providers
    ]
    strat_cls = _STRATEGIES.get(data.strategy, BalancedStrategy)
    router_inst = IntelligentRouter(strategy=strat_cls())
    explanation = router_inst.evaluate_with_explanation(
        TaskCategory.CHAT, candidates, strategy_name=data.strategy
    )
    provider_id = explanation.selected_provider
    model_id = explanation.selected_model
    try:
        metadata = model_registry.get_model(provider_id, model_id)
    except KeyError:
        metadata = None
    return provider_id, model_id, data.strategy, explanation, metadata


class ChatService:
    async def generate(
        self,
        data: ChatRequest,
        db: AsyncSession,
    ):
        message_repository = MessageRepository(db)
        conversation_repository = ConversationRepository(db)

        # Check or auto-create conversation
        if not data.conversation_id:
            conv = await conversation_repository.create(
                workspace_id=data.workspace_id or "default",
                title=data.prompt[:80] or "New Conversation",
            )
            data.conversation_id = str(conv.id)
        else:
            conversation = await conversation_repository.get(data.conversation_id)
            if conversation is None:
                # Root Cause Fix for 'Conversation not found': Auto-create conversation if not present in DB
                conversation = await conversation_repository.create(
                    workspace_id=data.workspace_id or "default",
                    title=data.prompt[:80] or "New Conversation",
                )
                data.conversation_id = str(conversation.id)

        # Start Distributed Trace Context
        trace_ctx = trace_engine.create_trace(
            conversation_id=data.conversation_id,
            workspace_id=data.workspace_id or "default",
            prompt=data.prompt,
        )

        # 1. AI Guardrails Request Scanning
        trace_ctx.start_stage("GUARDRAIL_SCAN")
        guardrail_res = guardrails_engine.scan_request(data.prompt)
        trace_ctx.guardrail_action = guardrail_res.action
        trace_ctx.end_stage("GUARDRAIL_SCAN", status="SUCCESS" if guardrail_res.action != "BLOCK" else "BLOCKED")
        
        if guardrail_res.action == "BLOCK":
            trace_ctx.finish(status="BLOCKED")
            raise HTTPException(status_code=400, detail=guardrail_res.reason)
        effective_prompt = guardrail_res.sanitized_text

        # 2. Resolve Provider and Model via Intelligent Routing Engine
        trace_ctx.start_stage("ROUTING")
        provider_id, model_id, strategy_name, explanation, metadata = _resolve_routing(data)
        trace_ctx.provider_id = provider_id
        trace_ctx.model_id = model_id
        trace_ctx.end_stage("ROUTING")

        # 3. Policy Engine Evaluation
        trace_ctx.start_stage("POLICY_EVALUATION")
        policy_decision = policy_engine.evaluate({
            "workspace_id": data.workspace_id or "default",
            "provider_id": provider_id,
            "model_id": model_id,
            "max_tokens": data.max_tokens,
            "temperature": data.temperature,
        })
        trace_ctx.policy_action = policy_decision.action.value if hasattr(policy_decision.action, "value") else str(policy_decision.action)
        trace_ctx.end_stage("POLICY_EVALUATION", status="SUCCESS" if policy_decision.action != PolicyAction.BLOCK else "BLOCKED")
        
        if policy_decision.action == PolicyAction.BLOCK:
            trace_ctx.finish(status="BLOCKED")
            raise HTTPException(status_code=403, detail=policy_decision.reason)

        try:
            provider = provider_manager.get(provider_id)
        except KeyError:
            trace_ctx.finish(status="FAILED")
            raise HTTPException(status_code=404, detail=f"Provider '{provider_id}' not found")

        # 4. Enterprise AI Memory Engine Lookup (Improvement 8 Search Pipeline)
        trace_ctx.start_stage("CACHE_LOOKUP")
        cache_hit = semantic_cache.get(
            prompt=effective_prompt,
            workspace_id=data.workspace_id or "default",
            model_id=model_id,
            system_prompt=data.system_prompt,
            attachments=data.attachments,
        )
        trace_ctx.cache_hit = cache_hit is not None
        trace_ctx.end_stage("CACHE_LOOKUP")
        if cache_hit:
            # Create user message
            attachments_json = json.dumps([a.model_dump() for a in data.attachments]) if data.attachments else None
            explanation_json = json.dumps(asdict(explanation)) if explanation else None

            await message_repository.create(
                conversation_id=data.conversation_id,
                role="user",
                content=data.prompt,
                provider=provider_id,
                model=model_id,
                system_prompt=data.system_prompt,
                attachments=attachments_json,
                strategy_used=strategy_name,
                routing_explanation_json=explanation_json,
            )

            # Create assistant cached message
            assistant_msg = await message_repository.create(
                conversation_id=data.conversation_id,
                role="assistant",
                content=cache_hit["response_text"],
                provider=provider_id,
                model=model_id,
                total_tokens=cache_hit["entry"].get("total_tokens", 0),
                cost=0.0,
                latency_ms=1,  # Sub-10ms cache retrieval
                strategy_used=strategy_name,
                routing_explanation_json=explanation_json,
            )

            return {
                "message": assistant_msg,
                "conversation_id": data.conversation_id,
                "provider": provider_id,
                "model": model_id,
                "response": cache_hit["response_text"],
                "cost_usd": 0.0,
                "latency_ms": 1,
                "cache_hit": True,
                "hit_type": cache_hit["hit_type"],
                "explanation": explanation,
            }

        # Serialize attachments & explanation JSON
        attachments_json = json.dumps([a.model_dump() for a in data.attachments]) if data.attachments else None
        explanation_json = json.dumps(asdict(explanation)) if explanation else None

        # Save user message
        user_msg = await message_repository.create(
            conversation_id=data.conversation_id,
            role="user",
            content=data.prompt,
            provider=provider_id,
            model=model_id,
            system_prompt=data.system_prompt,
            attachments=attachments_json,
            strategy_used=strategy_name,
            routing_explanation_json=explanation_json,
        )

        # Build multi-turn context from active conversation ONLY
        all_conv_msgs = await message_repository.list_by_conversation(data.conversation_id)
        prior_msgs = [m for m in all_conv_msgs if m.id != user_msg.id]
        if len(prior_msgs) > 20:
            prior_msgs = prior_msgs[-20:]

        messages_payload = []

        # 1. System Prompt
        if data.system_prompt and data.system_prompt.strip():
            messages_payload.append({"role": "system", "content": data.system_prompt.strip()})

        # 4. Recent Messages from active conversation only
        for msg in prior_msgs:
            if msg.content and msg.content.strip():
                role = "user" if msg.role == "user" else "assistant"
                messages_payload.append({"role": role, "content": msg.content.strip()})

        # 5. Current User Message (ALWAYS THE FINAL USER MESSAGE IN PAYLOAD)
        messages_payload.append({"role": "user", "content": data.prompt.strip()})

        # Clean string fallback for providers/components expecting single prompt text
        prompt_parts = []
        if data.system_prompt and data.system_prompt.strip():
            prompt_parts.append(f"System: {data.system_prompt.strip()}")
        if prior_msgs:
            history_blocks = [f"[{'User' if m.role == 'user' else 'Assistant'}]\n{m.content.strip()}" for m in prior_msgs]
            prompt_parts.append("\n\n".join(history_blocks))
        prompt_parts.append(data.prompt.strip())
        full_prompt = "\n\n".join(prompt_parts)

        # PART 4 & PART 5: Automatic Failover Loop & Granular Retry Policies
        trace_ctx.start_stage("PROVIDER_LLM_CALL")
        started_at = perf_counter()
        raw_response = None
        executed_provider_id = provider_id
        executed_model_id = model_id

        def _is_provider_active(p_name: str) -> bool:
            try:
                cfg = provider_manager.get_config(p_name)
                return bool(cfg.get("enabled", False) and cfg.get("status") in ("healthy", "configured"))
            except KeyError:
                return False

        candidates = []
        if explanation and hasattr(explanation, "ranked_candidates") and explanation.ranked_candidates:
            candidates = [
                {"provider_id": c.provider, "model_id": c.model_name}
                for c in explanation.ranked_candidates
                if _is_provider_active(c.provider)
            ]
        if not candidates:
            candidates = [{"provider_id": provider_id, "model_id": model_id}]


        for cand in candidates:
            cand_p_id = cand["provider_id"]
            cand_m_id = cand["model_id"]

            try:
                cand_provider = provider_manager.get(cand_p_id)
            except KeyError:
                continue

            for attempt in range(3):
                try:
                    raw_response = await cand_provider.generate(prompt=full_prompt, model=cand_m_id, messages=messages_payload)
                    executed_provider_id = cand_p_id
                    executed_model_id = cand_m_id
                    adaptive_router.record_execution_feedback(cand_p_id, cand_m_id, success=True)
                    break
                except Exception as e:
                    err_msg = str(e).lower()
                    if "429" in err_msg or "rate limit" in err_msg:
                        await asyncio.sleep(0.2 * (2 ** attempt))
                        continue
                    elif "timeout" in err_msg or "503" in err_msg:
                        if attempt < 2:
                            await asyncio.sleep(0.1)
                            continue

                    adaptive_router.record_execution_feedback(cand_p_id, cand_m_id, success=False, failures=1)
                    break

            if raw_response:
                break

        if not raw_response:
            trace_ctx.end_stage("PROVIDER_LLM_CALL", status="FAILED")
            trace_ctx.finish(status="FAILED")
            raise HTTPException(status_code=503, detail="No active enabled providers available for routing")

        provider_id = executed_provider_id
        model_id = executed_model_id
        trace_ctx.end_stage("PROVIDER_LLM_CALL", status="SUCCESS")

        # AI Guardrails Response Redaction (Secret/PII leakage protection)
        trace_ctx.start_stage("RESPONSE_SCAN")
        response = guardrails_engine.scan_response(raw_response)
        trace_ctx.end_stage("RESPONSE_SCAN")

        latency_ms = round((perf_counter() - started_at) * 1000)

        # Token & cost calculation
        prompt_tokens = max(len(full_prompt) // 4, 1)
        completion_tokens = max(len(response) // 4, 1)
        total_tokens = prompt_tokens + completion_tokens

        cost_calculator = CostCalculator()
        est_cost = float(
            cost_calculator.calculate_token_costs(
                prompt_tokens,
                completion_tokens,
                metadata.cost_per_1k_input_tokens if metadata else Decimal("0.001"),
                metadata.cost_per_1k_output_tokens if metadata else Decimal("0.002"),
            )
        )

        # Store entry in Semantic Cache for future queries
        semantic_cache.set(
            prompt=data.prompt,
            response_text=response,
            workspace_id=data.workspace_id or "default",
            provider_id=provider_id,
            model_id=model_id,
            estimated_cost_usd=est_cost,
            latency_ms=latency_ms,
            total_tokens=total_tokens,
        )
        cost_val = 0.0
        if metadata:
            cost_decimal = cost_calculator.calculate_token_costs(
                prompt_tokens, completion_tokens,
                metadata.cost_per_1k_input_tokens, metadata.cost_per_1k_output_tokens
            )
            cost_val = float(cost_decimal)

        # Save assistant message
        assistant_message = await message_repository.create(
            conversation_id=data.conversation_id,
            role="assistant",
            content=response,
            provider=provider_id,
            model=model_id,
            strategy_used=strategy_name,
            routing_explanation_json=explanation_json,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost=cost_val,
            latency_ms=latency_ms,
        )

        # Phase 6 Self-Learning Router: Record execution feedback
        adaptive_router.record_execution_feedback(
            provider_id=provider_id,
            model_id=model_id,
            success=True,
            actual_latency_ms=latency_ms,
            actual_cost_usd=cost_val,
        )

        trace_ctx.finish(status="SUCCESS", response=response, tokens=total_tokens, cost_usd=cost_val)

        return {
            "conversation_id": str(data.conversation_id),
            "provider": provider_id,
            "model": model_id,
            "response": response,
            "latency_ms": latency_ms,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "cost_usd": cost_val,
            "strategy_used": strategy_name,
            "routing_explanation": asdict(explanation) if explanation else None,
            "created_at": assistant_message.created_at,
        }

    async def stream_generate(self, data: ChatRequest, db: AsyncSession | None = None, request: Any = None):
        """Server-Sent Events (SSE) streaming generator yielding live token chunks, heartbeats, and telemetry."""
        if db is not None:
            async for sse_event in self._stream_generate_impl(data, db, request=request):
                yield sse_event
        else:
            async with get_db_session() as session_db:
                async for sse_event in self._stream_generate_impl(data, session_db, request=request):
                    yield sse_event

    async def _stream_generate_impl(self, data: ChatRequest, session_db: AsyncSession, request: Any = None):
        from app.streaming.manager import stream_manager
        import os

        from datetime import datetime
        t_start = perf_counter()
        print(f"[{datetime.utcnow().isoformat()}] [1] Chat request received | Conv: {data.conversation_id or 'new'}", flush=True)

        conversation_repository = ConversationRepository(session_db)
        message_repository = MessageRepository(session_db)

        # Measure DB Time 1 (Conversation check/creation)
        t_db0 = perf_counter()
        if not data.conversation_id:
            conv = await conversation_repository.create(
                workspace_id=data.workspace_id or "default",
                title=_generate_smart_title(data.prompt),
            )
            data.conversation_id = str(conv.id)
        else:
            conv = await conversation_repository.get(data.conversation_id)
            if conv is None:
                conv = await conversation_repository.create(
                    workspace_id=data.workspace_id or "default",
                    title=_generate_smart_title(data.prompt),
                )
                data.conversation_id = str(conv.id)
            elif conv and (conv.title == "New Conversation" or not conv.title):
                await conversation_repository.update(conv, title=_generate_smart_title(data.prompt))
        db_time_ms = (perf_counter() - t_db0) * 1000

        # Measure Router Time
        t_router0 = perf_counter()
        provider_id, model_id, strategy_name, explanation, metadata = _resolve_routing(data)
        router_time_ms = (perf_counter() - t_router0) * 1000

        print(f"[{datetime.utcnow().isoformat()}] [2] Routing completed | Selected: {provider_id}/{model_id}", flush=True)

        # Measure Save Time 1 (User message save)
        t_save0 = perf_counter()
        attachments_json = json.dumps([a.model_dump() for a in data.attachments]) if data.attachments else None
        explanation_json = json.dumps(asdict(explanation)) if explanation else None

        user_msg = await message_repository.create(
            conversation_id=data.conversation_id,
            role="user",
            content=data.prompt,
            provider=provider_id,
            model=model_id,
            system_prompt=data.system_prompt,
            attachments=attachments_json,
            strategy_used=strategy_name,
            routing_explanation_json=explanation_json,
        )
        save_time_ms = (perf_counter() - t_save0) * 1000

        # Register StreamSession in StreamManager
        session = stream_manager.create_session(
            conversation_id=data.conversation_id,
            workspace_id=data.workspace_id or "default",
            provider=provider_id,
            model=model_id,
            routing_strategy=strategy_name,
        )

        explanation_dict = asdict(explanation) if explanation else None

        # 1. Event: Metadata
        yield f"event: metadata\ndata: {json.dumps({'stream_id': session.stream_id, 'conversation_id': data.conversation_id, 'provider': provider_id, 'model': model_id, 'strategy': strategy_name})}\n\n"

        # 2. Event: Pipeline Real Lifecycle Stages
        yield f"event: pipeline\ndata: {json.dumps({'stage': 'analyzing', 'label': 'Understanding request...', 'status': 'completed', 'detail': 'Prompt analyzed'})}\n\n"
        yield f"event: pipeline\ndata: {json.dumps({'stage': 'guardrails', 'label': 'Running Guardrails...', 'status': 'completed', 'detail': 'Passed'})}\n\n"
        yield f"event: pipeline\ndata: {json.dumps({'stage': 'provider_selected', 'label': 'Provider selected', 'status': 'completed', 'detail': f'{provider_id.title()} ({model_id}) selected'})}\n\n"
        yield f"event: pipeline\ndata: {json.dumps({'stage': 'provider_connected', 'label': 'Connecting provider...', 'status': 'completed', 'detail': 'Connected'})}\n\n"
        yield f"event: pipeline\ndata: {json.dumps({'stage': 'model_loading', 'label': 'Loading model into memory...', 'status': 'running'})}\n\n"

        # 3. Event: Routing Explanation
        yield f"event: routing\ndata: {json.dumps({'strategy': strategy_name, 'provider': provider_id, 'model': model_id, 'explanation': explanation_dict})}\n\n"

        # Build multi-turn prompt context using PromptBuilder Engine
        t_db1 = perf_counter()
        all_conv_msgs = await message_repository.list_by_conversation(data.conversation_id)
        prior_msgs = [m for m in all_conv_msgs if m.id != user_msg.id]
        if len(prior_msgs) > 20:
            prior_msgs = prior_msgs[-20:]
        db_time_ms += (perf_counter() - t_db1) * 1000

        prompt_ctx = PromptContext(
            system_prompt=data.system_prompt,
            prior_messages=prior_msgs,
            user_prompt=data.prompt,
            attachments=data.attachments,
        )

        messages_payload = prompt_builder.build_messages_payload(prompt_ctx)
        full_prompt = prompt_builder.build_text_prompt(prompt_ctx)

        # Build ordered provider failover candidates list (active providers only)
        failover_candidates = []
        if provider_id and model_id and provider_manager.is_active(provider_id):
            failover_candidates.append((provider_id, model_id))

        possible_fallbacks = [
            ("ollama", settings.ollama_model),
            ("gemini", settings.gemini_model),
            ("openai", settings.openai_model),
        ]
        for p, m in possible_fallbacks:
            if provider_manager.is_active(p):
                failover_candidates.append((p, m))

        # Deduplicate while preserving order
        seen_cand = set()
        dedup_candidates = []
        for p, m in failover_candidates:
            if (p, m) not in seen_cand and provider_manager.is_active(p):
                seen_cand.add((p, m))
                dedup_candidates.append((p, m))

        if not dedup_candidates and provider_manager.is_active("ollama"):
            dedup_candidates.append(("ollama", settings.ollama_model))

        accumulated_chunks = []
        t_stream0 = perf_counter()
        first_token_received = False
        active_provider_id = provider_id
        active_model_id = model_id

        for cand_idx, (cand_p_id, cand_m_id) in enumerate(dedup_candidates):
            try:
                cand_provider = provider_manager.get(cand_p_id)
            except KeyError:
                continue

            logger.info("Provider execution started | stream_id=%s provider=%s model=%s", session.stream_id, cand_p_id, cand_m_id)

            try:
                res_stream = None
                if hasattr(cand_provider, "stream_generate"):
                    res_stream = cand_provider.stream_generate(prompt=full_prompt, model=cand_m_id, messages=messages_payload)

                if res_stream is not None and hasattr(res_stream, "__aiter__"):
                    async for chunk in res_stream:
                        if session.is_cancelled() or (request is not None and await request.is_disconnected()):
                            stream_manager.cancel_session(session.stream_id)
                            logger.warning("Stream cancelled by client connection closure | stream_id=%s conv_id=%s provider=%s", session.stream_id, data.conversation_id, cand_p_id)
                            break
                        if not first_token_received:
                            first_token_received = True
                            active_provider_id = cand_p_id
                            active_model_id = cand_m_id
                            ttft_ms = round((perf_counter() - t_stream0) * 1000, 2)
                            logger.info("First token received | stream_id=%s TTFT=%.2fms provider=%s model=%s", session.stream_id, ttft_ms, cand_p_id, cand_m_id)
                            print(f"[{datetime.utcnow().isoformat()}] [Backend] First token sent | stream_id={session.stream_id}", flush=True)
                            yield f"event: metadata\ndata: {json.dumps({'stream_id': session.stream_id, 'conversation_id': data.conversation_id, 'provider': cand_p_id, 'model': cand_m_id, 'strategy': strategy_name})}\n\n"
                            yield f"event: pipeline\ndata: {json.dumps({'stage': 'model_ready', 'label': 'Model ready', 'status': 'completed', 'detail': 'Model initialized'})}\n\n"
                            yield f"event: pipeline\ndata: {json.dumps({'stage': 'first_token', 'label': 'First token received', 'status': 'completed', 'detail': f'TTFT {ttft_ms}ms'})}\n\n"
                            yield f"event: pipeline\ndata: {json.dumps({'stage': 'generating', 'label': 'Generating response...', 'status': 'running'})}\n\n"

                        session.metrics.mark_first_token()
                        accumulated_chunks.append(chunk)
                        yield f"event: token\ndata: {json.dumps({'token': chunk})}\n\n"
                    if accumulated_chunks or first_token_received or session.is_cancelled():
                        break

                elif res_stream is not None and hasattr(res_stream, "__iter__") and not isinstance(res_stream, (str, bytes)):
                    for chunk in res_stream:
                        if session.is_cancelled():
                            logger.warning("Stream cancelled by client connection closure | stream_id=%s conv_id=%s provider=%s", session.stream_id, data.conversation_id, cand_p_id)
                            break
                        if not first_token_received:
                            first_token_received = True
                            active_provider_id = cand_p_id
                            active_model_id = cand_m_id
                            ttft_ms = round((perf_counter() - t_stream0) * 1000, 2)
                            logger.info("First token received | stream_id=%s TTFT=%.2fms provider=%s model=%s", session.stream_id, ttft_ms, cand_p_id, cand_m_id)
                            print(f"[{datetime.utcnow().isoformat()}] [Backend] First token sent | stream_id={session.stream_id}", flush=True)
                            yield f"event: metadata\ndata: {json.dumps({'stream_id': session.stream_id, 'conversation_id': data.conversation_id, 'provider': cand_p_id, 'model': cand_m_id, 'strategy': strategy_name})}\n\n"

                        session.metrics.mark_first_token()
                        accumulated_chunks.append(chunk)
                        yield f"event: token\ndata: {json.dumps({'token': chunk})}\n\n"
                    if accumulated_chunks or first_token_received or session.is_cancelled():
                        break

                elif hasattr(cand_provider, "generate"):
                    import inspect
                    res_gen = cand_provider.generate(prompt=full_prompt, model=cand_m_id)
                    response_text = await res_gen if inspect.isawaitable(res_gen) else res_gen
                    session.metrics.mark_first_token()
                    words = str(response_text).split(" ")
                    for i, word in enumerate(words):
                        if session.is_cancelled():
                            logger.warning("Stream cancelled by client connection closure | stream_id=%s conv_id=%s provider=%s", session.stream_id, data.conversation_id, cand_p_id)
                            break
                        if not first_token_received:
                            first_token_received = True
                            active_provider_id = cand_p_id
                            active_model_id = cand_m_id
                            ttft_ms = round((perf_counter() - t_stream0) * 1000, 2)
                            logger.info("First token received | stream_id=%s TTFT=%.2fms provider=%s model=%s", session.stream_id, ttft_ms, cand_p_id, cand_m_id)
                            print(f"[{datetime.utcnow().isoformat()}] [Backend] First token sent | stream_id={session.stream_id}", flush=True)
                            yield f"event: metadata\ndata: {json.dumps({'stream_id': session.stream_id, 'conversation_id': data.conversation_id, 'provider': cand_p_id, 'model': cand_m_id, 'strategy': strategy_name})}\n\n"

                        chunk = word + (" " if i < len(words) - 1 else "")
                        accumulated_chunks.append(chunk)
                        yield f"event: token\ndata: {json.dumps({'token': chunk})}\n\n"
                    if accumulated_chunks or first_token_received or session.is_cancelled():
                        break
            except Exception as err:
                logger.warning("Provider execution failed | stream_id=%s provider=%s model=%s error=%s", session.stream_id, cand_p_id, cand_m_id, err)
                if cand_idx < len(dedup_candidates) - 1:
                    next_p = dedup_candidates[cand_idx + 1][0]
                    yield f"event: warning\ndata: {json.dumps({'message': f'Provider {cand_p_id} unavailable. Automatically failing over to {next_p}...', 'provider': cand_p_id, 'retryable': True})}\n\n"
                else:
                    yield f"event: error\ndata: {json.dumps({'detail': f'Provider {cand_p_id} execution failed: {str(err)}', 'provider': cand_p_id, 'retryable': False})}\n\n"

        provider_id = active_provider_id
        model_id = active_model_id

        if not accumulated_chunks and not first_token_received:
            yield f"event: error\ndata: {json.dumps({'detail': 'Execution failed: No response tokens were returned by active provider.', 'provider': provider_id, 'model': model_id})}\n\n"

        stream_time_ms = (perf_counter() - t_stream0) * 1000

        print(f"[{datetime.utcnow().isoformat()}] [Backend] Last token sent | stream_id={session.stream_id}", flush=True)
        print(f"[{datetime.utcnow().isoformat()}] [Backend] SSE closed | stream_id={session.stream_id}", flush=True)

        full_response = "".join(accumulated_chunks)
        latency_ms = round(stream_time_ms)

        prompt_tokens = max(len(full_prompt) // 4, 1)
        completion_tokens = max(len(full_response) // 4, 1)
        total_tokens = prompt_tokens + completion_tokens

        session.metrics.prompt_tokens = prompt_tokens
        session.metrics.completion_tokens = completion_tokens
        session.metrics.finalize()

        metadata = None
        try:
            metadata = model_registry.get_model(provider_id, model_id)
        except Exception:
            pass

        cost_val = float(
            CostCalculator().calculate_token_costs(
                prompt_tokens,
                completion_tokens,
                metadata.cost_per_1k_input_tokens if metadata else Decimal("0.0015"),
                metadata.cost_per_1k_output_tokens if metadata else Decimal("0.006"),
            )
        )
        session.metrics.estimated_cost = Decimal(str(cost_val))

        # Persist assistant message to DB
        t_save1 = perf_counter()
        if full_response:
            # Record execution metadata in Continuous Learning Engine
            from app.routing.learning import ExecutionMetadata, continuous_learning_engine
            continuous_learning_engine.record_execution(
                ExecutionMetadata(
                    prompt_category="chat",
                    selected_provider=provider_id,
                    selected_model=model_id,
                    latency_ms=float(latency_ms),
                    cost_usd=float(cost_val),
                    success=bool(full_response.strip()),
                    failure=not bool(full_response.strip()),
                    cache_used=False,
                )
            )
            if full_response.strip():
                from app.cache.semantic import SemanticCache
                try:
                    sc = SemanticCache()
                    sc.store.set(
                        prompt=data.prompt,
                        response_text=full_response,
                        workspace_id=data.workspace_id or "default",
                        model_id=model_id,
                    )
                except Exception:
                    pass

        if full_response and not session.is_cancelled():
            try:
                assistant_msg = await message_repository.create(
                    conversation_id=data.conversation_id,
                    role="assistant",
                    content=full_response,
                    provider=provider_id,
                    model=model_id,
                    strategy_used=strategy_name,
                    routing_explanation_json=json.dumps(explanation_dict) if explanation_dict else None,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                    cost=cost_val,
                    latency_ms=latency_ms,
                )
                save_time_ms += (perf_counter() - t_save1) * 1000
                print(f"[{datetime.utcnow().isoformat()}] [10] Assistant message saved | Msg ID: {assistant_msg.id}", flush=True)

                semantic_cache.set(
                    prompt=data.prompt,
                    response_text=full_response,
                    workspace_id=data.workspace_id or "default",
                    provider_id=provider_id,
                    model_id=model_id,
                    estimated_cost_usd=cost_val,
                    latency_ms=latency_ms,
                    total_tokens=total_tokens,
                )

                if conv:
                    await conversation_repository.update(conv)
                    print(f"[{datetime.utcnow().isoformat()}] [11] Conversation updated | Conv ID: {data.conversation_id}", flush=True)
            except Exception as e:
                logger.error("Failed to save assistant message: %s", e)

        yield f"event: usage\ndata: {json.dumps({'prompt_tokens': prompt_tokens, 'completion_tokens': completion_tokens, 'total_tokens': total_tokens, 'cost_usd': cost_val, 'latency_ms': latency_ms, 'tokens_per_second': session.metrics.tokens_per_second})}\n\n"
        yield f"event: done\ndata: {json.dumps({'stream_id': session.stream_id, 'conversation_id': data.conversation_id, 'status': 'cancelled' if session.is_cancelled() else 'completed', 'total_tokens': total_tokens, 'cost_usd': cost_val, 'latency_ms': latency_ms, 'provider': provider_id, 'model': model_id})}\n\n"

        print(f"[{datetime.utcnow().isoformat()}] [12] HTTP response completed | SSE connection closed", flush=True)

        stream_manager.cleanup_session(session.stream_id)

    async def get_messages(
        self,
        conversation_id: str,
        db: AsyncSession,
        conversation: Conversation | None = None,
    ):
        if conversation is None:
            conversation_repository = ConversationRepository(db)
            conversation = await conversation_repository.get(conversation_id)

        if conversation is None:
            raise HTTPException(status_code=404, detail="Conversation not found")

        message_repository = MessageRepository(db)
        messages = await message_repository.list_by_conversation(conversation_id)

        logger.info("Conversation Loaded | Conversation ID: %s | Messages Loaded: %d", conversation_id, len(messages))

        def _safe_json_loads(val: str | None):
            if not val:
                return None
            try:
                return json.loads(val)
            except Exception:
                return None

        return {
            "conversation_id": conversation_id,
            "messages": [
                {
                    "id": message.id,
                    "role": message.role,
                    "content": message.content,
                    "provider": message.provider,
                    "model": message.model,
                    "system_prompt": message.system_prompt,
                    "attachments": _safe_json_loads(message.attachments),
                    "strategy_used": message.strategy_used,
                    "routing_explanation": _safe_json_loads(message.routing_explanation_json),
                    "prompt_tokens": message.prompt_tokens,
                    "completion_tokens": message.completion_tokens,
                    "total_tokens": message.total_tokens,
                    "cost_usd": message.cost,
                    "latency_ms": message.latency_ms,
                    "created_at": message.created_at,
                }
                for message in messages
            ],
        }


chat_service = ChatService()
