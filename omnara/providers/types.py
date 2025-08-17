"""Type definitions for Omnara providers.

This module defines standardized types and interfaces for all providers
to ensure consistency across different AI agent integrations.
"""

from dataclasses import dataclass
from typing import TypedDict, Literal, Optional, Protocol, Any, Dict, List
from abc import ABC, abstractmethod


# Provider names type
ProviderName = Literal["claude", "amp", "gemini"]

# Permission modes
PermissionMode = Literal["acceptEdits", "bypassPermissions", "default", "plan"]


@dataclass
class ProviderConfig:
    """Configuration for a provider."""

    name: ProviderName
    module_path: str
    main_function: str
    argv_name: str
    supports_mcp: bool
    supports_permissions: bool
    supports_git_diff: bool
    supports_web_ui: bool


class StandardFlags(TypedDict, total=False):
    """Standard flags supported across all providers."""

    api_key: str
    base_url: str
    auth_url: str
    session_id: Optional[str]
    git_diff: bool
    debug: bool
    verbose: bool


class ClaudeFlags(StandardFlags, total=False):
    """Claude-specific flags."""

    permission_mode: Optional[PermissionMode]
    dangerously_skip_permissions: bool
    continue_session: bool
    resume_session: bool


class GeminiFlags(StandardFlags, total=False):
    """Gemini-specific flags."""

    proxy_port: int
    capture_thinking: bool
    model: str
    mode: Literal["proxy", "sdk"]
    temperature: float
    max_tokens: int


class AmpFlags(StandardFlags, total=False):
    """Amp-specific flags."""

    dangerously_allow_all: bool
    settings_file: Optional[str]


# Union type for all provider flags
ProviderFlags = ClaudeFlags | GeminiFlags | AmpFlags


class ProviderProtocol(Protocol):
    """Protocol that all provider implementations should follow."""

    def __init__(self, flags: ProviderFlags) -> None:
        """Initialize the provider with configuration flags."""
        ...

    def run(self) -> None:
        """Run the provider."""
        ...

    def cleanup(self) -> None:
        """Clean up resources."""
        ...


class BaseProvider(ABC):
    """Abstract base class for provider implementations."""

    def __init__(self, flags: Dict[str, Any]) -> None:
        """Initialize the provider.

        Args:
            flags: Configuration flags for the provider
        """
        self.flags = flags
        self.api_key = flags.get("api_key")
        self.base_url = flags.get(
            "base_url", "https://agent-dashboard-mcp.onrender.com"
        )
        self.debug = flags.get("debug", False)
        self.session_id: Optional[str] = flags.get("session_id")

    @abstractmethod
    def run(self) -> None:
        """Run the provider implementation."""
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Clean up any resources used by the provider."""
        pass

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()


@dataclass
class Message:
    """Standardized message format for all providers."""

    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: float
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class Session:
    """Session information for tracking conversations."""

    session_id: str
    provider: ProviderName
    started_at: float
    messages: List[Message]
    metadata: Optional[Dict[str, Any]] = None


# Response streaming types
class StreamChunk(TypedDict):
    """A chunk of streaming response."""

    text: str
    is_final: bool
    metadata: Optional[Dict[str, Any]]


# Error types
class ProviderError(Exception):
    """Base exception for provider errors."""

    pass


class AuthenticationError(ProviderError):
    """Raised when authentication fails."""

    pass


class ConnectionError(ProviderError):
    """Raised when connection to provider fails."""

    pass


class ConfigurationError(ProviderError):
    """Raised when provider configuration is invalid."""

    pass


__all__ = [
    "ProviderName",
    "PermissionMode",
    "ProviderConfig",
    "StandardFlags",
    "ClaudeFlags",
    "GeminiFlags",
    "AmpFlags",
    "ProviderFlags",
    "ProviderProtocol",
    "BaseProvider",
    "Message",
    "Session",
    "StreamChunk",
    "ProviderError",
    "AuthenticationError",
    "ConnectionError",
    "ConfigurationError",
]
