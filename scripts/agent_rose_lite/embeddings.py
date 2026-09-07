"""Matryoshka hash embeddings + lazy capture (CUDA-graph analog).

Zero-cost stdlib substitute for GPU embedding serving:
- Hashing trick + L2-normalized bags → dense vectors (no pip, no GPU)
- Matryoshka dims: full vector prefix-truncates to smaller dims
- LazyTensor + lazy capture cache mirrors Perplexity ROSE CUDA graph replay
"""

from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

_TOKEN_RE = re.compile(r"[a-z0-9]+", re.I)


def _tokens(text: str) -> List[str]:
    return _TOKEN_RE.findall(text.lower())


def _hash_bucket(token: str, dim: int) -> int:
    digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, "big") % dim


def _l2_normalize(vec: List[float]) -> List[float]:
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    if not a or not b:
        return 0.0
    n = min(len(a), len(b))
    return sum(a[i] * b[i] for i in range(n))


@dataclass
class LazyTensor:
    """Deferred embedding result (LazyTensor / async D2H analog)."""

    key: str
    dim: int
    captured: bool = False
    _value: Optional[List[float]] = field(default=None, repr=False)
    _producer: Optional[object] = field(default=None, repr=False)

    def resolve(self) -> List[float]:
        if self._value is None:
            assert self._producer is not None
            self._value = self._producer._compute(self.key, self.dim)  # type: ignore[attr-defined]
            self.captured = True
            self._producer._cache[self.key, self.dim] = self._value  # type: ignore[attr-defined]
        else:
            self.captured = True
        return self._value


class MatryoshkaEmbedder:
    """Dense bag-of-hashes embedder with Matryoshka truncation + lazy cache."""

    def __init__(self, dims: Tuple[int, ...] = (256, 64, 32)) -> None:
        if not dims:
            raise ValueError("dims required")
        self.dims = tuple(sorted(dims, reverse=True))
        self.max_dim = self.dims[0]
        self._cache: Dict[Tuple[str, int], List[float]] = {}

    def _compute(self, text: str, dim: int) -> List[float]:
        vec = [0.0] * dim
        for tok in _tokens(text):
            idx = _hash_bucket(tok, dim)
            # signed hashing reduces collisions
            sign = 1.0 if (hashlib.md5(tok.encode()).digest()[0] % 2 == 0) else -1.0
            vec[idx] += sign
        return _l2_normalize(vec)

    def embed(self, text: str, dim: Optional[int] = None) -> List[float]:
        target = dim or self.max_dim
        if target not in self.dims and target != self.max_dim:
            # allow arbitrary truncation of max_dim for Matryoshka prefix
            if target > self.max_dim:
                raise ValueError(f"dim {target} exceeds max {self.max_dim}")
        full = self._cache.get((text, self.max_dim))
        if full is None:
            full = self._compute(text, self.max_dim)
            self._cache[(text, self.max_dim)] = full
        if target == self.max_dim:
            return list(full)
        # Matryoshka: exact prefix of the full vector (no re-norm) so dims nest.
        truncated = list(full[:target])
        self._cache[(text, target)] = truncated
        return truncated

    def embed_lazy(self, text: str, dim: Optional[int] = None) -> LazyTensor:
        target = dim or self.max_dim
        cached = self._cache.get((text, target))
        if cached is not None:
            return LazyTensor(key=text, dim=target, captured=True, _value=list(cached), _producer=self)
        return LazyTensor(key=text, dim=target, captured=False, _value=None, _producer=self)
