"""Karpathy/Neo4j wiki-graph steal: navigate links. Fail closed. No Aura."""

from __future__ import annotations

import json
import re
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence
from urllib.parse import unquote, urlparse

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.M)
PAREN_RE = re.compile(r"\([^)]*\)")
NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")
TOKEN_RE = re.compile(r"[a-z0-9]+", re.I)
MD_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
WIKI_LINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#([^\]|]+))?(?:\|[^\]]+)?\]\]")
PROXY_METRICS = frozenset({"tokens", "pr_velocity", "daily_messages"})
METERED_ENGINES = frozenset(
    {"neo4j_aura", "aura", "ki", "ki_install", "podman_neo4j", "embeddings"}
)
VECTOR_ENGINES = frozenset({"vector_only", "vector", "rag_flat"})
IAP_WEIGHT = 10
TASK_WEIGHT = 5


@dataclass(frozen=True)
class ControlDecision:
    action: str
    ok: bool
    reason: str
    addresses: tuple[str, ...] = ()


def _norm(value: str) -> str:
    return (value or "").strip().lower().replace("-", "_").replace(".", "_")


def _slug(title: str) -> str:
    stripped = PAREN_RE.sub("", title or "")
    return NON_ALNUM_RE.sub("-", stripped.lower()).strip("-")


def _tokens(text: str) -> set[str]:
    return set(TOKEN_RE.findall((text or "").lower()))


def evaluate_index(*, engine: str) -> ControlDecision:
    name = _norm(engine)
    if name in {"local_graph", "wiki_graph", "markdown_graph"}:
        return ControlDecision(
            action="allow_local_graph",
            ok=True,
            reason="navigate the wiki the docs already form",
        )
    if name in VECTOR_ENGINES:
        return ControlDecision(
            action="block_vector_only",
            ok=False,
            reason="similarity is not shape; hop the links instead",
        )
    if name in METERED_ENGINES or "aura" in name or "neo4j" in name:
        return ControlDecision(
            action="block_metered",
            ok=False,
            reason="Aura, ki, and Neo4j are outside the monthly cap",
        )
    return ControlDecision(
        action="block_metered",
        ok=False,
        reason="unknown index engine is denied",
    )


def _resolve_link(*, source: str, raw: str) -> str:
    target = (raw or "").strip()
    if not target or target.startswith("#"):
        return f"{source}{target}" if target else source
    parsed = urlparse(target)
    if parsed.scheme in {"http", "https", "mailto"}:
        return ""
    path_part = unquote(parsed.path or target.split("#", 1)[0])
    frag = parsed.fragment or (target.split("#", 1)[1] if "#" in target else "")
    if not path_part.endswith(".md") and "/" not in path_part:
        path_part = f"{path_part}.md" if path_part else path_part
    base = Path(source).parent
    resolved = (base / path_part).as_posix() if path_part else source
    resolved = resolved.replace("/./", "/")
    if frag:
        return f"{resolved}#{_slug(frag)}"
    return resolved


def build_graph(*, pages: Sequence[Mapping[str, str]]) -> dict[str, object]:
    nodes: dict[str, dict[str, object]] = {}
    edges: list[dict[str, str]] = []

    def add_node(address: str, text: str) -> None:
        existing = nodes.get(address)
        blob = text if not existing else f"{existing['text']}\n{text}"
        nodes[address] = {"address": address, "text": blob}

    for page in pages:
        path = str(page.get("path") or "").strip()
        markdown = page.get("markdown") or ""
        if not path:
            continue
        add_node(path, f"{path}\n{markdown}")
        for match in HEADING_RE.finditer(markdown):
            slug = _slug(match.group(2))
            if not slug:
                continue
            address = f"{path}#{slug}"
            add_node(address, match.group(2))
            edges.append({"kind": "HAS", "source": path, "target": address})

        for match in MD_LINK_RE.finditer(markdown):
            dest = _resolve_link(source=path, raw=match.group(2))
            if dest:
                edges.append({"kind": "LINKS_TO", "source": path, "target": dest})
        for match in WIKI_LINK_RE.finditer(markdown):
            raw = match.group(1)
            if match.group(2):
                raw = f"{raw}#{match.group(2)}"
            dest = _resolve_link(source=path, raw=raw)
            if dest:
                edges.append({"kind": "LINKS_TO", "source": path, "target": dest})

    return {"nodes": nodes, "edges": edges}


