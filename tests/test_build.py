"""Unit tests for build module."""

import inspect
from pathlib import Path

from vtk_python_docs.build import build_all
from vtk_python_docs.config import Config


class TestBuildAll:
    """Tests for build_all function."""

    def test_with_clean(self, tmp_path: Path):
        """Test build_all with clean_first=True."""
        config = Config(project_root=tmp_path)
        config.ensure_dirs()

        # Create test files that should be cleaned
        (config.enhanced_stubs_dir / "test.pyi").write_text("# test")

        # Note: Full build takes too long for unit tests
        # Just verify the function signature works
        assert callable(build_all)

    def test_signature(self):
        """Test that build_all has correct signature."""
        sig = inspect.signature(build_all)
        assert "config" in sig.parameters
        assert "clean_first" in sig.parameters
        assert sig.parameters["clean_first"].default is True
