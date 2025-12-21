"""Async tests for LLM module."""

import pytest

from vtk_python_docs.extract.llm import (
    LLM_MODEL,
    classify_class,
    classify_classes_batch,
)


class TestClassifyClass:
    """Tests for classify_class function."""

    @pytest.mark.asyncio
    async def test_empty_doc_returns_none(self):
        """Test that empty doc returns None."""
        result = await classify_class("vtkTest", "")
        assert result is None

    @pytest.mark.asyncio
    async def test_whitespace_doc_returns_none(self):
        """Test that whitespace-only doc returns None."""
        result = await classify_class("vtkTest", "   ")
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_dict_or_none(self):
        """Test that function returns dict or None."""
        if not LLM_MODEL:
            pytest.skip("LLM not configured")

        result = await classify_class(
            "vtkActor", "vtkActor is used to represent an entity in a rendering scene."
        )
        assert result is None or isinstance(result, dict)
        if result:
            assert "synopsis" in result
            assert "action_phrase" in result
            assert "visibility_score" in result


class TestClassifyClassesBatch:
    """Tests for classify_classes_batch function."""

    @pytest.mark.asyncio
    async def test_empty_list(self):
        """Test with empty list."""
        result = await classify_classes_batch([])
        assert result == {}

    @pytest.mark.asyncio
    async def test_returns_dict(self):
        """Test that function returns a dictionary."""
        items = [("vtkTest", "Test description.")]
        result = await classify_classes_batch(items)
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_with_custom_limits(self):
        """Test with custom rate limits."""
        items = [("vtkTest", "Test description.")]
        result = await classify_classes_batch(
            items,
            max_concurrent=5,
            rate_limit=30,
        )
        assert isinstance(result, dict)
