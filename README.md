# VTK Python Documentation Enhancement

A Python package for extracting VTK documentation, generating enhanced Python stubs, and creating markdown API documentation.

## 🚀 Features

- **VTK Documentation Extraction**: Extract documentation from VTK using Python introspection
- **VTK Type Introspection**: Automatic role classification (input, filter, output, etc.) and datatype detection using VTK's type system
- **Enhanced Python Stubs**: Generate VTK stub files with rich docstrings for IDE IntelliSense
- **Markdown Documentation**: Generate markdown API documentation organized by modules
- **JSONL Database**: Consolidated database of all VTK classes for querying
- **LLM Classification**: AI-powered class metadata using LiteLLM (synopsis, action_phrase, visibility_score)

## 📋 Requirements

- Python 3.10+
- VTK Python package
- [uv](https://docs.astral.sh/uv/) package manager

## 🛠️ Installation

```bash
git clone <repository-url>
cd vtk-python-docs
./setup.sh
```

Or manually with uv:

```bash
uv sync --extra dev
```

This creates a virtual environment and installs the package with all dependencies.

## ⚙️ LLM Configuration (Optional)

For AI-powered classification (synopsis, action_phrase, visibility_score), copy `.env.example` to `.env` and configure your LLM provider:

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
uv run vtk-docs build
```

This generates all outputs (~35 seconds without LLM, longer with LLM due to rate limiting):
- `docs/vtk-python-docs.jsonl` - JSONL database
- `docs/python-stubs-enhanced/` - Enhanced Python stubs
- `docs/python-api/` - Markdown documentation

### CLI Commands

```bash
uv run vtk-docs --help          # Show all commands
uv run vtk-docs build           # Run complete build pipeline
uv run vtk-docs extract         # Extract VTK documentation to JSONL
uv run vtk-docs stubs           # Generate and enhance Python stubs
uv run vtk-docs markdown        # Generate markdown documentation
uv run vtk-docs clean           # Clean generated files
uv run vtk-docs stats           # Show database statistics
uv run vtk-docs search <query>  # Search the documentation
```

### Search Examples

```bash
uv run vtk-docs search vtkActor           # Search by class name
uv run vtk-docs search Render -f synopsis # Search in synopsis field
uv run vtk-docs search Core -f module_name -n 20  # Search modules, show 20 results
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
├── llm-cache.jsonl          # Cached LLM classifications (avoids re-calling LLM)
├── python-stubs-enhanced/   # Enhanced .pyi stub files
│   ├── vtkCommonCore.pyi
│   └── ... (150+ modules)
└── python-api/              # Markdown documentation
    ├── index.md
    └── vtkCommonCore/
        ├── index.md
        └── vtkObject.md
```

### JSONL Record Fields

Each record in `vtk-python-docs.jsonl` contains:

| Field | Source | Description |
|-------|--------|-------------|
| `class_name` | VTK | Class name (e.g., `vtkActor`) |
| `module_name` | VTK | Module name (e.g., `vtkRenderingCore`) |
| `class_doc` | VTK | Raw documentation from `help()` |
| `role` | **Introspection** | Pipeline role: `input`, `filter`, `output`, `properties`, `renderer`, etc. |
| `input_datatype` | **Introspection** | Input data type (e.g., `vtkPolyData`) |
| `output_datatype` | **Introspection** | Output data type |
| `semantic_methods` | **Introspection** | Non-boilerplate methods |
| `synopsis` | **LLM** | One-sentence summary |
| `action_phrase` | **LLM** | Noun-phrase (e.g., "mesh smoothing") |
| `visibility_score` | **LLM** | 0.0-1.0 likelihood users mention this class |

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
uv sync --extra dev

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=vtk_python_docs

# Lint code
uv run ruff check .

# Type check
uv run pyright vtk_python_docs/
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
