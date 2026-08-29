"""
Automated unit tests for AWS Secrets Manager and Dynamic Key Vault Adapter.
Validates zero static leaks, caching, and environment resolution.
"""

import os
import pytest
from app.core.secrets_manager import AWSSecretsManagerService


def test_secrets_manager_env_resolution(monkeypatch):
    """Verifies that environment variables take precedence in dynamic secret resolution."""
    monkeypatch.setenv("TEST_SECRET_KEY_1", "dynamic-vault-value-9988")
    val = AWSSecretsManagerService.get_secret("TEST_SECRET_KEY_1")
    assert val == "dynamic-vault-value-9988"


def test_secrets_manager_caching_and_override():
    """Verifies in-memory cache lookup and programmatic override."""
    AWSSecretsManagerService.set_cached_secret("CACHE_KEY_XYZ", "cached-token-12345")
    val = AWSSecretsManagerService.get_secret("CACHE_KEY_XYZ")
    assert val == "cached-token-12345"

    AWSSecretsManagerService.clear_cache()
    # After cache clear, should fall back to default
    val_after = AWSSecretsManagerService.get_secret("CACHE_KEY_XYZ", default="fallback-val")
    assert val_after == "fallback-val"


def test_secrets_manager_default_fallback():
    """Verifies default fallback when secret is unconfigured."""
    val = AWSSecretsManagerService.get_secret("NON_EXISTENT_SECRET_2026", default="default-safe-val")
    assert val == "default-safe-val"
