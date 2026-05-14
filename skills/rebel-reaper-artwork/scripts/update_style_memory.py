#!/usr/bin/env python3
"""Merge abstract REBEL REAPER artwork observations into persistent style memory."""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TRAIT_CATEGORIES = [
    "palette_preferences",
    "linework",
    "motifs",
    "lettering_preferences",
    "composition_preferences",
    "texture_preferences",
    "avoid",
]

BASE_MEMORY: dict[str, Any] = {
    "brand_name": "REBEL REAPER",
    "default_text": "REBEL REAPER",
    "style_traits": {category: [] for category in TRAIT_CATEGORIES},
    "observations": [],
    "last_updated": "",
    "_trait_counts": {category: {} for category in TRAIT_CATEGORIES},
}

PROMOTION_THRESHOLD = 2
MAX_DESCRIPTOR_LENGTH = 140
MAX_OBSERVATIONS = 100
UNSAFE_PATTERNS = [
    re.compile(r"data:image/", re.IGNORECASE),
    re.compile(r"base64", re.IGNORECASE),
    re.compile(r"https?://", re.IGNORECASE),
    re.compile(r"/9j/|iVBORw0KGgo|R0lGODlh"),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def empty_memory() -> dict[str, Any]:
    return copy.deepcopy(BASE_MEMORY)


def normalize_descriptor(value: Any) -> str | None:
    """Return a safe abstract descriptor or None for content that should not be stored."""
    if isinstance(value, dict):
        value = value.get("value") or value.get("trait") or value.get("description")
    if not isinstance(value, str):
        return None

    descriptor = " ".join(value.strip().split())
    if not descriptor:
        return None
    if len(descriptor) > MAX_DESCRIPTOR_LENGTH:
        return None
    if any(pattern.search(descriptor) for pattern in UNSAFE_PATTERNS):
        return None
    if len(descriptor.split()) > 18:
        return None
    return descriptor.lower()


def ensure_shape(memory: dict[str, Any]) -> dict[str, Any]:
    merged = empty_memory()
    merged.update({key: value for key, value in memory.items() if key not in {"style_traits", "_trait_counts"}})

    style_traits = memory.get("style_traits", {}) if isinstance(memory.get("style_traits"), dict) else {}
    trait_counts = memory.get("_trait_counts", {}) if isinstance(memory.get("_trait_counts"), dict) else {}
    merged["style_traits"] = {category: [] for category in TRAIT_CATEGORIES}
    merged["_trait_counts"] = {category: {} for category in TRAIT_CATEGORIES}

    for category in TRAIT_CATEGORIES:
        for entry in style_traits.get(category, []):
            normalized = trait_to_entry(entry, category, utc_now())
            if normalized:
                merged["style_traits"][category].append(normalized)
                merged["_trait_counts"][category][normalized["value"]] = max(
                    int(normalized.get("count", 1)),
                    int(trait_counts.get(category, {}).get(normalized["value"], 0) or 0),
                )
        for value, count in trait_counts.get(category, {}).items():
            descriptor = normalize_descriptor(value)
            if descriptor:
                merged["_trait_counts"][category][descriptor] = max(
                    int(count or 0), merged["_trait_counts"][category].get(descriptor, 0)
                )
    return merged


def trait_to_entry(value: Any, category: str, timestamp: str, *, user_declared: bool = False) -> dict[str, Any] | None:
    descriptor = normalize_descriptor(value)
    if descriptor is None:
        return None
    existing_count = 1
    source = "user" if user_declared else "inferred"
    first_seen = timestamp
    if isinstance(value, dict):
        existing_count = int(value.get("count", 1) or 1)
        source = "user" if value.get("user_declared") else value.get("source", source)
        user_declared = bool(value.get("user_declared", user_declared))
        first_seen = value.get("first_seen") or timestamp
    return {
        "value": descriptor,
        "count": existing_count,
        "source": "user" if user_declared else source,
        "user_declared": user_declared,
        "status": "avoid" if category == "avoid" else "active",
        "first_seen": first_seen,
        "last_seen": timestamp,
    }


def entry_index(entries: list[dict[str, Any]], descriptor: str) -> int | None:
    for index, entry in enumerate(entries):
        if entry.get("value") == descriptor:
            return index
    return None


def upsert_trait(memory: dict[str, Any], category: str, value: Any, timestamp: str, *, user_declared: bool = False) -> None:
    entry = trait_to_entry(value, category, timestamp, user_declared=user_declared)
    if not entry:
        return

    descriptor = entry["value"]
    counts = memory["_trait_counts"].setdefault(category, {})
    counts[descriptor] = int(counts.get(descriptor, 0)) + 1

    should_promote = category == "avoid" or entry["user_declared"] or counts[descriptor] >= PROMOTION_THRESHOLD
    if not should_promote:
        return

    traits = memory["style_traits"].setdefault(category, [])
    index = entry_index(traits, descriptor)
    if index is None:
        entry["count"] = counts[descriptor]
        traits.append(entry)
        return

    existing = traits[index]
    existing["count"] = max(int(existing.get("count", 0)), counts[descriptor])
    existing["last_seen"] = timestamp
    if entry["user_declared"] and not existing.get("user_declared"):
        existing["source"] = "user"
        existing["user_declared"] = True
    if category == "avoid":
        existing["status"] = "avoid"


def listify(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def collect_analysis_traits(analysis: dict[str, Any]) -> dict[str, list[Any]]:
    collected = {category: [] for category in TRAIT_CATEGORIES}

    for container_key in ("style_traits", "traits", "analysis"):
        container = analysis.get(container_key)
        if isinstance(container, dict):
            for category in TRAIT_CATEGORIES:
                collected[category].extend(listify(container.get(category)))

    for category in TRAIT_CATEGORIES:
        collected[category].extend(listify(analysis.get(category)))

    corrections = analysis.get("corrections") or analysis.get("rejections") or analysis.get("rejected")
    if isinstance(corrections, dict):
        collected["avoid"].extend(listify(corrections.get("avoid") or corrections.get("rejected_elements")))
    else:
        collected["avoid"].extend(listify(corrections))

    return collected


def collect_user_preferences(analysis: dict[str, Any]) -> dict[str, list[Any]]:
    collected = {category: [] for category in TRAIT_CATEGORIES}
    preferences = analysis.get("user_preferences") or analysis.get("declared_preferences") or {}
    if isinstance(preferences, dict):
        for category in TRAIT_CATEGORIES:
            collected[category].extend(listify(preferences.get(category)))
    return collected


def add_observation(memory: dict[str, Any], analysis: dict[str, Any], timestamp: str, traits_seen: dict[str, list[str]]) -> None:
    summary = normalize_descriptor(analysis.get("summary") or analysis.get("session_summary") or "artwork style observation")
    observation = {
        "timestamp": timestamp,
        "approved": bool(analysis.get("approved", False)),
        "summary": summary or "artwork style observation",
        "traits_seen": {category: values for category, values in traits_seen.items() if values},
        "avoid": traits_seen.get("avoid", []),
    }
    memory.setdefault("observations", []).append(observation)
    memory["observations"] = memory["observations"][-MAX_OBSERVATIONS:]


def merge_analysis(memory: dict[str, Any], analysis: dict[str, Any], timestamp: str) -> None:
    inferred_traits = collect_analysis_traits(analysis)
    user_traits = collect_user_preferences(analysis)
    seen_for_observation = {category: [] for category in TRAIT_CATEGORIES}

    for category, values in inferred_traits.items():
        for value in values:
            descriptor = normalize_descriptor(value)
            if descriptor:
                seen_for_observation[category].append(descriptor)
                upsert_trait(memory, category, descriptor, timestamp, user_declared=False)

    for category, values in user_traits.items():
        for value in values:
            descriptor = normalize_descriptor(value)
            if descriptor:
                seen_for_observation[category].append(descriptor)
                upsert_trait(memory, category, descriptor, timestamp, user_declared=True)

    add_observation(memory, analysis, timestamp, seen_for_observation)
    memory["last_updated"] = timestamp


def load_json_file(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_analyses(paths: list[Path]) -> list[dict[str, Any]]:
    if not paths:
        data = json.load(sys.stdin)
        return data if isinstance(data, list) else [data]

    analyses: list[dict[str, Any]] = []
    for path in paths:
        data = load_json_file(path)
        analyses.extend(data if isinstance(data, list) else [data])
    return [analysis for analysis in analyses if isinstance(analysis, dict)]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("analysis", nargs="*", type=Path, help="JSON artwork analysis file(s); reads stdin if omitted")
    parser.add_argument(
        "--memory",
        type=Path,
        default=Path(".agents/memory/rebel-reaper-style.json"),
        help="Path to persistent style memory JSON",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    timestamp = utc_now()

    if args.memory.exists():
        memory = ensure_shape(load_json_file(args.memory))
    else:
        memory = empty_memory()

    analyses = load_analyses(args.analysis)
    for analysis in analyses:
        merge_analysis(memory, analysis, timestamp)

    args.memory.parent.mkdir(parents=True, exist_ok=True)
    with args.memory.open("w", encoding="utf-8") as handle:
        json.dump(memory, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
