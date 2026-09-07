#!/usr/bin/env python3
"""
Self-Organizing Agent Memory System

Structured, scene-aware memory cells that consolidate, decay, and self-organize.
Replaces flat lessons-learned.md + raw feedback logs with intelligent retrieval.

Dependencies: Python stdlib only (no ML, no LanceDB, no pip install).

Usage:
    python memory_manager.py --ingest            # Ingest unprocessed feedback
    python memory_manager.py --recall            # Recall high-salience memories
    python memory_manager.py --recall --scene X  # Scene-specific recall
    python memory_manager.py --maintain          # Decay + consolidate
    python memory_manager.py --seed              # Seed from lessons-learned.md
    python memory_manager.py --stats             # Show memory stats
"""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

_UTC = timezone.utc
from typing import List, Optional

SCENES = {
    "store-publishing": [
        "publish", "store", "play console", "testflight", "app store",
        "fastlane", "google play", "app connect", "release",
    ],
    "code-editing": [
        "edit", "write", "implement", "refactor", "fix bug", "code change",
    ],
    "git-operations": [
        "commit", "push", "branch", "merge", "pull request", "rebase",
    ],
    "testing": [
        "test", "jest", "coverage", "assert", "verify", "maestro",
        "espresso", "xctest",
    ],
    "debugging": [
        "debug", "error", "crash", "stack trace", "investigate", "diagnose",
    ],
    "automation": [
        "automate", "api", "cli", "script", "hook", "workflow",
    ],
    "animation-parity": [
        "animation", "shimmer", "pulsing", "circle", "parity", "timing",
    ],
    "credentials": [
        "secret", "key", "password", "credential", "token", "2fa", "auth",
    ],
}

CELL_TYPE_KEYWORDS = {
    "risk": ["lie", "lying", "wrong", "incorrect", "false", "claim", "never"],
    "pattern": ["pattern", "repeated", "again", "keeps", "always"],
    "decision": ["decided", "chose", "approach", "strategy", "went with"],
    "preference": ["prefer", "want", "should", "must", "mandate"],
}


def classify_scene(text: str) -> str:
    text_lower = text.lower()
    best_scene = "general"
    best_score = 0
    for scene, keywords in SCENES.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > best_score:
            best_score = score
            best_scene = scene
    return best_scene


def classify_cell_type(text: str, is_negative: bool) -> str:
    text_lower = text.lower()
    if is_negative:
        for kw in CELL_TYPE_KEYWORDS["risk"]:
            if kw in text_lower:
                return "risk"
    for cell_type, keywords in CELL_TYPE_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return cell_type
    return "risk" if is_negative else "fact"


def extract_text(entry: dict) -> str:
    parts = []
    for key in ("context", "user_message", "prompt", "message"):
        val = entry.get(key, "")
        if not isinstance(val, str) or not val:
            continue
        # user_message often contains embedded JSON with a "prompt" field
        if val.startswith("{"):
            try:
                # Newlines from outer JSON parsing break inner JSON
                cleaned = val.replace("\n", " ").replace("\r", " ")
                parsed = json.loads(cleaned)
                val = parsed.get("prompt", parsed.get("context", val))
            except (json.JSONDecodeError, TypeError):
                pass
        if isinstance(val, str):
            parts.append(val[:300])
    return " ".join(parts) if parts else str(entry)[:300]


def compress_content(text: str) -> str:
    # Try to parse JSON wrapper and extract prompt/context
    if text.startswith("{"):
        try:
            cleaned = text.replace("\n", " ").replace("\r", " ")
            parsed = json.loads(cleaned)
            text = parsed.get("prompt", parsed.get("context", text))
        except (json.JSONDecodeError, TypeError):
            pass
    text = re.sub(r"https?://\S+", "", text)
    # Strip JSON-like blobs, session IDs, paths
    text = re.sub(r'\{"session_id":[^}]*\}', "", text)
    text = re.sub(r"/Users/\S+", "", text)
    text = re.sub(r"\{[^}]*\}", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:200]


