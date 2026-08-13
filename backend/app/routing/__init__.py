"""Public, provider-agnostic intelligent routing foundation."""

from app.routing.analyzer import PromptAnalysisResult, PromptAnalyzer, prompt_analyzer
from app.routing.classifier import TaskCategoryV2, TaskClassificationResult, TaskClassifier, task_classifier
from app.routing.complexity import ComplexityAnalysisResult, ComplexityAnalyzer, ComplexityLevel, complexity_analyzer
from app.routing.engine import AdaptiveAIRoutingEngine, FullRoutingDecision, adaptive_routing_engine
from app.routing.explainability import (
    CandidateExplanation,
    RejectedProviderExplanation,
    RoutingExplanationEngine,
    RoutingExplanationPayload,
    TimelineStage,
    explainability_engine,
)
from app.routing.router import IntelligentRouter
from app.routing.scoring import CandidateScoreBreakdown, MultiFactorScoringEngine, scoring_engine
from app.routing.strategies import (
    BalancedStrategy,
    CheapestStrategy,
    CustomWeightedStrategy,
    EmbeddingOptimizedStrategy,
    FastestStrategy,
    HighestQualityStrategy,
    ImageGenerationOptimizedStrategy,
    ReasoningOptimizedStrategy,
    VisionOptimizedStrategy,
)
from app.routing.learning import ContinuousLearningEngine, ExecutionMetadata, continuous_learning_engine
from app.routing.types import CandidateScore, ModelInfo, RoutingDecisionExplanation, TaskCategory

__all__ = [
    "AdaptiveAIRoutingEngine",
    "BalancedStrategy",
    "CandidateExplanation",
    "CandidateScore",
    "CandidateScoreBreakdown",
    "CheapestStrategy",
    "ComplexityAnalysisResult",
    "ComplexityAnalyzer",
    "ComplexityLevel",
    "ContinuousLearningEngine",
    "CustomWeightedStrategy",
    "EmbeddingOptimizedStrategy",
    "ExecutionMetadata",
    "FastestStrategy",
    "FullRoutingDecision",
    "HighestQualityStrategy",
    "ImageGenerationOptimizedStrategy",
    "IntelligentRouter",
    "ModelInfo",
    "MultiFactorScoringEngine",
    "PromptAnalysisResult",
    "PromptAnalyzer",
    "ReasoningOptimizedStrategy",
    "RejectedProviderExplanation",
    "RoutingDecisionExplanation",
    "RoutingExplanationEngine",
    "RoutingExplanationPayload",
    "TaskCategory",
    "TaskCategoryV2",
    "TaskClassificationResult",
    "TaskClassifier",
    "TimelineStage",
    "VisionOptimizedStrategy",
    "adaptive_routing_engine",
    "complexity_analyzer",
    "continuous_learning_engine",
    "explainability_engine",
    "prompt_analyzer",
    "scoring_engine",
    "task_classifier",
]
