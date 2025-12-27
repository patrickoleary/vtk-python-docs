"""LLM-based classification and synopsis generation using LiteLLM.

Code map:
    check_llm_configured()         Verify LLM is configured, exit if not
    classify_class()               Classify a single VTK class (async)
    classify_classes_batch()       Classify multiple classes with rate limiting (async)
        _load_cache()              Load cached classifications from file
"""

import asyncio
import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

# Load .env from project root
_env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(_env_path)

# Cache file path
_cache_path = Path(__file__).parent.parent.parent / "docs" / "llm-cache.jsonl"
_llm_cache: dict[str, dict[str, Any]] | None = None


def _load_cache() -> dict[str, dict[str, Any]]:
    """Load LLM classification cache from file."""
    global _llm_cache
    if _llm_cache is not None:
        return _llm_cache

    _llm_cache = {}
    if _cache_path.exists():
        with open(_cache_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    record = json.loads(line)
                    _llm_cache[record["class_name"]] = record
    return _llm_cache


# Configuration from environment
LLM_MODEL = os.getenv("LLM_MODEL", "")
LLM_RATE_LIMIT = int(os.getenv("LLM_RATE_LIMIT", "60"))
LLM_MAX_CONCURRENT = int(os.getenv("LLM_MAX_CONCURRENT", "10"))


CLASSIFY_PROMPT = """You are classifying VTK (Visualization Toolkit) classes for documentation.

Given a VTK class name and its documentation, return a JSON object with these three fields:

1. "synopsis": A single sentence (max 20 words) summarizing what the class does.
   - Do not start with the class name or "This class" or "A class that"
   - Start directly with what it does

2. "action_phrase": A noun-phrase (max 5 words) describing the primary action.
   - Examples: "mesh smoothing", "file reading", "color mapping", "volume rendering"

3. "visibility_score": A float score (0.0 to 1.0) indicating how likely users are to mention this class in prompts.
   - 0.9: Classes users actively search for (readers, sources, common filters)
   - 0.7: Classes for specific tasks (properties, widgets, specialized filters)
   - 0.5: Standard pipeline components often copied from examples
   - 0.3: Internal data structures rarely named by users
   - 0.1: Infrastructure and base classes users almost never type

Class: {class_name}

Documentation:
{class_doc}

Respond with only the JSON object, no other text:"""


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

    Returns a dict with synopsis, action_phrase, and visibility_score.

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

        # Build prompt
        prompt = CLASSIFY_PROMPT.format(
            class_name=class_name,
            class_doc=class_doc,
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

        # Validate visibility_score
        visibility = result.pop("visibility", None) or result.get("visibility_score")
        if isinstance(visibility, (int, float)):
            result["visibility_score"] = max(0.0, min(1.0, float(visibility)))
        else:
            result["visibility_score"] = 0.3

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

    Uses cached results when available to avoid expensive LLM calls.

    Args:
        items: List of (class_name, class_doc) tuples.
        max_concurrent: Maximum concurrent requests.
        rate_limit: Requests per minute limit.

    Returns:
        Dictionary mapping class_name to classification dict.
    """
    cache = _load_cache()
    results: dict[str, dict[str, Any] | None] = {}
    uncached_items: list[tuple[str, str]] = []

    # Check cache first
    for class_name, class_doc in items:
        if class_name in cache:
            results[class_name] = cache[class_name]
        else:
            uncached_items.append((class_name, class_doc))

    if cache:
        print(f"   📦 Using {len(results)} cached classifications")

    if not uncached_items:
        return results

    # Process uncached items with LLM
    print(f"   🤖 Calling LLM for {len(uncached_items)} uncached classes...")

    max_concurrent = max_concurrent or LLM_MAX_CONCURRENT
    rate_limit = rate_limit or LLM_RATE_LIMIT

    semaphore = asyncio.Semaphore(max_concurrent)
    delay = 60.0 / rate_limit if rate_limit > 0 else 0

    async def process_item(class_name: str, class_doc: str, index: int):
        async with semaphore:
            if delay > 0 and index > 0:
                await asyncio.sleep(delay * (index % max_concurrent))
            results[class_name] = await classify_class(class_name, class_doc)

    tasks = [process_item(name, doc, i) for i, (name, doc) in enumerate(uncached_items)]
    await asyncio.gather(*tasks, return_exceptions=True)

    return results
