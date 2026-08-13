"""Complexity Analyzer module for measuring request complexity using documented heuristics."""

from dataclasses import dataclass, field
from enum import Enum


class ComplexityLevel(str, Enum):
    """Complexity levels for model-complexity matching."""

    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"


@dataclass(frozen=True, slots=True)
class ComplexityAnalysisResult:
    """Structured complexity analysis output."""

    level: ComplexityLevel
    score_1_to_10: float
    factors: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict:
        return {
            "level": self.level.value,
            "score_1_to_10": self.score_1_to_10,
            "factors": list(self.factors),
        }


class ComplexityAnalyzer:
    """Estimate request complexity using token heuristics, structural indicators, and analytical indicators."""

    def analyze(
        self,
        prompt: str,
        estimated_tokens: int,
        reasoning_depth: str = "low",
        has_code: bool = False,
        has_files: bool = False,
        has_math: bool = False,
    ) -> ComplexityAnalysisResult:
        """Calculate complexity score (1.0 to 10.0) and assign complexity level."""
        score = 1.0
        factors = []

        # Token length factor
        if estimated_tokens > 4000:
            score += 4.0
            factors.append(f"Large prompt context ({estimated_tokens} tokens)")
        elif estimated_tokens > 1500:
            score += 3.0
            factors.append(f"Substantial prompt length ({estimated_tokens} tokens)")
        elif estimated_tokens > 400:
            score += 2.0
            factors.append(f"Moderate prompt length ({estimated_tokens} tokens)")
        elif estimated_tokens > 150:
            score += 1.0
            factors.append("Standard prompt length")

        # Reasoning depth factor
        if reasoning_depth == "high":
            score += 2.5
            factors.append("High reasoning depth requested")
        elif reasoning_depth == "medium":
            score += 1.5
            factors.append("Medium reasoning depth requested")

        # Structural & Domain indicators
        if has_code:
            lines_of_code = prompt.count("\n")
            if lines_of_code > 50:
                score += 2.0
                factors.append("Large code block (>50 lines)")
            else:
                score += 1.0
                factors.append("Code snippet present")

        if has_files:
            score += 1.5
            factors.append("File attachment context included")

        if has_math:
            score += 1.5
            factors.append("Mathematical formula or calculations")

        # Multi-question or multi-step logic
        question_marks = prompt.count("?")
        if question_marks > 3:
            score += 1.0
            factors.append("Multiple queries in prompt")

        final_score = round(min(max(score, 1.0), 10.0), 1)

        # Map numerical score to complexity level
        if final_score >= 7.5:
            level = ComplexityLevel.VERY_COMPLEX
        elif final_score >= 5.0:
            level = ComplexityLevel.COMPLEX
        elif final_score >= 3.0:
            level = ComplexityLevel.MEDIUM
        else:
            level = ComplexityLevel.SIMPLE

        return ComplexityAnalysisResult(
            level=level,
            score_1_to_10=final_score,
            factors=tuple(factors),
        )


complexity_analyzer = ComplexityAnalyzer()
