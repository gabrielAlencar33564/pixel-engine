"""A pilha de uma face: quem cobre quem quando as partes se tocam (a camada maior cobre a menor)."""

from __future__ import annotations

from typing import Any

from ..construtor import Vec


class Pilha:
    """A altura de cada parte é ``z - y`` (a altura na tela a 45°: a frente desce); a parte de camada maior cobre a de
    camada menor cuja caixa em x e na altura ela toca, com 1 px de folga."""

    def __init__(self) -> None:
        self.items: list[tuple[str, int, tuple[float, float, float, float]]] = []

    def add(self, pid: str, layer: int, pts: list[Vec]) -> None:
        xs = [p[0] for p in pts]
        zs = [p[2] - p[1] for p in pts]
        self.items.append((pid, layer, (min(xs), max(xs), min(zs), max(zs))))

    def rules(self) -> list[dict[str, Any]]:
        out = []
        for a, la, (ax0, ax1, az0, az1) in self.items:
            for c, lc, (cx0, cx1, cz0, cz1) in self.items:
                if la > lc and ax0 < cx1 + 1.0 and cx0 < ax1 + 1.0 and az0 < cz1 + 1.0 and cz0 < az1 + 1.0:
                    out.append({"front": a, "back": c})
        return out
