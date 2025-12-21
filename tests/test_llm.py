"""Unit tests for LLM module."""

import pytest

from vtk_python_docs.extract.llm import (
    CLASSIFY_PROMPT,
    LLM_MAX_CONCURRENT,
    LLM_RATE_LIMIT,
    check_llm_configured,
)


class TestLLMConfig:
    """Tests for LLM configuration."""

    def test_classify_prompt_has_placeholders(self):
        """Test that classify prompt has required placeholders."""
        assert "{class_name}" in CLASSIFY_PROMPT
        assert "{class_doc}" in CLASSIFY_PROMPT

    def test_rate_limit_is_positive(self):
        """Test that rate limit is a positive integer."""
        assert isinstance(LLM_RATE_LIMIT, int)
        assert LLM_RATE_LIMIT > 0

    def test_max_concurrent_is_positive(self):
        """Test that max concurrent is a positive integer."""
        assert isinstance(LLM_MAX_CONCURRENT, int)
        assert LLM_MAX_CONCURRENT > 0


class TestCheckLLMConfigured:
    """Tests for check_llm_configured function."""

    def test_exits_when_no_model(self, monkeypatch):
        """Test exits with code 1 when LLM_MODEL is empty."""
        from vtk_python_docs.extract import llm

        monkeypatch.setattr(llm, "LLM_MODEL", "")

        with pytest.raises(SystemExit) as exc_info:
            check_llm_configured()
        assert exc_info.value.code == 1

    def test_exits_when_missing_api_key(self, monkeypatch):
        """Test exits when API key is missing for model."""
        from vtk_python_docs.extract import llm

        monkeypatch.setattr(llm, "LLM_MODEL", "anthropic/claude-3-haiku")
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        with pytest.raises(SystemExit) as exc_info:
            check_llm_configured()
        assert exc_info.value.code == 1
