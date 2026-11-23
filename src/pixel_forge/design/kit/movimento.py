"""A cadeia do balanço (``sway_*``) e a escolha do elo pela altura."""

from __future__ import annotations

from collections.abc import Sequence

from ..construtor import AssetBuilder, Junta, q, qv

Elo = tuple[str, float, float]


def sway_chain(b: AssetBuilder, parent: str, z0: float, span: float, links: int) -> list[Elo]:
    """A cadeia ``sway_1..links`` presa a ``parent`` a partir da altura ``z0``, cobrindo ``span`` px; devolve
    ``(osso, z_base, z_topo)`` de cada elo (as alturas absolutas), para as peças escolherem o osso pelo trecho."""
    seg = span / links
    junta = Junta("y", q(seg), (-20_000, 20_000))
    b.bone("sway_1", parent, qv(0, 0, z0), junta)
    for i in range(2, links + 1):
        b.bone(f"sway_{i}", f"sway_{i - 1}", qv(0, 0, seg), junta)
    return [(f"sway_{i + 1}", z0 + i * seg, z0 + (i + 1) * seg) for i in range(links)]


def bone_for(chain: Sequence[Elo], z: float) -> tuple[str, float]:
    """O osso do trecho que contém a altura ``z`` e o z local nele."""
    for bone, z_lo, z_hi in chain:
        if z < z_hi:
            return bone, z - z_lo
    bone, z_lo, _ = chain[-1]
    return bone, z - z_lo
