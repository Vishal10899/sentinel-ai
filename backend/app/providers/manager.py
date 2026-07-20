"""Provider registry that decouples application code from vendor adapters."""

from app.providers.base import BaseProvider


class ProviderManager:
    """Register, retrieve, and inspect provider adapters by stable name."""

    def __init__(self) -> None:
        self._providers: dict[str, BaseProvider] = {}

    def register(self, provider: BaseProvider) -> None:
        """Register one provider and reject ambiguous duplicate identifiers."""
        if provider.name in self._providers:
            raise ValueError(f"Provider '{provider.name}' is already registered")

        self._providers[provider.name] = provider

    def get(self, name: str) -> BaseProvider:
        """Retrieve a registered provider by name."""
        return self.get_provider(name)

    def get_provider(self, name: str) -> BaseProvider:
        """Retrieve a registered provider through the explicit public API."""
        return self._providers[name]

    def clear(self) -> None:
        """Clear registrations so repeated application lifespans remain deterministic."""
        self._providers.clear()

    def list_providers(self) -> tuple[BaseProvider, ...]:
        """Return registered adapters in registration order."""
        return tuple(self._providers.values())

    def provider_names(self) -> tuple[str, ...]:
        """Return registered provider identifiers without exposing internal state."""
        return tuple(self._providers)

    def configure(self, name: str, **configuration: object) -> None:
        """Apply a configuration update through the provider abstraction."""
        self.get_provider(name).configure(**configuration)

    async def health_checks(self) -> list[dict[str, str]]:
        """Collect local provider health reports without invoking vendor APIs."""
        return [await provider.health() for provider in self._providers.values()]


# One process-scoped registry is populated during application startup.
provider_manager = ProviderManager()
