import json
import time
import uuid
import logging
from typing import Any, AsyncGenerator

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.chat.dto import ChatRequest
from app.chat.service import chat_service
from app.db.session import get_db
from app.models_registry import model_registry
from app.providers import provider_manager
from app.security.repository import virtual_key_repository
from app.security.keys import VirtualKey

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["OpenAI Gateway Proxy"])


# --- Schemas ---

class OpenAIMessage(BaseModel):
    role: str
    content: str
    name: str | None = None


class OpenAIChatCompletionRequest(BaseModel):
    model: str = Field(default="auto")
    messages: list[OpenAIMessage] = Field(min_length=1)
    stream: bool = Field(default=False)
    temperature: float | None = Field(default=None)
    max_tokens: int | None = Field(default=None)
    max_completion_tokens: int | None = Field(default=None)
    top_p: float | None = Field(default=None)
    frequency_penalty: float | None = Field(default=None)
    presence_penalty: float | None = Field(default=None)
    stop: str | list[str] | None = Field(default=None)


# --- Helper: Authentication & Authorization ---

def _extract_bearer_token(authorization: str | None, x_api_key: str | None) -> str | None:
    if authorization:
        if authorization.lower().startswith("bearer "):
            return authorization[7:].strip()
        return authorization.strip()
    if x_api_key:
        return x_api_key.strip()
    return None


async def authenticate_virtual_key(
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None, alias="x-api-key"),
) -> VirtualKey:
    secret = _extract_bearer_token(authorization, x_api_key)
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "message": "Authentication required. Provide a valid Virtual API Key via Bearer token in Authorization header.",
                    "type": "invalid_request_error",
                    "param": None,
                    "code": "invalid_api_key",
                }
            },
        )

    key_obj = virtual_key_repository.authenticate_secret(secret)
    if not key_obj:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "message": "Invalid or expired Virtual API Key.",
                    "type": "invalid_request_error",
                    "param": None,
                    "code": "invalid_api_key",
                }
            },
        )

    if not key_obj.is_active or key_obj.is_expired():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "message": "Virtual API Key is inactive or expired.",
                    "type": "invalid_request_error",
                    "param": None,
                    "code": "key_expired",
                }
            },
        )

    return key_obj


# --- Helper: Request Translation ---

def _resolve_model_and_provider(requested_model: str) -> tuple[str | None, str | None, str]:
    """Resolve provider_id, model_id, and routing strategy from OpenAI request model string."""
    req = requested_model.strip().lower()

    if req in ("auto", "adaptive", "smart", "default", "sentinel"):
        return None, None, "adaptive"

    if "/" in req:
        parts = req.split("/", 1)
        return parts[0], parts[1], "direct"

    # Check model registry
    for m in model_registry.list_models():
        if m.model_id.lower() == req or m.display_name.lower() == req:
            return m.provider_id, m.model_id, "direct"

    # Direct model name fallback
    return None, requested_model, "adaptive"


def _check_key_permissions(key_obj: VirtualKey, provider_id: str | None, model_id: str | None) -> None:
    """Verify that virtual key is authorized to access requested provider and model."""
    if key_obj.allowed_providers and provider_id:
        if provider_id not in key_obj.allowed_providers:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": {
                        "message": f"Virtual Key does not have permission to access provider '{provider_id}'.",
                        "type": "invalid_request_error",
                        "param": "model",
                        "code": "permission_denied",
                    }
                },
            )

    if key_obj.allowed_models and model_id:
        if model_id not in key_obj.allowed_models:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": {
                        "message": f"Virtual Key does not have permission to access model '{model_id}'.",
                        "type": "invalid_request_error",
                        "param": "model",
                        "code": "permission_denied",
                    }
                },
            )


# --- Endpoints ---

