"""O sorteio determinístico: SplitMix64 em inteiros, sem gerador global nem ``hash()`` nativo."""

from __future__ import annotations

_MASK64 = (1 << 64) - 1


class Stream:
    def __init__(self, seed: int) -> None:
        self._state = seed & _MASK64

    def _next_u64(self) -> int:
        self._state = (self._state + 0x9E3779B97F4A7C15) & _MASK64
        z = self._state
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & _MASK64
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & _MASK64
        return z ^ (z >> 31)

    def randint(self, lo: int, hi: int) -> int:
        """Inteiro uniforme em [lo, hi], sem viés (por rejeição)."""
        span = hi - lo + 1
        limit = (1 << 64) - ((1 << 64) % span)
        while True:
            v = self._next_u64()
            if v < limit:
                return lo + v % span
