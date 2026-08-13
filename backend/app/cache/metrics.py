from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class CacheMetrics:
    """Telemetry and performance metrics for Enterprise AI Memory Engine (Improvement 9)."""

    total_requests: int = 0
    exact_hits: int = 0
    semantic_hits: int = 0
    rejected_hits: int = 0
    misses: int = 0
    total_latency_saved_ms: float = 0.0
    total_cost_saved_usd: float = 0.0
    total_tokens_saved: int = 0
    evictions: int = 0
    invalidations: int = 0
    similarity_scores_history: list[float] = field(default_factory=list)
    confidence_scores_history: list[float] = field(default_factory=list)
    reused_prompts_counts: dict[str, int] = field(default_factory=dict)

    @property
    def total_hits(self) -> int:
        return self.exact_hits + self.semantic_hits

    @property
    def hit_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return round((self.total_hits / self.total_requests) * 100, 2)

    @property
    def miss_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return round((self.misses / self.total_requests) * 100, 2)

    @property
    def average_similarity(self) -> float:
        if not self.similarity_scores_history:
            return 1.0
        return round(sum(self.similarity_scores_history) / len(self.similarity_scores_history), 4)

    @property
    def average_confidence(self) -> float:
        if not self.confidence_scores_history:
            return 0.95
        return round(sum(self.confidence_scores_history) / len(self.confidence_scores_history), 4)

    @property
    def average_latency_saved_ms(self) -> float:
        if self.total_hits == 0:
            return 0.0
        return round(self.total_latency_saved_ms / self.total_hits, 2)

    def record_hit(self, prompt: str, similarity: float, confidence: float) -> None:
        short = prompt[:60].strip()
        self.reused_prompts_counts[short] = self.reused_prompts_counts.get(short, 0) + 1
        self.similarity_scores_history.append(similarity)
        self.confidence_scores_history.append(confidence)
        # Keep sliding window of last 1000 scores
        if len(self.similarity_scores_history) > 1000:
            self.similarity_scores_history.pop(0)
        if len(self.confidence_scores_history) > 1000:
            self.confidence_scores_history.pop(0)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["total_hits"] = self.total_hits
        d["hit_rate_pct"] = self.hit_rate
        d["miss_rate_pct"] = self.miss_rate
        d["average_similarity"] = self.average_similarity
        d["average_confidence"] = self.average_confidence
        d["avg_latency_saved_ms"] = self.average_latency_saved_ms
        sorted_reused = sorted(self.reused_prompts_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        d["most_reused_prompts"] = [{"prompt": p, "count": c} for p, c in sorted_reused]
        return d
