#!/usr/bin/env python3
"""Extract LLM classifications from vtk-python-docs.jsonl to a cache file.

This script reads the existing JSONL output and extracts the LLM-computed fields
(synopsis, action_phrase, visibility_score) into a separate cache file.

Usage:
    python scripts/extract_llm_cache.py
"""

import json
from pathlib import Path


def main():
    project_root = Path(__file__).parent.parent
    input_path = project_root / "docs" / "vtk-python-docs.jsonl"
    output_path = project_root / "docs" / "llm-cache.jsonl"

    if not input_path.exists():
        print(f"❌ Input file not found: {input_path}")
        return 1

    print(f"📖 Reading {input_path}...")

    cache_records = []
    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            record = json.loads(line)

            class_name = record.get("class_name", "")
            synopsis = record.get("synopsis", "")
            action_phrase = record.get("action_phrase", "")
            visibility_score = record.get("visibility_score", 0.3)

            # Only cache if we have meaningful LLM output
            if synopsis or action_phrase:
                cache_records.append({
                    "class_name": class_name,
                    "synopsis": synopsis,
                    "action_phrase": action_phrase,
                    "visibility_score": visibility_score,
                })

    print(f"💾 Writing {len(cache_records)} records to {output_path}...")

    with open(output_path, "w", encoding="utf-8") as f:
        for record in cache_records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"✅ Done! Cache file created: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
