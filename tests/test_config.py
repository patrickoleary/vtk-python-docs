"""Unit tests for config module."""

from pathlib import Path

from vtk_python_docs.config import SYNOPSIS_MAX_WORDS, Config, get_config


class TestConfig:
    """Tests for Config class."""

    def test_default_project_root(self):
        """Test that default project root is set correctly."""
        config = Config()
        assert config.project_root.exists()
        assert (config.project_root / "vtk_python_docs").exists()

    def test_custom_project_root(self, tmp_path: Path):
        """Test custom project root."""
        config = Config(project_root=tmp_path)
        assert config.project_root == tmp_path

    def test_docs_dir(self):
        """Test docs directory path."""
        config = Config()
        assert config.docs_dir == config.project_root / "docs"

    def test_jsonl_output(self):
        """Test JSONL output path."""
        config = Config()
        assert config.jsonl_output == config.docs_dir / "vtk-python-docs.jsonl"

    def test_enhanced_stubs_dir(self):
        """Test enhanced stubs directory path."""
        config = Config()
        assert config.enhanced_stubs_dir == config.docs_dir / "python-stubs-enhanced"

    def test_markdown_dir(self):
        """Test markdown directory path."""
        config = Config()
        assert config.markdown_dir == config.docs_dir / "python-api"

    def test_ensure_dirs(self, tmp_path: Path):
        """Test that ensure_dirs creates directories."""
        config = Config(project_root=tmp_path)
        config.ensure_dirs()

        assert config.docs_dir.exists()
        assert config.enhanced_stubs_dir.exists()
        assert config.markdown_dir.exists()

    def test_clean(self, tmp_path: Path):
        """Test that clean removes directories."""
        config = Config(project_root=tmp_path)
        config.ensure_dirs()

        # Create a test file
        test_file = config.enhanced_stubs_dir / "test.pyi"
        test_file.write_text("# test")

        config.clean()

        assert not config.enhanced_stubs_dir.exists()
        assert not config.markdown_dir.exists()


class TestGetConfig:
    """Tests for get_config function."""

    def test_returns_config(self):
        """Test that get_config returns a Config instance."""
        config = get_config()
        assert isinstance(config, Config)

    def test_singleton(self):
        """Test that get_config returns the same instance."""
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2


class TestConstants:
    """Tests for module constants."""

    def test_synopsis_max_words(self):
        """Test SYNOPSIS_MAX_WORDS is reasonable."""
        assert isinstance(SYNOPSIS_MAX_WORDS, int)
        assert 10 <= SYNOPSIS_MAX_WORDS <= 50
