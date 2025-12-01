"""Unit tests for markdown generator module."""

import json
from pathlib import Path

from vtk_python_docs.markdown.generator import (
    create_class_markdown,
    create_main_index,
    format_method_doc,
    get_vtk_version,
    load_docs_by_module,
    process_modules,
)


class TestGetVTKVersion:
    """Tests for get_vtk_version function."""

    def test_returns_string(self):
        """Test that function returns a string."""
        result = get_vtk_version()
        assert isinstance(result, str)

    def test_version_format(self):
        """Test that version has expected format."""
        result = get_vtk_version()
        # Should be something like "9.5.0" or "Unknown"
        assert len(result) > 0


class TestFormatMethodDoc:
    """Tests for format_method_doc function."""

    def test_empty_doc(self):
        """Test empty doc returns placeholder."""
        assert format_method_doc("") == "*No documentation available.*"

    def test_simple_doc(self):
        """Test simple doc is returned."""
        doc = "This is a method description."
        result = format_method_doc(doc)
        assert "This is a method description" in result

    def test_multiline_doc(self):
        """Test multiline doc is formatted."""
        doc = "Line 1\nLine 2\nLine 3"
        result = format_method_doc(doc)
        assert "Line 1" in result


class TestCreateClassMarkdown:
    """Tests for create_class_markdown function."""

    def test_creates_markdown(self):
        """Test that markdown is created."""
        class_data = {
            "class_doc": "Test class description.",
            "synopsis": "Test synopsis.",
            "structured_docs": {"sections": {}},
        }
        result = create_class_markdown("vtkTest", class_data, "vtkTestModule")
        assert "# vtkTest" in result
        assert "Test class description" in result

    def test_includes_module(self):
        """Test that module is included."""
        class_data = {
            "class_doc": "Description.",
            "structured_docs": {"sections": {}},
        }
        result = create_class_markdown("vtkTest", class_data, "vtkTestModule")
        assert "vtkTestModule" in result

    def test_includes_synopsis(self):
        """Test that synopsis is included."""
        class_data = {
            "class_doc": "Description.",
            "synopsis": "This is the synopsis.",
            "structured_docs": {"sections": {}},
        }
        result = create_class_markdown("vtkTest", class_data, "vtkTestModule")
        assert "This is the synopsis" in result


class TestProcessModules:
    """Tests for process_modules function."""

    def test_empty_module(self, tmp_path: Path):
        """Test processing empty module."""
        docs_by_module = {"vtkEmpty": {}}
        results = process_modules(docs_by_module, tmp_path)
        assert results[0]["status"] == "empty"
        assert results[0]["class_count"] == 0

    def test_processes_classes(self, tmp_path: Path):
        """Test processing module with classes."""
        docs_by_module = {
            "vtkTestModule": {
                "vtkTest": {
                    "class_doc": "Test description.",
                    "structured_docs": {"sections": {}},
                }
            }
        }
        results = process_modules(docs_by_module, tmp_path)
        assert results[0]["status"] == "success"
        assert results[0]["class_count"] == 1

    def test_creates_files(self, tmp_path: Path):
        """Test that files are created."""
        docs_by_module = {
            "vtkTestModule": {
                "vtkTest": {
                    "class_doc": "Test description.",
                    "structured_docs": {"sections": {}},
                }
            }
        }
        process_modules(docs_by_module, tmp_path)

        assert (tmp_path / "vtkTestModule" / "vtkTest.md").exists()
        assert (tmp_path / "vtkTestModule" / "index.md").exists()


class TestCreateMainIndex:
    """Tests for create_main_index function."""

    def test_creates_index(self, tmp_path: Path):
        """Test that index is created."""
        results = [
            {"module": "vtkCore", "status": "success", "class_count": 10},
            {"module": "vtkRendering", "status": "success", "class_count": 20},
        ]
        create_main_index(tmp_path, results)
        assert (tmp_path / "index.md").exists()

    def test_index_content(self, tmp_path: Path):
        """Test index content."""
        results = [
            {"module": "vtkCore", "status": "success", "class_count": 10},
        ]
        create_main_index(tmp_path, results)
        content = (tmp_path / "index.md").read_text()
        assert "vtkCore" in content


class TestLoadDocsByModule:
    """Tests for load_docs_by_module function."""

    def test_nonexistent_file(self, tmp_path: Path):
        """Test with nonexistent file returns empty dict."""
        result = load_docs_by_module(tmp_path / "nonexistent.jsonl")
        assert result == {}

    def test_loads_docs(self, tmp_path: Path):
        """Test loading docs from JSONL."""
        jsonl_file = tmp_path / "test.jsonl"
        with open(jsonl_file, "w") as f:
            f.write(json.dumps({"class_name": "vtkTest", "module_name": "vtkCore"}) + "\n")

        result = load_docs_by_module(jsonl_file)
        assert "vtkCore" in result
        assert "vtkTest" in result["vtkCore"]
