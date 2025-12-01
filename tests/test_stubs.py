"""Unit tests for stubs module."""

import json
import shutil
from pathlib import Path

from vtk_python_docs.stubs.enhance import (
    enhance_stubs,
    generate_official_stubs,
    load_docs_by_module,
)


class TestLoadDocsByModule:
    """Tests for load_docs_by_module function."""

    def test_nonexistent_file(self, tmp_path: Path):
        """Test with nonexistent file."""
        result = load_docs_by_module(tmp_path / "nonexistent.jsonl")
        assert result == {}

    def test_loads_and_groups_by_module(self, tmp_path: Path):
        """Test loading and grouping by module."""
        jsonl_file = tmp_path / "test.jsonl"
        with open(jsonl_file, "w") as f:
            f.write(json.dumps({"class_name": "vtkA", "module_name": "vtkCore"}) + "\n")
            f.write(json.dumps({"class_name": "vtkB", "module_name": "vtkCore"}) + "\n")
            f.write(json.dumps({"class_name": "vtkC", "module_name": "vtkRendering"}) + "\n")

        result = load_docs_by_module(jsonl_file)
        assert len(result) == 2
        assert len(result["vtkCore"]) == 2
        assert len(result["vtkRendering"]) == 1


class TestEnhanceStubs:
    """Tests for enhance_stubs function."""

    def test_enhances_stubs(self, tmp_path: Path):
        """Test enhancing stubs."""
        stubs_dir = tmp_path / "stubs"
        stubs_dir.mkdir()
        (stubs_dir / "vtkTest.pyi").write_text("class vtkTest:\n    pass\n")

        docs_by_module = {
            "vtkTest": {
                "vtkTest": {
                    "class_doc": "Test description.",
                    "structured_docs": {"sections": {}},
                }
            }
        }

        output_dir = tmp_path / "output"

        result = enhance_stubs(stubs_dir, docs_by_module, output_dir)
        assert result == 1
        assert (output_dir / "vtkTest.pyi").exists()


class TestGenerateOfficialStubs:
    """Tests for generate_official_stubs function."""

    def test_returns_path_or_none(self):
        """Test that function returns Path or None."""
        result = generate_official_stubs(timeout=120)
        assert result is None or isinstance(result, Path)
        if result:
            shutil.rmtree(result)

    def test_generates_stubs(self):
        """Test that stubs are generated."""
        temp_dir = generate_official_stubs(timeout=120)
        assert temp_dir is not None
        pyi_files = list(temp_dir.glob("*.pyi"))
        assert len(pyi_files) > 0
        shutil.rmtree(temp_dir)
