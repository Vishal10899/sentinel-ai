"""Task Classifier module for classifying requests into fine-grained task categories."""

import re
from dataclasses import dataclass, field
from enum import Enum


class TaskCategoryV2(str, Enum):
    """Supported task categories for AI routing classification."""

    GENERAL_CHAT = "general_chat"
    CODING = "coding"
    CODE_REVIEW = "code_review"
    DEBUGGING = "debugging"
    SQL = "sql"
    DOCUMENTATION = "documentation"
    SUMMARIZATION = "summarization"
    TRANSLATION = "translation"
    CREATIVE_WRITING = "creative_writing"
    REASONING = "reasoning"
    MATH = "math"
    DATA_ANALYSIS = "data_analysis"
    BUSINESS = "business"
    RESEARCH = "research"
    SECURITY_REVIEW = "security_review"


@dataclass(frozen=True, slots=True)
class TaskClassificationResult:
    """Structured classification output containing primary category and confidence scores."""

    primary_category: TaskCategoryV2
    confidence: float
    secondary_categories: tuple[str, ...] = field(default_factory=tuple)
    category_scores: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "primary_category": self.primary_category.value,
            "confidence": self.confidence,
            "secondary_categories": list(self.secondary_categories),
            "category_scores": self.category_scores,
        }


class TaskClassifier:
    """Classify user prompts into fine-grained task categories using weighted keyword and regex patterns."""

    _PATTERNS: dict[TaskCategoryV2, list[str]] = {
        TaskCategoryV2.SECURITY_REVIEW: [
            r"\b(security|vulnerability|owasp|cve|exploit|penetration|auth|jwt|token\s+leak|xss|csrf|injection|audit|mitigate)\b",
            r"\b(secret|token|api_key|password|credential|leak)\b",
        ],
        TaskCategoryV2.SQL: [
            r"\b(sql|database|postgres|mysql|query|select\s+.*from|join\s+\w+|index|where\s+\w+|group\bby|order\bby)\b",
            r"```sql",
        ],
        TaskCategoryV2.DEBUGGING: [
            r"\b(debug|fix|bug|error|exception|traceback|stacktrace|failing|broken|issue|undefined|nullpointer)\b",
            r"\b(help\s+fix|why\s+is\s+this\s+failing|syntaxerror|typeerror)\b",
        ],
        TaskCategoryV2.CODE_REVIEW: [
            r"\b(code\s+review|review\s+this|improve\s+code|refactor|clean\s+code|best\s+practices|dry\s+principle|optimize\s+code)\b",
        ],
        TaskCategoryV2.CODING: [
            r"\b(python|javascript|typescript|c\+\+|java|rust|go|html|css|function|class|def|async|await|api|code|script|program|build\s+an?\s+app)\b",
            r"```[a-z]*\n",
        ],
        TaskCategoryV2.MATH: [
            r"\b(calculate|solve|equation|integral|derivative|matrix|algebra|math|geometry|formula|theorem|proof)\b",
            r"[\d\w\)]\s*[\+\-\*/\^=]\s*[\d\w\(]",
        ],
        TaskCategoryV2.DATA_ANALYSIS: [
            r"\b(data\s+analysis|pandas|dataframe|chart|csv|dataset|statistics|trend|metrics|correlation|distribution)\b",
        ],
        TaskCategoryV2.SUMMARIZATION: [
            r"\b(summarize|summary|tl;dr|brief|condense|abstract|outline|key\s+takeaways|bullet\s+points)\b",
        ],
        TaskCategoryV2.TRANSLATION: [
            r"\b(translate|english|spanish|french|german|chinese|japanese|russian|portuguese|italian|korean)\b",
        ],
        TaskCategoryV2.DOCUMENTATION: [
            r"\b(documentation|docs|readme|swagger|openapi|api\s+docs|docstring|comments|user\s+guide)\b",
        ],
        TaskCategoryV2.REASONING: [
            r"\b(step[- ]by[- ]step|why|explain|analyze|reason|deduce|logic|compare|contrast|tradeoff|evaluate|architect)\b",
        ],
        TaskCategoryV2.CREATIVE_WRITING: [
            r"\b(write\s+a\s+story|poem|essay|blog\s+post|creative|article|tagline|marketing\s+copy)\b",
        ],
        TaskCategoryV2.BUSINESS: [
            r"\b(business|strategy|finops|roi|budget|cost|pricing|market|proposal|stakeholder|revenue)\b",
        ],
        TaskCategoryV2.RESEARCH: [
            r"\b(research|paper|study|literature|history|background|findings|survey|citations)\b",
        ],
    }

    def classify(self, prompt: str, detected_language: str | None = None, has_attachments: bool = False) -> TaskClassificationResult:
        """Classify prompt into primary category with confidence score."""
        text = prompt.lower().strip()
        if not text and not has_attachments:
            return TaskClassificationResult(
                primary_category=TaskCategoryV2.GENERAL_CHAT,
                confidence=0.90,
                secondary_categories=(),
                category_scores={TaskCategoryV2.GENERAL_CHAT.value: 0.90},
            )

        scores: dict[TaskCategoryV2, float] = {cat: 0.0 for cat in TaskCategoryV2}

        for cat, pattern_list in self._PATTERNS.items():
            for pat in pattern_list:
                matches = re.findall(pat, text, re.IGNORECASE)
                if matches:
                    scores[cat] += len(matches) * 0.40

        # Programming language hint
        if detected_language:
            if detected_language == "sql":
                scores[TaskCategoryV2.SQL] += 0.8
            else:
                scores[TaskCategoryV2.CODING] += 0.6

        if has_attachments:
            scores[TaskCategoryV2.DOCUMENTATION] += 0.5
            scores[TaskCategoryV2.DATA_ANALYSIS] += 0.4

        # Rank categories by score
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top_cat, top_score = sorted_scores[0]

        if top_score < 0.35:
            primary_cat = TaskCategoryV2.GENERAL_CHAT
            confidence = 0.85
        else:
            primary_cat = top_cat
            confidence = min(round(top_score, 2), 0.99)

        # Secondary categories (score > 0.3)
        secondaries = [cat.value for cat, score in sorted_scores[1:] if score > 0.30 and cat != primary_cat]

        normalized_scores = {
            cat.value: round(min(score, 1.0), 2) for cat, score in sorted_scores if score > 0
        }
        if not normalized_scores:
            normalized_scores = {TaskCategoryV2.GENERAL_CHAT.value: 0.85}

        return TaskClassificationResult(
            primary_category=primary_cat,
            confidence=confidence,
            secondary_categories=tuple(secondaries[:3]),
            category_scores=normalized_scores,
        )


task_classifier = TaskClassifier()
