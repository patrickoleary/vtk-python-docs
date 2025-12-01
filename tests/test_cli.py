"""Unit tests for CLI module."""

import json
from pathlib import Path

from typer.testing import CliRunner

from vtk_python_docs.cli import app

runner = CliRunner()


class TestCLIHelp:
    """Tests for CLI help commands."""

    def test_main_help(self):
        """Test main help command."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "VTK Python documentation" in result.stdout

    def test_extract_help(self):
        """Test extract help command."""
        result = runner.invoke(app, ["extract", "--help"])
        assert result.exit_code == 0
        assert "Extract VTK documentation" in result.stdout

    def test_stubs_help(self):
        """Test stubs help command."""
        result = runner.invoke(app, ["stubs", "--help"])
        assert result.exit_code == 0
        assert "Generate and enhance" in result.stdout

    def test_markdown_help(self):
        """Test markdown help command."""
        result = runner.invoke(app, ["markdown", "--help"])
        assert result.exit_code == 0
        assert "Generate markdown" in result.stdout

    def test_build_help(self):
        """Test build help command."""
        result = runner.invoke(app, ["build", "--help"])
        assert result.exit_code == 0
        assert "complete build pipeline" in result.stdout

    def test_clean_help(self):
        """Test clean help command."""
        result = runner.invoke(app, ["clean", "--help"])
        assert result.exit_code == 0
        assert "Clean" in result.stdout

    def test_stats_help(self):
        """Test stats help command."""
        result = runner.invoke(app, ["stats", "--help"])
        assert result.exit_code == 0
        assert "statistics" in result.stdout

    def test_search_help(self):
        """Test search help command."""
        result = runner.invoke(app, ["search", "--help"])
        assert result.exit_code == 0
        assert "Search" in result.stdout


class TestCLIClean:
    """Tests for clean command."""

    def test_clean_command(self, tmp_path: Path, monkeypatch):
        """Test clean command runs."""
        from vtk_python_docs import config

        test_config = config.Config(project_root=tmp_path)
        test_config.ensure_dirs()

        # Create test files
        (test_config.enhanced_stubs_dir / "test.pyi").write_text("# test")

        monkeypatch.setattr(config, "_default_config", test_config)

        result = runner.invoke(app, ["clean"])
        assert result.exit_code == 0
        assert "Clean complete" in result.stdout


class TestCLIStats:
    """Tests for stats command."""

    def test_stats_no_database(self, tmp_path: Path, monkeypatch):
        """Test stats command when database doesn't exist."""
        from vtk_python_docs import config

        test_config = config.Config(project_root=tmp_path)
        monkeypatch.setattr(config, "_default_config", test_config)

        result = runner.invoke(app, ["stats"])
        assert result.exit_code == 1
        assert "not found" in result.stdout

    def test_stats_with_database(self, tmp_path: Path, monkeypatch):
        """Test stats command with database."""
        from vtk_python_docs import config

        test_config = config.Config(project_root=tmp_path)
        test_config.docs_dir.mkdir(parents=True, exist_ok=True)

        # Create test JSONL
        with open(test_config.jsonl_output, "w") as f:
            f.write(
                json.dumps({"class_name": "vtkTest", "module_name": "vtkCore", "structured_docs": {"sections": {}}})
                + "\n"
            )

        monkeypatch.setattr(config, "_default_config", test_config)

        result = runner.invoke(app, ["stats"])
        assert result.exit_code == 0
        assert "Total classes" in result.stdout


class TestCLISearch:
    """Tests for search command."""

    def test_search_no_database(self, tmp_path: Path, monkeypatch):
        """Test search command when database doesn't exist."""
        from vtk_python_docs import config

        test_config = config.Config(project_root=tmp_path)
        monkeypatch.setattr(config, "_default_config", test_config)

        result = runner.invoke(app, ["search", "vtkActor"])
        assert result.exit_code == 1
        assert "not found" in result.stdout

    def test_search_with_results(self, tmp_path: Path, monkeypatch):
        """Test search command with results."""
        from vtk_python_docs import config

        test_config = config.Config(project_root=tmp_path)
        test_config.docs_dir.mkdir(parents=True, exist_ok=True)

        # Create test JSONL
        with open(test_config.jsonl_output, "w") as f:
            f.write(
                json.dumps({"class_name": "vtkActor", "module_name": "vtkRenderingCore", "synopsis": "Test synopsis"})
                + "\n"
            )

        monkeypatch.setattr(config, "_default_config", test_config)

        result = runner.invoke(app, ["search", "vtkActor"])
        assert result.exit_code == 0
        assert "vtkActor" in result.stdout

    def test_search_no_results(self, tmp_path: Path, monkeypatch):
        """Test search command with no results."""
        from vtk_python_docs import config

        test_config = config.Config(project_root=tmp_path)
        test_config.docs_dir.mkdir(parents=True, exist_ok=True)

        # Create test JSONL
        with open(test_config.jsonl_output, "w") as f:
            f.write(json.dumps({"class_name": "vtkActor", "module_name": "vtkRenderingCore"}) + "\n")

        monkeypatch.setattr(config, "_default_config", test_config)

        result = runner.invoke(app, ["search", "NonExistent"])
        assert result.exit_code == 0
        assert "No results found" in result.stdout
