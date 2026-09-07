"""Ivy-lite request gateway: prepare/chunk text before Tulip batching."""

from __future__ import annotations

from typing import List, Tuple

from .tulip_batch import TokenBudgetBatcher


def prepare_texts(texts: List[str], token_budget: int = 512) -> List[List[str]]:
    batcher = TokenBudgetBatcher(token_budget=token_budget)
    items: List[Tuple[str, int]] = [(t, batcher.estimate_tokens(t)) for t in texts]
    return [[payload for payload, _ in batch] for batch in batcher.pack(items)]