@router.post("/chat/completions", summary="OpenAI-Compatible Chat Completions Proxy Gateway")
async def chat_completions(
    http_request: Request,
    body: OpenAIChatCompletionRequest,
    db: AsyncSession = Depends(get_db),
    key_obj: VirtualKey = Depends(authenticate_virtual_key),
):
    """Minimal Production OpenAI-Compatible Gateway proxying request through Sentinel control plane."""
    # 1. Extract messages payload
    system_prompt = ""
    user_prompt = ""
    prior_messages = []

    for msg in body.messages:
        if msg.role == "system":
            system_prompt = msg.content
        elif msg.role == "user":
            user_prompt = msg.content
        elif msg.role == "assistant":
            prior_messages.append({"role": "assistant", "content": msg.content})

    if not user_prompt and not body.messages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "message": "At least one message with role 'user' is required.",
                    "type": "invalid_request_error",
                    "param": "messages",
                    "code": "missing_required_parameter",
                }
            },
        )
    if not user_prompt:
        user_prompt = body.messages[-1].content

    # 2. Resolve Model & Provider
    provider_id, model_id, strategy = _resolve_model_and_provider(body.model)
    _check_key_permissions(key_obj, provider_id, model_id)

    max_toks = body.max_tokens or body.max_completion_tokens

    # Construct Sentinel ChatRequest safely omitting None optional overrides
    chat_kwargs: dict[str, Any] = {
        "prompt": user_prompt,
        "system_prompt": system_prompt if system_prompt else None,
        "provider": provider_id,
        "model": model_id,
        "strategy": strategy,
        "workspace_id": key_obj.workspace_id,  # Strict workspace isolation!
    }
    if max_toks is not None:
        chat_kwargs["max_tokens"] = max_toks
    if body.temperature is not None:
        chat_kwargs["temperature"] = body.temperature

    chat_req = ChatRequest(**chat_kwargs)


    request_id = f"chatcmpl-{uuid.uuid4().hex[:24]}"
    created_ts = int(time.time())

    # 3. Handle Streaming vs Non-Streaming
    if body.stream:
        async def _openai_sse_generator() -> AsyncGenerator[str, None]:
            first_chunk_emitted = False
            executed_model = body.model

            async for sse_raw in chat_service.stream_generate(chat_req, db=db, request=http_request):
                # Parse Sentinel SSE event format
                lines = sse_raw.strip().split("\n")
                event_type = None
                event_data_str = ""

                for line in lines:
                    if line.startswith("event: "):
                        event_type = line[7:].strip()
                    elif line.startswith("data: "):
                        event_data_str = line[6:].strip()

                if event_type == "metadata" and event_data_str:
                    try:
                        meta = json.loads(event_data_str)
                        executed_model = meta.get("model") or body.model
                    except Exception:
                        pass

                elif event_type == "token" and event_data_str:
                    try:
                        token_obj = json.loads(event_data_str)
                        token = token_obj.get("token", "")

                        chunk_payload = {
                            "id": request_id,
                            "object": "chat.completion.chunk",
                            "created": created_ts,
                            "model": executed_model,
                            "choices": [
                                {
                                    "index": 0,
                                    "delta": {"content": token} if token else {},
                                    "finish_reason": None,
                                }
                            ],
                        }
                        yield f"data: {json.dumps(chunk_payload)}\n\n"
                    except Exception:
                        continue

                elif event_type == "error" and event_data_str:
                    try:
                        err_obj = json.loads(event_data_str)
                        err_payload = {
                            "error": {
                                "message": err_obj.get("detail", "Provider execution failed."),
                                "type": "server_error",
                                "param": None,
                                "code": "provider_error",
                            }
                        }
                        yield f"data: {json.dumps(err_payload)}\n\n"
                    except Exception:
                        pass

                elif event_type == "done":
                    # Final termination chunk
                    stop_payload = {
                        "id": request_id,
                        "object": "chat.completion.chunk",
                        "created": created_ts,
                        "model": executed_model,
                        "choices": [
                            {
                                "index": 0,
                                "delta": {},
                                "finish_reason": "stop",
                            }
                        ],
                    }
                    yield f"data: {json.dumps(stop_payload)}\n\n"
                    yield "data: [DONE]\n\n"

        return StreamingResponse(
            _openai_sse_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    else:
        # Non-streaming request
        try:
            res = await chat_service.generate(chat_req, db)
            response_payload = {
                "id": request_id,
                "object": "chat.completion",
                "created": created_ts,
                "model": res.get("model", body.model),
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": res.get("response", ""),
                        },
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": res.get("prompt_tokens", 0),
                    "completion_tokens": res.get("completion_tokens", 0),
                    "total_tokens": res.get("total_tokens", 0),
                },
                "sentinel_telemetry": {
                    "provider": res.get("provider"),
                    "strategy_used": res.get("strategy_used"),
                    "latency_ms": res.get("latency_ms"),
                    "cost_usd": res.get("cost_usd"),
                    "workspace_id": key_obj.workspace_id,
                },
            }
            return JSONResponse(content=response_payload, status_code=200)

        except HTTPException as http_err:
            raise http_err
        except Exception as exc:
            logger.exception("OpenAI Gateway processing error: %s", exc)
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "message": str(exc),
                        "type": "server_error",
                        "param": None,
                        "code": "internal_error",
                    }
                },
            )


