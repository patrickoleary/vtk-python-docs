"""Unit tests for markdown generator module.

Tests the public API generate_all() and verifies output structure.
"""

import json
from pathlib import Path

from vtk_python_docs.config import Config
from vtk_python_docs.markdown.generator import generate_all


class TestGenerateAll:
    """Tests for generate_all() public API."""

    def test_returns_zero_for_missing_jsonl(self, tmp_path: Path):
        """Test returns 0 when JSONL file doesn't exist."""
        config = Config(project_root=tmp_path)
        result = generate_all(config)
        assert result == 0

    def test_generates_markdown_files(self, tmp_path: Path):
        """Test that markdown files are generated."""
        config = Config(project_root=tmp_path)
        config.docs_dir.mkdir(parents=True, exist_ok=True)

        # Create test JSONL
        with open(config.jsonl_output, "w") as f:
            f.write(json.dumps({
                "class_name": "vtkTest",
                "module_name": "vtkTestModule",
                "class_doc": "Test class description.",
                "synopsis": "Test synopsis.",
                "structured_docs": {"sections": {}},
            }) + "\n")

        result = generate_all(config)
        assert result == 1  # 1 module processed

        # Verify files created
        assert (config.markdown_dir / "vtkTestModule" / "vtkTest.md").exists()
        assert (config.markdown_dir / "vtkTestModule" / "index.md").exists()
        assert (config.markdown_dir / "index.md").exists()

    def test_markdown_content(self, tmp_path: Path):
        """Test that markdown content is correct."""
        config = Config(project_root=tmp_path)
        config.docs_dir.mkdir(parents=True, exist_ok=True)

        # Create test JSONL
        with open(config.jsonl_output, "w") as f:
            f.write(json.dumps({
                "class_name": "vtkActor",
                "module_name": "vtkRenderingCore",
                "class_doc": "Represents an entity in a rendering scene.",
                "synopsis": "Represents an entity in a rendering scene.",
                "structured_docs": {"sections": {}},
            }) + "\n")

        generate_all(config)

        # Check class markdown
        class_md = (config.markdown_dir / "vtkRenderingCore" / "vtkActor.md").read_text()
        assert "# vtkActor" in class_md
        assert "vtkRenderingCore" in class_md
        assert "Represents an entity" in class_md

        # Check module index
        index_md = (config.markdown_dir / "vtkRenderingCore" / "index.md").read_text()
        assert "vtkActor" in index_md

        # Check main index
        main_md = (config.markdown_dir / "index.md").read_text()
        assert "vtkRenderingCore" in main_md

    def test_metadata_table(self, tmp_path: Path):
        """Test that metadata table is generated correctly."""
        config = Config(project_root=tmp_path)
        config.docs_dir.mkdir(parents=True, exist_ok=True)

        # Create test JSONL with full metadata
        with open(config.jsonl_output, "w") as f:
            f.write(json.dumps({
                "class_name": "vtkSphereSource",
                "module_name": "vtkFiltersSources",
                "class_doc": "Creates a sphere.",
                "synopsis": "Generates sphere geometry.",
                "role": "input",
                "action_phrase": "sphere generation",
                "visibility_score": 0.9,
                "input_datatype": "",
                "output_datatype": "vtkPolyData",
                "semantic_methods": ["SetRadius", "SetCenter", "SetThetaResolution"],
                "structured_docs": {"sections": {}},
            }) + "\n")

        generate_all(config)

        class_md = (config.markdown_dir / "vtkFiltersSources" / "vtkSphereSource.md").read_text()

        # Check metadata table
        assert "| **Role** | input |" in class_md
        assert "| **Action** | sphere generation |" in class_md
        assert "| **Visibility** |" in class_md
        assert "| **Output Type** | vtkPolyData |" in class_md

        # Check key methods
        assert "## Key Methods" in class_md
        assert "`SetRadius`" in class_md
        assert "`SetCenter`" in class_md

    def test_multiple_modules(self, tmp_path: Path):
        """Test processing multiple modules."""
        config = Config(project_root=tmp_path)
        config.docs_dir.mkdir(parents=True, exist_ok=True)

        # Create test JSONL with multiple modules
        with open(config.jsonl_output, "w") as f:
            f.write(json.dumps({
                "class_name": "vtkObject",
                "module_name": "vtkCommonCore",
                "class_doc": "Base class.",
                "structured_docs": {"sections": {}},
            }) + "\n")
            f.write(json.dumps({
                "class_name": "vtkActor",
                "module_name": "vtkRenderingCore",
                "class_doc": "Actor class.",
                "structured_docs": {"sections": {}},
            }) + "\n")

        result = generate_all(config)
        assert result == 2  # 2 modules processed

        assert (config.markdown_dir / "vtkCommonCore" / "vtkObject.md").exists()
        assert (config.markdown_dir / "vtkRenderingCore" / "vtkActor.md").exists()
