"""Configuration and path management for VTK Python documentation."""

from pathlib import Path


class Config:
    """Central configuration for VTK documentation generation.

    All paths are resolved relative to the project root by default,
    but can be overridden for custom workflows.
    """

    def __init__(self, project_root: Path | None = None):
        """Initialize configuration.

        Args:
            project_root: Root directory of the project. If None, uses the
                         parent of the vtk_python_docs package directory.
        """
        if project_root is None:
            # Default: parent of this package
            self._project_root = Path(__file__).parent.parent.resolve()
        else:
            self._project_root = Path(project_root).resolve()

    @property
    def project_root(self) -> Path:
        """Project root directory."""
        return self._project_root

    @property
    def docs_dir(self) -> Path:
        """Main docs output directory."""
        return self._project_root / "docs"

    @property
    def jsonl_output(self) -> Path:
        """Path to consolidated JSONL database."""
        return self.docs_dir / "vtk-python-docs.jsonl"

    @property
    def enhanced_stubs_dir(self) -> Path:
        """Directory for enhanced VTK stubs with documentation."""
        return self.docs_dir / "python-stubs-enhanced"

    @property
    def markdown_dir(self) -> Path:
        """Directory for generated markdown documentation."""
        return self.docs_dir / "python-api"

    def ensure_dirs(self) -> None:
        """Create all output directories if they don't exist."""
        self.docs_dir.mkdir(parents=True, exist_ok=True)
        self.enhanced_stubs_dir.mkdir(parents=True, exist_ok=True)
        self.markdown_dir.mkdir(parents=True, exist_ok=True)

    def clean(self) -> None:
        """Remove all generated output directories."""
        import shutil

        for path in [self.enhanced_stubs_dir, self.markdown_dir]:
            if path.exists():
                shutil.rmtree(path)

        if self.jsonl_output.exists():
            self.jsonl_output.unlink()

# Synopsis generation settings
SYNOPSIS_MAX_WORDS = 18

# Default configuration instance
_default_config: Config | None = None

def get_config() -> Config:
    """Get the default configuration instance."""
    global _default_config
    if _default_config is None:
        _default_config = Config()
    return _default_config

def set_config(config: Config) -> None:
    """Set the default configuration instance."""
    global _default_config
    _default_config = config
