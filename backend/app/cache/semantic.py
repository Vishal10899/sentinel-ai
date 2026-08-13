import hashlib
import math
import re
import time
from typing import Any

from app.cache.metrics import CacheMetrics
from app.cache.store import CacheEntry, CacheStore


class SemanticCache:
    """Enterprise AI Memory Engine (Embedding Retrieval, Memory Ranking, Confidence Scoring, Adaptive Learning)."""

    def __init__(
        self,
        store: CacheStore | None = None,
        default_threshold: float = 0.80,
        default_ttl: int = 86400,
    ) -> None:
        self.store = store or CacheStore()
        self.default_threshold = default_threshold
        self.default_ttl = default_ttl
        self.metrics = CacheMetrics()

    def normalize_prompt(self, prompt: str) -> str:
        """Clean and normalize prompt text for consistent matching."""
        if not prompt:
            return ""
        text = prompt.lower().strip()
        text = re.sub(r"[^\w\s]", "", text)
        return re.sub(r"\s+", " ", text)

    def _hash_key(self, normalized_prompt: str, workspace_id: str, model_id: str) -> str:
        """Compute SHA-256 key for exact match lookup."""
        raw = f"{workspace_id}:{model_id}:{normalized_prompt}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def generate_embedding(self, prompt: str) -> list[float]:
        """Generate a 128-dimensional L2-normalized float embedding vector (Improvement 1)."""
        dim = 128
        vec = [0.0] * dim
        tokens = prompt.lower().split()
        if not tokens:
            return vec

        for i, token in enumerate(tokens):
            h = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
            idx = h % dim
            weight = 1.0 + (1.0 / (i + 1))  # TF-IDF position weighting
            vec[idx] += weight

        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [round(v / norm, 6) for v in vec]
        return vec

    def cosine_similarity(self, vec1: list[float] | None, vec2: list[float] | None) -> float:
        """Compute vector cosine similarity between two embedding vectors."""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        dot = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return round(dot / (norm1 * norm2), 4)

    def jaccard_similarity(self, prompt_a: str, prompt_b: str) -> float:
        """Calculate token Jaccard similarity score between two normalized prompts."""
        tokens_a = set(prompt_a.split())
        tokens_b = set(prompt_b.split())
        if not tokens_a or not tokens_b:
            return 0.0
        intersection = tokens_a.intersection(tokens_b)
        union = tokens_a.union(tokens_b)
        return len(intersection) / len(union)

    def calculate_similarity(self, prompt_norm: str, vec_a: list[float] | None, entry: CacheEntry) -> float:
        """Calculate hybrid vector cosine + Jaccard similarity score."""
        vec_sim = self.cosine_similarity(vec_a, entry.embedding) if entry.embedding else 0.0
        jaccard_sim = self.jaccard_similarity(prompt_norm, entry.normalized_prompt)
        if vec_sim > 0:
            return round(vec_sim * 0.70 + jaccard_sim * 0.30, 4)
        return round(jaccard_sim, 4)

    def generate_fingerprint(
        self,
        prompt: str,
        workspace_id: str = "default",
        system_prompt: str = "",
        attachments: list[Any] | None = None,
        intent: str = "GENERAL",
    ) -> dict[str, Any]:
        """Generate Memory Fingerprint to prevent incorrect cache reuse (Improvement 7)."""
        sys_hash = hashlib.sha256(system_prompt.encode("utf-8")).hexdigest() if system_prompt else ""
        has_code = bool(re.search(r"def\s+\w+|class\s+\w+|import\s+\w+|function\s+\w+", prompt))
        return {
            "intent": intent,
            "workspace_id": workspace_id,
            "system_prompt_hash": sys_hash,
            "has_attachments": bool(attachments),
            "attachment_count": len(attachments) if attachments else 0,
            "has_code": has_code,
            "fingerprint_hash": hashlib.sha256(f"{workspace_id}:{sys_hash}:{intent}:{has_code}".encode()).hexdigest()[:16],
        }

    FRESHNESS_KEYWORDS = {
        "latest", "today", "current", "real-time", "realtime",
        "live", "now", "recent", "updated", "latest news", "price today"
    }

    def requires_freshness(self, prompt: str) -> bool:
        """Check if request prompt requires live/real-time freshness (Phase 4)."""
        if not prompt:
            return False
        words = set(re.findall(r"\b\w+\b", prompt.lower()))
        return bool(words.intersection(self.FRESHNESS_KEYWORDS))

    def calculate_confidence(
        self,
        entry: CacheEntry,
        similarity: float,
        workspace_id: str,
        system_prompt: str = "",
        attachments: list[Any] | None = None,
    ) -> float:
        """Calculate Confidence Score for memory reuse (Improvement 3)."""
        # Workspace Compatibility
        ws_compat = 1.0 if entry.workspace_id == workspace_id else 0.0
        if ws_compat == 0.0:
            return 0.0  # Strict workspace isolation

        # System Prompt Compatibility (Improvement 10 Safety Constraint)
        sys_hash = hashlib.sha256(system_prompt.encode("utf-8")).hexdigest() if system_prompt else ""
        cached_sys_hash = entry.fingerprint.get("system_prompt_hash", "")
        sys_compat = 1.0 if cached_sys_hash == sys_hash else (0.20 if (sys_hash or cached_sys_hash) else 1.0)

        # Attachment Compatibility
        att_count = len(attachments) if attachments else 0
        cached_att_count = entry.fingerprint.get("attachment_count", 0)
        att_compat = 1.0 if cached_att_count == att_count else 0.30

        # Freshness & Quality Factors
        freshness_factor = 1.0 if entry.freshness_status == "VALID" and not entry.is_expired() else 0.0
        quality_factor = getattr(entry, "quality_score", 0.90)

        # Composite Confidence Formula
        conf = (
            similarity * 0.40 +
            ws_compat * 0.20 +
            sys_compat * 0.20 +
            att_compat * 0.10 +
            quality_factor * 0.05 +
            freshness_factor * 0.05
        )
        return round(min(conf, 1.0), 4)

    def rank_memories(
        self,
        candidates: list[tuple[CacheEntry, float, float]],
    ) -> CacheEntry | None:
        """Rank memory candidates using composite Multi-Factor Memory Score (Improvement 2)."""
        if not candidates:
            return None

        ranked = []
        now = time.time()
        for entry, sim, conf in candidates:
            use_boost = min(entry.use_count * 0.02, 0.10)
            recency_factor = 1.0 if (now - entry.last_used) < 3600 else 0.95
            quality_factor = getattr(entry, "quality_score", 0.90)

            # Final Memory Score
            score = (conf * 0.45) + (sim * 0.35) + use_boost + (quality_factor * 0.10) * recency_factor
            ranked.append((score, entry, sim, conf))

        ranked.sort(key=lambda x: x[0], reverse=True)
        best_score, best_entry, best_sim, best_conf = ranked[0]
        best_entry.similarity = best_sim
        best_entry.confidence = best_conf
        return best_entry

    def get(
        self,
        prompt: str,
        workspace_id: str = "default",
        model_id: str = "default",
        similarity_threshold: float | None = None,
        system_prompt: str = "",
        attachments: list[Any] | None = None,
        confidence_threshold: float = 0.80,
    ) -> dict[str, Any] | None:
        """Enterprise Search Pipeline: Exact Search -> Vector Search -> Ranking -> Confidence Evaluation (Improvement 8)."""
        self.metrics.total_requests += 1

        # Response Validation: Freshness requirement check (Phase 4 / Improvement 10)
        if self.requires_freshness(prompt):
            self.metrics.misses += 1
            return None

        norm_prompt = self.normalize_prompt(prompt)
        if not norm_prompt:
            self.metrics.misses += 1
            return None

        exact_key = self._hash_key(norm_prompt, workspace_id, model_id)
        threshold = similarity_threshold or self.default_threshold

        # 1. Exact Match Lookup
        exact_entry = self.store.get(exact_key)
        if exact_entry:
            conf = self.calculate_confidence(exact_entry, 1.0, workspace_id, system_prompt, attachments)
            if conf >= confidence_threshold:
                self.metrics.exact_hits += 1
                self.metrics.total_latency_saved_ms += exact_entry.latency_ms
                self.metrics.total_cost_saved_usd += exact_entry.estimated_cost_usd
                self.metrics.total_tokens_saved += exact_entry.total_tokens
                self.metrics.record_hit(prompt, 1.0, conf)

                # Adaptive Memory Learning update (Improvement 6)
                exact_entry.use_count += 1
                exact_entry.successful_reuses += 1
                exact_entry.last_used = time.time()
                exact_entry.quality_score = min(1.0, exact_entry.quality_score + 0.01)
                exact_entry.confidence = min(1.0, exact_entry.confidence + 0.01)

                return {
                    "hit": True,
                    "hit_type": "exact",
                    "similarity_score": 1.0,
                    "confidence": conf,
                    "entry": exact_entry.to_dict(),
                    "response_text": exact_entry.response_text,
                    "provider_id": exact_entry.provider_id,
                    "model_id": exact_entry.model_id,
                }

        # 2. Vector Embedding Generation & Semantic Search
        prompt_vec = self.generate_embedding(prompt)
        entries = self.store.list_entries(workspace_id=workspace_id)
        candidates: list[tuple[CacheEntry, float, float]] = []

        for entry in entries:
            sim = self.calculate_similarity(norm_prompt, prompt_vec, entry)
            if sim >= threshold:
                conf = self.calculate_confidence(entry, sim, workspace_id, system_prompt, attachments)
                candidates.append((entry, sim, conf))

        # 3. AI Memory Ranking (Improvement 2)
        best_entry = self.rank_memories(candidates)

        # 4. Confidence & Safety Evaluation (Improvement 3 & 10)
        if best_entry:
            best_sim = getattr(best_entry, "similarity", 1.0)
            best_conf = getattr(best_entry, "confidence", 0.90)

            if best_conf >= confidence_threshold:
                self.metrics.semantic_hits += 1
                self.metrics.total_latency_saved_ms += best_entry.latency_ms
                self.metrics.total_cost_saved_usd += best_entry.estimated_cost_usd
                self.metrics.total_tokens_saved += best_entry.total_tokens
                self.metrics.record_hit(prompt, best_sim, best_conf)

                # Adaptive Memory Learning (Improvement 6)
                best_entry.use_count += 1
                best_entry.successful_reuses += 1
                best_entry.last_used = time.time()
                best_entry.quality_score = min(1.0, best_entry.quality_score + 0.01)
                best_entry.confidence = min(1.0, best_entry.confidence + 0.01)

                return {
                    "hit": True,
                    "hit_type": "semantic",
                    "similarity_score": round(best_sim, 4),
                    "confidence": round(best_conf, 4),
                    "entry": best_entry.to_dict(),
                    "response_text": best_entry.response_text,
                    "provider_id": best_entry.provider_id,
                    "model_id": best_entry.model_id,
                }
            else:
                best_entry.rejected_reuses += 1
                self.metrics.rejected_hits += 1

        self.metrics.misses += 1
        return None

    def set(
        self,
        prompt: str,
        response_text: str,
        workspace_id: str = "default",
        provider_id: str = "default",
        model_id: str = "default",
        estimated_cost_usd: float = 0.0,
        latency_ms: float = 0.0,
        total_tokens: int = 0,
        ttl_seconds: int | None = None,
        conversation_id: str | None = None,
        system_prompt: str = "",
        attachments: list[Any] | None = None,
    ) -> CacheEntry:
        """Store memory record with vector embedding & fingerprint in AI Memory Engine (Improvement 4 & 5)."""
        norm_prompt = self.normalize_prompt(prompt)
        key = self._hash_key(norm_prompt, workspace_id, model_id)
        embedding = self.generate_embedding(prompt)
        fingerprint = self.generate_fingerprint(
            prompt, workspace_id=workspace_id, system_prompt=system_prompt, attachments=attachments
        )

        entry = CacheEntry(
            key=key,
            workspace_id=workspace_id,
            prompt=prompt,
            normalized_prompt=norm_prompt,
            response_text=response_text,
            provider_id=provider_id,
            model_id=model_id,
            estimated_cost_usd=estimated_cost_usd,
            latency_ms=latency_ms,
            total_tokens=total_tokens,
            ttl_seconds=ttl_seconds or self.default_ttl,
            embedding=embedding,
            conversation_id=conversation_id,
            fingerprint=fingerprint,
        )

        self.store.set(entry)
        return entry

    def invalidate(self, workspace_id: str | None = None) -> int:
        """Clear cache entries and update invalidation metrics."""
        count = self.store.clear(workspace_id=workspace_id)
        self.metrics.invalidations += count
        return count

    def get_metrics(self) -> dict[str, Any]:
        """Return enterprise memory analytics & quality metrics (Improvement 9)."""
        m = self.metrics.to_dict()
        entries = self.store.list_entries()
        m["total_memories"] = len(entries)
        m["active_entries"] = len(entries)
        m["cache_size"] = len(entries)
        m["estimated_memory_bytes"] = sum(len(e.prompt) + len(e.response_text) for e in entries) * 2

        # Workspace Statistics & Quality Distribution
        ws_counts: dict[str, int] = {}
        high_q = 0
        med_q = 0
        aging = 0

        for e in entries:
            ws_counts[e.workspace_id] = ws_counts.get(e.workspace_id, 0) + 1
            st = e.update_lifecycle_state()
            if st == "FREQUENTLY_USED" or e.quality_score >= 0.95:
                high_q += 1
            elif st == "AGING":
                aging += 1
            else:
                med_q += 1

        m["quality_distribution"] = {
            "high_quality": high_q,
            "standard": med_q,
            "aging": aging,
        }
        m["workspace_statistics"] = ws_counts
        total_reuses = sum(e.use_count for e in entries)
        m["average_reuse_count"] = round(total_reuses / len(entries), 2) if entries else 0.0

        # Most Valuable Memories (by cost & token savings)
        valuable = sorted(entries, key=lambda e: (e.use_count * e.total_tokens), reverse=True)[:5]
        m["most_valuable_memories"] = [
            {
                "memory_id": e.memory_id,
                "prompt": e.prompt[:60],
                "use_count": e.use_count,
                "tokens_saved": e.use_count * e.total_tokens,
                "provider": e.provider_id,
            }
            for e in valuable
        ]

        return m


semantic_cache = SemanticCache()
