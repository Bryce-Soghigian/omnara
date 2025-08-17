"""Omnara Provider Registry and Management"""

from typing import Dict, Optional
from .types import ProviderConfig

# Provider registry with configuration for each supported provider
PROVIDER_REGISTRY: Dict[str, ProviderConfig] = {
    "claude": ProviderConfig(
        name="claude",
        module_path="integrations.cli_wrappers.claude_code.claude_wrapper_v3",
        main_function="main",
        argv_name="claude_wrapper_v3",
        supports_mcp=True,
        supports_permissions=True,
        supports_git_diff=True,
        supports_web_ui=True,
    ),
    "amp": ProviderConfig(
        name="amp",
        module_path="integrations.cli_wrappers.amp.amp",
        main_function="main",
        argv_name="amp_wrapper",
        supports_mcp=False,
        supports_permissions=False,
        supports_git_diff=True,
        supports_web_ui=True,
    ),
    "gemini": ProviderConfig(
        name="gemini",
        module_path="integrations.cli_wrappers.gemini.gemini_proxy",
        main_function="main",
        argv_name="gemini_proxy",
        supports_mcp=False,
        supports_permissions=False,
        supports_git_diff=True,
        supports_web_ui=True,
    ),
}


def get_provider_config(provider_name: str) -> Optional[ProviderConfig]:
    """Get configuration for a specific provider.

    Args:
        provider_name: Name of the provider (claude, amp, gemini, etc.)

    Returns:
        ProviderConfig if provider exists, None otherwise
    """
    return PROVIDER_REGISTRY.get(provider_name.lower())


def list_providers() -> list[str]:
    """Get list of all available provider names."""
    return list(PROVIDER_REGISTRY.keys())


__all__ = ["PROVIDER_REGISTRY", "get_provider_config", "list_providers"]