@router.get("/models", summary="List OpenAI-Compatible Models")
async def list_models(key_obj: VirtualKey = Depends(authenticate_virtual_key)):
    """Return model catalog entries formatted for OpenAI SDK compatibility."""
    models_data = []
    for m in model_registry.list_models(enabled_only=True):
        if key_obj.allowed_models and m.model_id not in key_obj.allowed_models:
            continue
        models_data.append(
            {
                "id": m.model_id,
                "object": "model",
                "created": 1700000000,
                "owned_by": m.provider_id,
                "permission": [],
                "root": m.model_id,
                "parent": None,
            }
        )
    return JSONResponse(content={"object": "list", "data": models_data})


@router.post("/embeddings", summary="OpenAI-Compatible Vector Embeddings Proxy Gateway")
async def create_embeddings(
    http_request: Request,
    payload: dict[str, Any],
    key_obj: VirtualKey = Depends(authenticate_virtual_key),
):
    """Route vector embedding requests to active provider or Ollama."""
    input_text = payload.get("input", "")
    requested_model = payload.get("model", "text-embedding-004")

    if isinstance(input_text, list):
        input_text = " ".join(str(x) for x in input_text)

    if not input_text:
        raise HTTPException(
            status_code=400,
            detail={"error": {"message": "Field 'input' is required.", "type": "invalid_request_error", "code": "missing_parameter"}},
        )

    provider_id = "ollama" if provider_manager.is_active("ollama") else "gemini"
    provider = provider_manager.get(provider_id)
    vec = await provider.embed(input_text, model=requested_model)

    return JSONResponse(
        content={
            "object": "list",
            "data": [
                {
                    "object": "embedding",
                    "embedding": vec,
                    "index": 0,
                }
            ],
            "model": requested_model,
            "usage": {
                "prompt_tokens": max(len(input_text) // 4, 1),
                "total_tokens": max(len(input_text) // 4, 1),
            },
        }
    )


@router.post("/messages", summary="Anthropic-Compatible Messages Gateway Proxy")
async def create_anthropic_messages(
    http_request: Request,
    payload: dict[str, Any],
    key_obj: VirtualKey = Depends(authenticate_virtual_key),
    db: AsyncSession = Depends(get_db),
):
    """Parity gateway proxy for Anthropic SDK clients (/v1/messages)."""
    messages_raw = payload.get("messages", [])
    model = payload.get("model", "claude-3-5-sonnet")
    stream = payload.get("stream", False)
    
    # Translate Anthropic messages format to ChatRequest
    chat_messages = []
    for msg in messages_raw:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if isinstance(content, list):
            content_str = " ".join([c.get("text", "") for c in content if isinstance(c, dict) and c.get("type") == "text"])
        else:
            content_str = str(content)
        chat_messages.append(OpenAIMessage(role=role, content=content_str))

    req = OpenAIChatCompletionRequest(model=model, messages=chat_messages, stream=stream)
    return await create_chat_completion(http_request, req, key_obj, db)


@router.post("/responses", summary="Responses Gateway Proxy")
async def create_responses_completion(
    http_request: Request,
    payload: dict[str, Any],
    key_obj: VirtualKey = Depends(authenticate_virtual_key),
    db: AsyncSession = Depends(get_db),
):
    """Parity gateway proxy for /v1/responses endpoint."""
    input_item = payload.get("input", "")
    model = payload.get("model", "auto")
    stream = payload.get("stream", False)
    
    messages = [OpenAIMessage(role="user", content=str(input_item))]
    req = OpenAIChatCompletionRequest(model=model, messages=messages, stream=stream)
    return await create_chat_completion(http_request, req, key_obj, db)

