"""O estilo como o render o lê: os materiais por id, o lado da sombra na tela e a luz unitária."""

from __future__ import annotations

from dataclasses import dataclass

from ..contracts.estilo import MaterialDef, StyleDoc


@dataclass(frozen=True)
class EstiloRender:
    doc: StyleDoc
    materials: dict[str, MaterialDef]
    sx: int  # o lado da sombra na tela (+x direita, +y baixo): o oposto da luz
    sy: int
    side: int  # −1 com a luz da esquerda, +1 da direita
    light: tuple[float, float, float]  # a luz unitária em (direita, baixo, para a câmera)
    family_up: dict[str, str]  # o degrau de cima da família (o material cujo ``cast_material`` é este)

    def tom_do_meio(self, material: str) -> int:
        r = self.materials[material].ramp
        return r[len(r) // 2]


def estilo_render(style: StyleDoc) -> EstiloRender:
    lx, ly, lz = style.shading.light_dir
    ups: dict[str, list[str]] = {}
    for m in style.materials:
        if m.cast_material is not None:
            ups.setdefault(m.cast_material, []).append(m.id)
    ln = max(1e-9, float(lx * lx + ly * ly + lz * lz) ** 0.5)  # pow, como o render sempre fez (o mesmo float)
    return EstiloRender(style, {m.id: m for m in style.materials},
                        1 if lx < 0 else (-1 if lx > 0 else 0), 1 if ly < 0 else (-1 if ly > 0 else 0),
                        -1 if lx <= 0 else 1, (lx / ln, ly / ln, lz / ln),
                        {k: v[0] for k, v in ups.items() if len(v) == 1})