def word_overlap(a: str, b: str) -> float:
    words_a = set(re.findall(r"\w{3,}", a.lower()))
    words_b = set(re.findall(r"\w{3,}", b.lower()))
    if not words_a or not words_b:
        return 0.0
    return len(words_a & words_b) / len(words_a | words_b)


def _is_negative(entry: dict) -> bool:
    if entry.get("reward", 0) < 0:
        return True
    if entry.get("feedback", "").startswith("negative"):
        return True
    if entry.get("signal", "").startswith("negative"):
        return True
    return False


def _now_utc() -> str:
    return datetime.now(tz=_UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_ts(ts_str: str) -> datetime:
    clean = ts_str.replace("Z", "").split("+")[0]
    return datetime.fromisoformat(clean).replace(tzinfo=_UTC)


class MemoryManager:
    def __init__(self, memory_dir: Path):
        self.memory_dir = memory_dir
        self.cells_file = memory_dir / "memory_cells.jsonl"
        self.feedback_log = memory_dir / "feedback" / "feedback-log.jsonl"

    def load_cells(self) -> List[dict]:
        if not self.cells_file.exists():
            return []
        cells = []
        with open(self.cells_file) as f:
            for line in f:
                if line.strip():
                    try:
                        cells.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return cells

    def save_cells(self, cells: List[dict]):
        self.cells_file.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.cells_file.with_suffix(".tmp")
        with open(tmp, "w") as f:
            for cell in cells:
                f.write(json.dumps(cell) + "\n")
        tmp.rename(self.cells_file)

    def ingest(self, entry: dict) -> dict:
        cells = self.load_cells()
        cell = self._ingest_into(cells, entry)
        self.save_cells(cells)
        return cell

    def recall(
        self,
        scene: Optional[str] = None,
        min_salience: float = 0.2,
        limit: int = 10,
        query: Optional[str] = None,
        embed_dim: int = 64,
    ) -> List[dict]:
        """Recall cells by salience, optionally re-ranked with ROSE-lite embeddings.

        When `query` is set, hybrid score = 0.45*salience + 0.55*cosine(query, content).
        This mirrors Perplexity's unified LLM/embed stack: one retrieval path, no
        separate paid vector DB.
        """
        cells = self.load_cells()
        if scene:
            cells = [c for c in cells if c["scene"] == scene]
        cells = [c for c in cells if c["salience"] >= min_salience]
        if not query:
            cells.sort(key=lambda c: c["salience"], reverse=True)
            return cells[:limit]

        # Lazy import keeps memory_manager stdlib-only unless hybrid recall is used.
        import sys
        from pathlib import Path as _Path

        scripts_root = _Path(__file__).resolve().parents[3] / "scripts"
        if str(scripts_root) not in sys.path:
            sys.path.insert(0, str(scripts_root))
        from agent_rose_lite.embeddings import MatryoshkaEmbedder, cosine_similarity

        emb = MatryoshkaEmbedder(dims=(max(embed_dim, 64), 64, 32, 16))
        qv = emb.embed(query, dim=embed_dim)

        def hybrid(cell: dict) -> float:
            cv = emb.embed(cell.get("content", ""), dim=embed_dim)
            return 0.45 * float(cell.get("salience", 0)) + 0.55 * cosine_similarity(qv, cv)

        cells.sort(key=hybrid, reverse=True)
        return cells[:limit]

    def decay(self, half_life_days: float = 14.0) -> int:
        cells = self.load_cells()
        now = datetime.now(tz=_UTC)
        pruned = []
        for cell in cells:
            try:
                last = _parse_ts(cell["last_seen"])
                age_days = (now - last).total_seconds() / 86400
                cell["salience"] = round(
                    cell["salience"] * (2 ** (-age_days / half_life_days)), 4
                )
            except (ValueError, KeyError):
                pass
            if cell["salience"] >= 0.05:
                pruned.append(cell)
        self.save_cells(pruned)
        return len(cells) - len(pruned)

    def consolidate(self, threshold: float = 0.4) -> int:
        cells = self.load_cells()
        skip: set = set()
        merged = []
        for i, a in enumerate(cells):
            if i in skip:
                continue
            for j in range(i + 1, len(cells)):
                if j in skip:
                    continue
                b = cells[j]
                if a["scene"] == b["scene"] and word_overlap(a["content"], b["content"]) > threshold:
                    a["evidence_count"] += b["evidence_count"]
                    a["salience"] = min(1.0, max(a["salience"], b["salience"]) + 0.1)
                    a["last_seen"] = max(a["last_seen"], b["last_seen"])
                    a["source_ids"] = list(set(a["source_ids"] + b["source_ids"]))
                    if len(b["content"]) > len(a["content"]):
                        a["content"] = b["content"]
                    skip.add(j)
            merged.append(a)
        self.save_cells(merged)
        return len(cells) - len(merged)

    def seed_from_lessons(self, lessons_file: Path) -> int:
        if not lessons_file.exists():
            return 0
        content = lessons_file.read_text()
        sections = re.split(r"^## ", content, flags=re.MULTILINE)
        count = 0
        for section in sections[1:]:
            lines = section.strip().split("\n")
            title = lines[0].strip()
            body = "\n".join(lines[1:])
            text = f"{title} {body}"
            scene = classify_scene(text)
            is_critical = "CRITICAL" in text[:200]
            cell_type = classify_cell_type(text, is_critical or "lie" in text.lower())
            salience = 0.9 if is_critical else 0.6
            cells = self.load_cells()
            cell = {
                "id": f"cell_lesson_{count}",
                "scene": scene,
                "cell_type": cell_type,
                "salience": salience,
                "content": compress_content(f"{title}. {body[:300]}"),
                "evidence_count": 1,
                "first_seen": "2026-02-05T00:00:00Z",
                "last_seen": _now_utc(),
                "source_ids": [f"lesson_{count}"],
            }
            cells.append(cell)
            self.save_cells(cells)
            count += 1
        return count

    def _ingest_into(self, cells: List[dict], entry: dict) -> dict:
        """Ingest a single entry into an in-memory cell list (no disk I/O)."""
        text = extract_text(entry)
        scene = classify_scene(text)
        negative = _is_negative(entry)
        cell_type = classify_cell_type(text, negative)
        content = compress_content(text)
        raw_intensity = entry.get("intensity")
        if raw_intensity is not None:
            intensity = float(raw_intensity) / 5.0
        else:
            intensity = 0.8 if negative else 0.5
        now = _now_utc()
        entry_id = entry.get("id", f"fb_{entry.get('timestamp', now)}")

        for cell in cells:
            if cell["scene"] == scene and word_overlap(cell["content"], content) > 0.3:
                cell["evidence_count"] += 1
                cell["salience"] = min(1.0, cell["salience"] + intensity * 0.15)
                cell["last_seen"] = now
                if entry_id not in cell["source_ids"]:
                    cell["source_ids"].append(entry_id)
                return cell

        cell = {
            "id": f"cell_{scene}_{len(cells)}",
            "scene": scene,
            "cell_type": cell_type,
            "salience": round(max(0.3, intensity), 3),
            "content": content,
            "evidence_count": 1,
            "first_seen": now,
            "last_seen": now,
            "source_ids": [entry_id],
        }
        cells.append(cell)
        return cell

    def ingest_all_unprocessed(self) -> int:
        if not self.feedback_log.exists():
            return 0
        cells = self.load_cells()
        existing_ids: set = set()
        for cell in cells:
            existing_ids.update(cell.get("source_ids", []))
        count = 0
        with open(self.feedback_log) as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                    entry_id = entry.get("id", f"fb_{entry.get('timestamp', '')}")
                    if entry_id not in existing_ids:
                        entry["id"] = entry_id
                        self._ingest_into(cells, entry)
                        existing_ids.add(entry_id)
                        count += 1
                except json.JSONDecodeError:
                    continue
        if count > 0:
            self.save_cells(cells)
        return count

    def stats(self) -> dict:
        cells = self.load_cells()
        scenes: dict = {}
        types: dict = {}
        for cell in cells:
            scenes[cell["scene"]] = scenes.get(cell["scene"], 0) + 1
            types[cell["cell_type"]] = types.get(cell["cell_type"], 0) + 1
        avg_salience = sum(c["salience"] for c in cells) / len(cells) if cells else 0
        return {
            "total_cells": len(cells),
            "by_scene": scenes,
            "by_type": types,
            "avg_salience": round(avg_salience, 3),
            "high_salience": sum(1 for c in cells if c["salience"] >= 0.7),
        }


def format_recall(cells: List[dict]) -> str:
    if not cells:
        return "No relevant memories."
    icons = {"risk": "!", "pattern": "~", "decision": ">", "preference": "*", "fact": "-"}
    lines = []
    for cell in cells:
        icon = icons.get(cell["cell_type"], "-")
        bar = "#" * int(cell["salience"] * 5) + "-" * (5 - int(cell["salience"] * 5))
        line = f"  {icon} [{bar}] [{cell['scene']}] {cell['content'][:120]}"
        if cell["evidence_count"] > 1:
            line += f"\n    (seen {cell['evidence_count']}x, last: {cell['last_seen'][:10]})"
        lines.append(line)
    return "\n".join(lines)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Self-Organizing Agent Memory")
    parser.add_argument("--ingest", action="store_true", help="Ingest feedback (stdin or log)")
    parser.add_argument("--recall", action="store_true", help="Recall memories")
    parser.add_argument("--scene", type=str, help="Filter by scene")
    parser.add_argument("--query", type=str, help="Hybrid semantic recall query (ROSE-lite)")
    parser.add_argument("--maintain", action="store_true", help="Decay + consolidate")
    parser.add_argument("--seed", action="store_true", help="Seed from lessons-learned.md")
    parser.add_argument("--stats", action="store_true", help="Show stats")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--memory-dir", type=str, help="Override memory directory")

    args = parser.parse_args()

    if args.memory_dir:
        memory_dir = Path(args.memory_dir)
    else:
        memory_dir = Path(__file__).parent.parent.parent / "memory"

    mgr = MemoryManager(memory_dir)

    if args.ingest:
        if not sys.stdin.isatty():
            stdin_data = sys.stdin.read().strip()
            if stdin_data:
                try:
                    entry = json.loads(stdin_data)
                    cell = mgr.ingest(entry)
                    if args.json:
                        print(json.dumps(cell))
                    else:
                        print(f"Ingested -> [{cell['scene']}] {cell['content'][:80]}")
                except json.JSONDecodeError:
                    print("Error: Invalid JSON on stdin", file=sys.stderr)
                    sys.exit(1)
                return
        count = mgr.ingest_all_unprocessed()
        if args.json:
            print(json.dumps({"ingested": count}))
        else:
            print(f"Ingested {count} new entries.")

    elif args.recall:
        cells = mgr.recall(scene=args.scene, query=args.query)
        if args.json:
            print(json.dumps(cells, indent=2))
        else:
            print(format_recall(cells))

    elif args.maintain:
        pruned = mgr.decay()
        merged = mgr.consolidate()
        if args.json:
            print(json.dumps({"pruned": pruned, "merged": merged}))
        else:
            print(f"Decay: pruned {pruned}. Consolidate: merged {merged}.")

    elif args.seed:
        lessons_file = memory_dir / "lessons-learned.md"
        count = mgr.seed_from_lessons(lessons_file)
        if args.json:
            print(json.dumps({"seeded": count}))
        else:
            print(f"Seeded {count} cells from lessons-learned.md")

    elif args.stats:
        s = mgr.stats()
        if args.json:
            print(json.dumps(s, indent=2))
        else:
            print(f"Cells: {s['total_cells']}  High salience: {s['high_salience']}  Avg: {s['avg_salience']}")
            for scene, n in sorted(s["by_scene"].items(), key=lambda x: -x[1]):
                print(f"  {scene}: {n}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
