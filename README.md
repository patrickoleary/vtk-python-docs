# VTK Python Documentation Enhancement

A Python package for extracting VTK documentation, generating enhanced Python stubs, and creating markdown API documentation.

## 🚀 Features

- **VTK Documentation Extraction**: Extract documentation from VTK using Python introspection
- **Enhanced Python Stubs**: Generate VTK stub files with rich docstrings for IDE IntelliSense
- **Markdown Documentation**: Generate markdown API documentation organized by modules
- **JSONL Database**: Consolidated database of all VTK classes for querying
- **LLM Classification**: AI-powered class metadata using LiteLLM (synopsis, action phrase, role, visibility)

## 📋 Requirements

- Python 3.10+
- VTK Python package

## 🛠️ Installation

```bash
git clone <repository-url>
cd vtk-python-docs
./setup.sh
```

This creates a virtual environment and installs the package in editable mode.

## ⚙️ LLM Configuration (Optional)

For AI-powered classification (synopsis, role, visibility), copy `.env.example` to `.env` and configure your LLM provider:

```bash
cp .env.example .env
# Edit .env with your API key
```

Supported providers via [LiteLLM](https://docs.litellm.ai/docs/providers):
- **OpenAI**: `gpt-4o-mini`, `gpt-4o`
- **Anthropic**: `claude-3-haiku-20240307`, `claude-3-5-sonnet-20241022`
- **Ollama** (local, free): `ollama/llama3.2`, `ollama/mistral`
- **Google**: `gemini/gemini-1.5-flash`
- And 100+ more providers

If no LLM is configured, classification metadata will be skipped.

## 📖 Usage

### Full Build

```bash
source .venv/bin/activate
vtk-docs build
```

This generates all outputs (~35 seconds without LLM, longer with LLM due to rate limiting):
- `docs/vtk-python-docs.jsonl` - JSONL database
- `docs/python-stubs-enhanced/` - Enhanced Python stubs
- `docs/python-api/` - Markdown documentation

### CLI Commands

```bash
vtk-docs --help          # Show all commands
vtk-docs build           # Run complete build pipeline
vtk-docs extract         # Extract VTK documentation to JSONL
vtk-docs stubs           # Generate and enhance Python stubs
vtk-docs markdown        # Generate markdown documentation
vtk-docs clean           # Clean generated files
vtk-docs stats           # Show database statistics
vtk-docs search <query>  # Search the documentation
```

### Search Examples

```bash
vtk-docs search vtkActor           # Search by class name
vtk-docs search Render -f synopsis # Search in synopsis field
vtk-docs search Core -f module_name -n 20  # Search modules, show 20 results
```

### Programmatic Usage

```python
from vtk_python_docs.build import build_all

# Run full build
build_all()

# Or use individual components
from vtk_python_docs.extract import extract_all
from vtk_python_docs.stubs import generate_all as generate_stubs
from vtk_python_docs.markdown import generate_all as generate_markdown
from vtk_python_docs.config import get_config

config = get_config()
extract_all(config)
generate_stubs(config)
generate_markdown(config)
```

### Querying the JSONL Database

```python
import json
from pathlib import Path

# Stream through JSONL database
for line in open('docs/vtk-python-docs.jsonl'):
    record = json.loads(line)
    if 'Actor' in record['class_name']:
        print(f"{record['class_name']}: {record.get('synopsis', '')}")
```

## 📁 Output Structure

```
docs/
├── vtk-python-docs.jsonl    # All VTK classes (JSONL format)
├── python-stubs-enhanced/   # Enhanced .pyi stub files
│   ├── vtkCommonCore.pyi
│   └── ... (150+ modules)
└── python-api/              # Markdown documentation
    ├── index.md
    └── vtkCommonCore/
        ├── index.md
        └── vtkObject.md
```

## 🔧 Project Structure

```
vtk-python-docs/
├── pyproject.toml
├── setup.sh
├── tests/               # pytest test suite
└── vtk_python_docs/
    ├── __init__.py
    ├── cli.py           # Typer CLI
    ├── config.py        # Centralized configuration
    ├── build.py         # Build pipeline orchestrator
    ├── extract/         # VTK documentation extraction
    ├── stubs/           # Stub generation & enhancement
    └── markdown/        # Markdown generation
```

## 🧪 Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Run tests with coverage
pytest tests/ --cov=vtk_python_docs

# Lint code
ruff check vtk_python_docs/

# Type check
pyright vtk_python_docs/
```

## 🔑 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_MODEL` | LiteLLM model identifier | (none) |
| `OPENAI_API_KEY` | OpenAI API key | (none) |
| `ANTHROPIC_API_KEY` | Anthropic API key | (none) |
| `GEMINI_API_KEY` | Google Gemini API key | (none) |
| `LLM_RATE_LIMIT` | Requests per minute | 60 |
| `LLM_MAX_CONCURRENT` | Max concurrent requests | 10 |

## 📄 License

This project enhances the official VTK Python bindings. Please refer to VTK's licensing terms for the underlying VTK library.
