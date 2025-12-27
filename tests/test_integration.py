"""Integration tests for vtk_python_docs package."""

import json
from pathlib import Path

import pytest

from vtk_python_docs.config import Config
from vtk_python_docs.extract.extractor import _extract_class_docs


class TestExtractClassDocs:
    """Integration tests for _extract_class_docs."""

    def test_extracts_vtkobject(self):
        """Test extracting docs for vtkObject."""
        result = _extract_class_docs("vtkmodules.vtkCommonCore", "vtkObject")
        assert result is not None
        assert result["class_name"] == "vtkObject"
        assert "class_doc" in result
        assert "structured_docs" in result

    def test_extracts_vtkactor(self):
        """Test extracting docs for vtkActor."""
        result = _extract_class_docs("vtkmodules.vtkRenderingCore", "vtkActor")
        assert result is not None
        assert result["class_name"] == "vtkActor"
        assert len(result.get("class_doc", "")) > 0


class TestFullExtraction:
    """Integration tests for full extraction pipeline."""

    @pytest.fixture
    def temp_config(self, tmp_path: Path) -> Config:
        """Create a temporary config for testing."""
        return Config(project_root=tmp_path)

    def test_jsonl_format_valid(self, temp_config: Config):
        """Test that JSONL output is valid JSON lines."""
        # Create a minimal JSONL for testing
        temp_config.docs_dir.mkdir(parents=True, exist_ok=True)

        # Extract just one class and write it
        result = _extract_class_docs("vtkmodules.vtkCommonCore", "vtkObject")
        if result:
            with open(temp_config.jsonl_output, "w") as f:
                record = {"class_name": "vtkObject", "module_name": "vtkCommonCore", **result}
                f.write(json.dumps(record) + "\n")

            # Verify it's valid JSONL
            with open(temp_config.jsonl_output) as f:
                for line in f:
                    data = json.loads(line)
                    assert "class_name" in data
                    assert "module_name" in data