def navigate(
    *,
    query: str,
    graph: Mapping[str, object],
    max_hops: int = 2,
) -> ControlDecision:
    nodes = graph.get("nodes") or {}
    edges = graph.get("edges") or []
    if not isinstance(nodes, dict) or not nodes:
        return ControlDecision(
            action="block_no_walk",
            ok=False,
            reason="no wiki graph to walk",
        )
    q = _tokens(query)
    seeds = [
        addr
        for addr, node in nodes.items()
        if q and _tokens(str(node.get("text") or "")) & q
    ]
    if not seeds:
        return ControlDecision(
            action="block_no_walk",
            ok=False,
            reason="query does not land on a graph node",
        )

    adj: dict[str, set[str]] = {}
    for edge in edges:
        if not isinstance(edge, Mapping):
            continue
        src = str(edge.get("source") or "")
        dst = str(edge.get("target") or "")
        if src and dst:
            adj.setdefault(src, set()).add(dst)
            adj.setdefault(dst, set()).add(src)

    seen: set[str] = set()
    queue: deque[tuple[str, int]] = deque((seed, 0) for seed in seeds)
    while queue:
        addr, hops = queue.popleft()
        if addr in seen:
            continue
        seen.add(addr)
        if hops >= int(max_hops):
            continue
        for nxt in adj.get(addr, ()):
            if nxt not in seen:
                queue.append((nxt, hops + 1))

    return ControlDecision(
        action="allow_walk",
        ok=True,
        reason="walked containment and links instead of dumping the corpus",
        addresses=tuple(sorted(seen)),
    )


def evaluate_walk(*, cite: str, addresses: Sequence[str]) -> ControlDecision:
    target = (cite or "").strip()
    if target and target in set(addresses):
        return ControlDecision(
            action="allow_on_graph",
            ok=True,
            reason="cite sits on the walked path",
        )
    return ControlDecision(
        action="block_off_graph",
        ok=False,
        reason="cite is not on a walkable wiki path",
    )


def rank_work(*, candidates: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    scored: list[tuple[float, dict[str, object]]] = []
    for raw in candidates:
        row = dict(raw)
        metric = _norm(str(row.get("metric", "")))
        effort = max(float(row.get("effort") or 1), 1.0)
        if metric in PROXY_METRICS:
            score = 0.0
        else:
            iap = float(row.get("expected_iap_attempts") or 0)
            tasks = float(row.get("expected_completed_tasks") or 0)
            score = (iap * IAP_WEIGHT + tasks * TASK_WEIGHT) / effort
        row["score"] = score
        scored.append((score, row))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [row for _, row in scored]


def require_wiki_controls(
    *,
    has_index: bool,
    has_walk: bool,
    has_cite: bool,
) -> ControlDecision:
    if has_index and has_walk and has_cite:
        return ControlDecision(
            action="controls_complete",
            ok=True,
            reason="index, walk, and cite evaluated",
        )
    return ControlDecision(
        action="block_incomplete_controls",
        ok=False,
        reason="fail closed: missing index, walk, or cite",
    )


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Local wiki graph (no Aura).")
    parser.add_argument("--engine", default="")
    parser.add_argument("--pages", default="")
    parser.add_argument("--query", default="")
    parser.add_argument("--cite", default="")
    parser.add_argument("--max-hops", default="2")
    args = parser.parse_args()

    payload: dict[str, object] = {}
    ok = True

    has_index = bool(args.engine)
    if has_index:
        index = evaluate_index(engine=args.engine)
        payload["index"] = {k: v for k, v in index.__dict__.items() if k != "addresses"}
        ok = ok and index.ok

    pages: list[dict[str, str]] = []
    for raw in [part.strip() for part in args.pages.split(",") if part.strip()]:
        path = Path(raw)
        pages.append({"path": raw, "markdown": path.read_text() if path.is_file() else ""})

    has_walk = bool(args.query or pages)
    walk_addresses: list[str] = []
    if has_walk:
        graph = build_graph(pages=pages)
        walked = navigate(query=args.query, graph=graph, max_hops=int(args.max_hops or 2))
        payload["walk"] = {
            "action": walked.action,
            "ok": walked.ok,
            "reason": walked.reason,
            "addresses": list(walked.addresses),
        }
        walk_addresses = list(walked.addresses)
        ok = ok and walked.ok

    has_cite = bool(args.cite)
    if has_cite:
        grounded = evaluate_walk(cite=args.cite, addresses=walk_addresses)
        payload["cite"] = {k: v for k, v in grounded.__dict__.items() if k != "addresses"}
        ok = ok and grounded.ok

    completeness = require_wiki_controls(
        has_index=has_index,
        has_walk=has_walk,
        has_cite=has_cite,
    )
    payload["completeness"] = {
        k: v for k, v in completeness.__dict__.items() if k != "addresses"
    }
    ok = ok and completeness.ok
    print(json.dumps(payload, indent=2))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
