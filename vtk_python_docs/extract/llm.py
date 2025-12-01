"""LLM-based classification and synopsis generation using LiteLLM."""

import asyncio
import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from .roles import ROLE_LABELS, ROLE_DESCRIPTIONS, VISIBILITY_LABELS, VISIBILITY_DESCRIPTIONS

# Load .env from project root
_env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(_env_path)


# Configuration from environment
LLM_MODEL = os.getenv("LLM_MODEL", "")
LLM_RATE_LIMIT = int(os.getenv("LLM_RATE_LIMIT", "60"))
LLM_MAX_CONCURRENT = int(os.getenv("LLM_MAX_CONCURRENT", "10"))


CLASSIFY_PROMPT = """You are classifying VTK (Visualization Toolkit) classes for documentation.

Given a VTK class name and its documentation, return a JSON object with these four fields:

1. "synopsis": A single sentence (max 20 words) summarizing what the class does.
   - Do not start with the class name or "This class" or "A class that"
   - Start directly with what it does

2. "action_phrase": A noun-phrase (max 5 words) describing the primary action.
   - Examples: "mesh smoothing", "file reading", "color mapping", "volume rendering"

3. "role": One of the following role labels that best describes the class:
{role_list}

4. "visibility": How likely users are to mention this class in prompts:
{visibility_list}

Class: {class_name}

Documentation:
{class_doc}

Respond with only the JSON object, no other text:"""


def _build_role_list() -> str:
    """Build formatted role list for prompt."""
    lines = []
    for label in ROLE_LABELS:
        desc = ROLE_DESCRIPTIONS[label]
        lines.append(f"   - {label}: {desc}")
    return "\n".join(lines)


def _build_visibility_list() -> str:
    """Build formatted visibility list for prompt."""
    lines = []
    for label in VISIBILITY_LABELS:
        desc = VISIBILITY_DESCRIPTIONS[label]
        lines.append(f"   - {label}: {desc}")
    return "\n".join(lines)

def check_llm_configured() -> None:
    """Check if LLM is properly configured, exit with instructions if not."""
    if not LLM_MODEL:
        print("❌ LLM not configured. Synopsis generation requires an LLM.")
        print()
        print("To configure, create a .env file with:")
        print("  LLM_MODEL=anthropic/claude-3-haiku-20240307")
        print("  ANTHROPIC_API_KEY=your-api-key")
        print()
        print("Or use Ollama (no API key needed):")
        print("  LLM_MODEL=ollama/llama3")
        print()
        print("See .env.example for more options.")
        raise SystemExit(1)

    # Check for required API keys based on model
    model_lower = LLM_MODEL.lower()
    missing_key = None

    if model_lower.startswith("ollama/"):
        return  # Ollama doesn't need API key
    elif "gpt" in model_lower or "openai" in model_lower:
        if not os.getenv("OPENAI_API_KEY"):
            missing_key = "OPENAI_API_KEY"
    elif "claude" in model_lower or "anthropic" in model_lower:
        if not os.getenv("ANTHROPIC_API_KEY"):
            missing_key = "ANTHROPIC_API_KEY"
    elif "gemini" in model_lower:
        if not os.getenv("GEMINI_API_KEY"):
            missing_key = "GEMINI_API_KEY"

    if missing_key:
        print(f"❌ LLM model '{LLM_MODEL}' requires {missing_key}")
        print()
        print("Add to your .env file:")
        print(f"  {missing_key}=your-api-key")
        raise SystemExit(1)


async def classify_class(class_name: str, class_doc: str) -> dict[str, Any] | None:
    """Classify a VTK class using LLM.

    Returns a dict with synopsis, action_phrase, role, and visibility.

    Args:
        class_name: Name of the VTK class.
        class_doc: Class documentation text.

    Returns:
        Classification dict or None if failed.
    """
    if not class_doc or not class_doc.strip():
        return None

    try:
        import litellm

        # Truncate long docs to avoid token limits
        max_doc_length = 2000
        if len(class_doc) > max_doc_length:
            class_doc = class_doc[:max_doc_length] + "..."

        # Build prompt with role and visibility lists
        prompt = CLASSIFY_PROMPT.format(
            class_name=class_name,
            class_doc=class_doc,
            role_list=_build_role_list(),
            visibility_list=_build_visibility_list(),
        )

        response = await litellm.acompletion(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.3,
        )

        # Extract and parse JSON response
        content = response.choices[0].message.content  # type: ignore
        if not content:
            return None

        # Clean up response - remove markdown code blocks if present
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1] if "\n" in content else content[3:]
        if content.endswith("```"):
            content = content.rsplit("```", 1)[0]
        content = content.strip()

        result = json.loads(content)

        # Validate and clean up result
        if "synopsis" in result:
            synopsis = result["synopsis"].strip().strip("\"'")
            if synopsis and not synopsis.endswith("."):
                synopsis += "."
            result["synopsis"] = synopsis

        # Validate role is in allowed list
        if result.get("role") not in ROLE_LABELS:
            result["role"] = "utility_helper"

        # Validate visibility is in allowed list
        if result.get("visibility") not in VISIBILITY_LABELS:
            result["visibility"] = "unlikely"

        return result

    except json.JSONDecodeError as e:
        print(f"⚠️  JSON parse error for {class_name}: {e}")
        return None
    except Exception as e:
        print(f"⚠️  LLM error for {class_name}: {e}")
        return None


async def classify_classes_batch(
    items: list[tuple[str, str]],
    max_concurrent: int | None = None,
    rate_limit: int | None = None,
) -> dict[str, dict[str, Any] | None]:
    """Classify multiple VTK classes with rate limiting.

    Args:
        items: List of (class_name, class_doc) tuples.
        max_concurrent: Maximum concurrent requests.
        rate_limit: Requests per minute limit.

    Returns:
        Dictionary mapping class_name to classification dict.
    """
    max_concurrent = max_concurrent or LLM_MAX_CONCURRENT
    rate_limit = rate_limit or LLM_RATE_LIMIT

    semaphore = asyncio.Semaphore(max_concurrent)
    results: dict[str, dict[str, Any] | None] = {}
    delay = 60.0 / rate_limit if rate_limit > 0 else 0

    async def process_item(class_name: str, class_doc: str, index: int):
        async with semaphore:
            if delay > 0 and index > 0:
                await asyncio.sleep(delay * (index % max_concurrent))
            results[class_name] = await classify_class(class_name, class_doc)

    tasks = [process_item(name, doc, i) for i, (name, doc) in enumerate(items)]
    await asyncio.gather(*tasks, return_exceptions=True)

    return results
