"""Tulip-style token-budget batcher.

Perplexity: for small embedding models, latency tracks token count, not
sequence count; ~512 tokens saturates a sub-1B model. We reuse that rule for
agent memory ingest/maintain batches under a configurable token budget.
"""

from __future__ import annotations

from typing import List, Sequence, Tuple, TypeVar

T = TypeVar("T")


class TokenBudgetBatcher:
    def __init__(self, token_budget: int = 512) -> None:
        if token_budget < 1:
            raise ValueError("token_budget must be >= 1")
        self.token_budget = token_budget

    def estimate_tokens(self, text: str) -> int:
        # Cheap whitespace estimate; Ivy would tokenize for real.
        return max(1, len(text.split()))

    def pack(self, items: Sequence[Tuple[T, int]]) -> List[List[Tuple[T, int]]]:
        """Pack (payload, token_count) into batches that never exceed budget.

        Oversized single items get their own batch (Ivy chunk-split analog is
        upstream; here we refuse silent truncation).
        """
        batches: List[List[Tuple[T, int]]] = []
        current: List[Tuple[T, int]] = []
        used = 0
        for item, tokens in items:
            tokens = max(1, int(tokens))
            if tokens > self.token_budget:
                if current:
                    batches.append(current)
                    current, used = [], 0
                batches.append([(item, tokens)])
                continue
            if used + tokens > self.token_budget and current:
                batches.append(current)
                current, used = [], 0
            current.append((item, tokens))
            used += tokens
        if current:
            batches.append(current)
        return batches
