import re
from app.orchestration.models import IntentResult, RequestProfile
from typing import Any, Dict, List, Optional

class IntentDetector:
    """Enterprise AI Intent Engine & Request Profiler (15 Estimation Dimensions)."""

    def __init__(self) -> None:
        self._patterns = {
            "CODE_GENERATION": [
                r"\b(write|create|implement|build|generate|code|function|class|method|script|program)\b.*(python|javascript|typescript|c\+\+|java|rust|go|sql|html|css|api)",
                r"```[a-z]*\n",
            ],
            "CODE_REVIEW": [
                r"\b(review|audit|optimize|refactor|clean|improve|security review)\b.*(code|script|function)",
            ],
            "DEBUGGING": [
                r"\b(fix|debug|error|exception|traceback|bug|syntaxerror|nullpointer|issue|failing|crash)\b",
            ],
            "ARCHITECTURE": [
                r"\b(architecture|system design|microservice|database schema|scalability|high availability|infrastructure|distributed system)\b",
            ],
            "REASONING": [
                r"\b(why|explain|step-by-step|analyze|reason|deduce|logic|compare|contrast|pros and cons|tradeoff|eval)\b",
            ],
            "MATHEMATICS": [
                r"\b(calculate|solve|equation|integral|derivative|matrix|formula|algebra|math|theorem|proof|\d+[\+\-\*/\^]\d+)\b",
            ],
            "DATA_ANALYSIS": [
                r"\b(data analysis|analytics|pandas|dataframe|query|sql|chart|trend|statistics|correlation|dataset)\b",
            ],
            "LEGAL_DRAFTING": [
                r"\b(contract|clause|legal|terms|agreement|indemnification|liability|compliance|statute|jurisdiction)\b",
            ],
            "MEDICAL_EXPLANATION": [
                r"\b(symptom|diagnosis|medical|treatment|dosage|clinical|patient|doctor|pharma|physiology)\b",
            ],
            "CREATIVE_WRITING": [
                r"\b(story|poem|essay|brainstorm|script|creative|fiction|rhyme|song|narrative|dialogue)\b",
            ],
            "TRANSLATION": [
                r"\b(translate|english|spanish|french|german|chinese|japanese|russian|portuguese|italian)\b",
            ],
            "SUMMARIZATION": [
                r"\b(summarize|summary|tl;dr|brief|condense|abstract|outline|key points|bullet points)\b",
            ],
            "CLASSIFICATION": [
                r"\b(classify|categorize|label|sentiment|tag|group|sort)\b",
            ],
            "RESEARCH": [
                r"\b(research|investigate|survey|history|background|literature|overview|findings)\b",
            ],
            "CONVERSATION": [
                r"\b(hi|hello|hey|how are you|good morning|chat|talk|thanks|thank you)\b",
            ],
        }

        # Privacy sensitivity detection patterns (source code, PII, company secrets, keys)
        self._privacy_patterns = [
            r"\b(api_key|secret|password|bearer|private_key|token|credential)\b",
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", # Email PII
            r"\b\d{3}-\d{2}-\d{4}\b",                                # SSN PII
            r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",              # IP PII
            r"\b(confidential|proprietary|internal only|company secret|do not distribute)\b",
            r"class\s+\w+|def\s+\w+|import\s+\w+",                  # Source code
        ]

    def detect_intent(self, prompt: str, has_attachments: bool = False) -> IntentResult:
        """Classify prompt intent and estimate reasoning, factual accuracy, and creativity requirements."""
        text = prompt.lower()
        if not text and not has_attachments:
            return IntentResult(
                intent="CONVERSATION", confidence=0.9, estimated_complexity="VERY_LOW",
                reasoning_depth=0.2, factual_accuracy_req=0.5, creativity_req=0.5
            )

        scores: dict[str, float] = {intent: 0.0 for intent in self._patterns}

        for intent, pattern_list in self._patterns.items():
            for pat in pattern_list:
                matches = re.findall(pat, text, re.IGNORECASE)
                if matches:
                    scores[intent] += len(matches) * 0.40

        if has_attachments:
            scores["DATA_ANALYSIS"] += 1.2
            scores["RESEARCH"] += 1.0

        top_intent = max(scores, key=lambda k: scores[k])
        confidence = min(scores[top_intent], 0.98)

        if confidence < 0.25:
            top_intent = "CONVERSATION"
            confidence = 0.85

        req_caps: list[str] = []
        if top_intent in ["CODE_GENERATION", "CODE_REVIEW", "DEBUGGING", "ARCHITECTURE", "REASONING", "MATHEMATICS"]:
            req_caps.append("reasoning")
        if has_attachments or "image" in text or "photo" in text or "chart" in text:
            req_caps.append("vision")
        if "tool" in text or "json" in text or "schema" in text or "api" in text:
            req_caps.append("tools")

        # Complexity estimation (VERY_LOW to VERY_HIGH)
        len_p = len(prompt)
        if top_intent in ["ARCHITECTURE", "LEGAL_DRAFTING", "MEDICAL_EXPLANATION"] or len_p > 3000:
            complexity = "VERY_HIGH" if len_p > 6000 else "HIGH"
        elif top_intent in ["CODE_GENERATION", "CODE_REVIEW", "DEBUGGING", "MATHEMATICS", "REASONING"] or len_p > 1000:
            complexity = "MEDIUM" if len_p < 2000 else "HIGH"
        elif top_intent in ["CONVERSATION", "CLASSIFICATION"]:
            complexity = "VERY_LOW" if len_p < 100 else "LOW"
        else:
            complexity = "MEDIUM"

        # Reasoning depth, factual accuracy, creativity profiles
        reasoning_depth = 0.5
        factual_req = 0.5
        creativity_req = 0.5

        if top_intent in ["ARCHITECTURE", "REASONING", "MATHEMATICS", "DEBUGGING"]:
            reasoning_depth = 0.90
            factual_req = 0.90
            creativity_req = 0.20
        elif top_intent in ["CODE_GENERATION", "CODE_REVIEW", "DATA_ANALYSIS"]:
            reasoning_depth = 0.80
            factual_req = 0.88
            creativity_req = 0.30
        elif top_intent in ["LEGAL_DRAFTING", "MEDICAL_EXPLANATION"]:
            reasoning_depth = 0.85
            factual_req = 0.98
            creativity_req = 0.10
        elif top_intent in ["CREATIVE_WRITING"]:
            reasoning_depth = 0.40
            factual_req = 0.30
            creativity_req = 0.95

        return IntentResult(
            intent=top_intent,
            confidence=round(confidence, 2),
            required_capabilities=req_caps,
            estimated_complexity=complexity,
            reasoning_depth=reasoning_depth,
            factual_accuracy_req=factual_req,
            creativity_req=creativity_req,
        )

    def profile_request(self, prompt: str, system_prompt: str = "", has_attachments: bool = False) -> RequestProfile:
        """Analyze prompt across 15 estimation dimensions."""
        total_len = len(prompt) + len(system_prompt)
        estimated_prompt_tokens = max(total_len // 4, 1)
        estimated_context_tokens = estimated_prompt_tokens + 1500

        intent_res = self.detect_intent(prompt, has_attachments=has_attachments)

        # Detect privacy sensitivity (source code, PII, credentials)
        privacy_hits = 0
        for pat in self._privacy_patterns:
            if re.search(pat, prompt, re.IGNORECASE):
                privacy_hits += 1
        privacy_sensitivity = min(privacy_hits * 0.40, 1.0)

        # Local execution suitability
        local_suitability = 0.50
        if privacy_sensitivity > 0.5 or intent_res.intent in ["CODE_GENERATION", "CODE_REVIEW", "DEBUGGING", "CONVERSATION"]:
            local_suitability += 0.30
        if intent_res.estimated_complexity in ["VERY_LOW", "LOW", "MEDIUM"]:
            local_suitability += 0.20
        local_suitability = min(local_suitability, 1.0)

        prompt_lower = prompt.lower()
        is_latency_sensitive = any(w in prompt_lower for w in ["fast", "quick", "realtime", "instant", "immediately"])
        is_cost_sensitive = any(w in prompt_lower for w in ["cheap", "free", "low cost", "budget", "economical"])
        needs_json = any(w in prompt_lower for w in ["json", "structured", "schema", "format as json"])
        needs_vision = "vision" in intent_res.required_capabilities
        needs_tools = "tools" in intent_res.required_capabilities

        return RequestProfile(
            prompt_tokens=estimated_prompt_tokens,
            context_tokens=estimated_context_tokens,
            complexity=intent_res.estimated_complexity,
            reasoning_depth=intent_res.reasoning_depth,
            factual_accuracy=intent_res.factual_accuracy_req,
            creativity=intent_res.creativity_req,
            latency_importance=0.90 if is_latency_sensitive else 0.50,
            cost_sensitivity=0.90 if is_cost_sensitive else (0.75 if local_suitability > 0.7 else 0.50),
            local_execution_suitability=round(local_suitability, 2),
            privacy_sensitivity=round(privacy_sensitivity, 2),
            is_latency_sensitive=is_latency_sensitive,
            is_cost_sensitive=is_cost_sensitive,
            needs_streaming=True,
            needs_vision=needs_vision,
            needs_tools=needs_tools,
            needs_json=needs_json,
            confidence_score=intent_res.confidence,
        )

    def generate_prompt_intelligence_profile(
        self, prompt: str, system_prompt: str = "", has_attachments: bool = False
    ) -> Any:
        """Generate comprehensive Phase 1 Prompt Intelligence Profile."""
        from app.orchestration.models import PromptIntelligenceProfile

        intent_res = self.detect_intent(prompt, has_attachments=has_attachments)
        req_prof = self.profile_request(prompt, system_prompt=system_prompt, has_attachments=has_attachments)

        text = prompt.lower()
        has_code_keywords = any(w in text for w in ["code", "python", "javascript", "typescript", "script", "function", "class", "def ", "import ", "sql"])
        coding_pct = 90.0 if intent_res.intent in ["CODE_GENERATION", "CODE_REVIEW", "DEBUGGING"] else (60.0 if has_code_keywords else 0.0)
        math_pct = 95.0 if intent_res.intent in ["MATHEMATICS"] else 0.0
        arch_pct = 90.0 if intent_res.intent in ["ARCHITECTURE"] else 0.0
        writing_pct = 85.0 if intent_res.intent in ["CREATIVE_WRITING"] else 0.0
        research_pct = 80.0 if intent_res.intent in ["RESEARCH", "DATA_ANALYSIS"] else 0.0
        vision_pct = 100.0 if req_prof.needs_vision else 0.0
        translation_pct = 95.0 if intent_res.intent in ["TRANSLATION"] else 0.0
        summarization_pct = 95.0 if intent_res.intent in ["SUMMARIZATION"] else 0.0

        freshness_required = any(w in text for w in ["latest", "today", "current", "real-time", "realtime", "live", "now", "recent", "updated"])
        pii_detected = req_prof.privacy_sensitivity > 0.3

        return PromptIntelligenceProfile(
            intent=intent_res.intent,
            goal=f"Execute {intent_res.intent.lower().replace('_', ' ')} task efficiently",
            complexity=intent_res.estimated_complexity,
            reasoning_depth=intent_res.reasoning_depth,
            creativity_req=intent_res.creativity_req,
            accuracy_req=intent_res.factual_accuracy_req,
            coding_pct=coding_pct,
            math_pct=math_pct,
            architecture_pct=arch_pct,
            writing_pct=writing_pct,
            research_pct=research_pct,
            vision_pct=vision_pct,
            image_gen_pct=0.0,
            translation_pct=translation_pct,
            summarization_pct=summarization_pct,
            needs_json=req_prof.needs_json,
            needs_structured_output=req_prof.needs_json,
            needs_tools=req_prof.needs_tools,
            needs_streaming=True,
            needs_long_context=len(prompt) > 4000,
            has_conversation_dependency=bool(system_prompt),
            privacy_sensitivity=req_prof.privacy_sensitivity,
            pii_detected=pii_detected,
            security_risk="HIGH" if req_prof.privacy_sensitivity > 0.7 else ("MEDIUM" if pii_detected else "LOW"),
            latency_priority=req_prof.latency_importance,
            cost_priority=req_prof.cost_sensitivity,
            quality_priority=round((req_prof.reasoning_depth + req_prof.factual_accuracy) / 2, 2),
            freshness_required=freshness_required,
            language="English",
            estimated_input_tokens=req_prof.prompt_tokens,
            estimated_output_tokens=max(req_prof.prompt_tokens // 2, 100),
            expected_runtime_ms=round(req_prof.prompt_tokens * 1.5 + 200),
            confidence=intent_res.confidence,
        )


intent_detector = IntentDetector()
