"""As oito direções (S, SW, W, NW, N, NE, E, SE) e o azimute de cada uma, de 45 em 45 graus a partir da S."""

from __future__ import annotations

DIRECOES: tuple[str, ...] = ("S", "SW", "W", "NW", "N", "NE", "E", "SE")
AZIMUTE_MDEG: dict[str, int] = {d: i * 45_000 for i, d in enumerate(DIRECOES)}
