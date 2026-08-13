"""Sentinel Enterprise Exception Hierarchy for Provider Execution Orchestration."""


class SentinelEnterpriseError(Exception):
    """Base enterprise exception for Sentinel AI."""

    def __init__(self, message: str, status_code: int = 500, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}

    def to_dict(self) -> dict:
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "status_code": self.status_code,
            "details": self.details,
        }


class SentinelInvalidRequestError(SentinelEnterpriseError):
    """400 Invalid Request error (non-transient)."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message=message, status_code=400, details=details)


class SentinelAuthenticationError(SentinelEnterpriseError):
    """401/403 Authentication/Authorization error (non-transient)."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message=message, status_code=401, details=details)


class SentinelRateLimitError(SentinelEnterpriseError):
    """429 Rate Limit error (transient)."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message=message, status_code=429, details=details)


class SentinelProviderTimeoutError(SentinelEnterpriseError):
    """Execution Timeout error (transient)."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message=message, status_code=504, details=details)


class SentinelProviderUnavailableError(SentinelEnterpriseError):
    """500/502/503 Provider Service Unavailable error (transient)."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message=message, status_code=503, details=details)


class SentinelExecutionOrchestrationError(SentinelEnterpriseError):
    """All providers failed execution."""

    def __init__(self, message: str = "All candidate LLM providers failed execution.", details: dict | None = None) -> None:
        super().__init__(message=message, status_code=502, details=details)
