"""O estilo do jogo: a paleta, os materiais (rampa de tons, tinta de contorno, textura, degrau de sombra) e a luz.

O estilo guarda valores, não interruptores: o contorno por dentro com o sel-out, a limpeza pixel-perfect, as linhas
do sólido varrido, a sombra projetada entre peças e no chão e a limpeza de cor isolada são o jeito da engine.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field

from .base import Id, PosInt, Strict

Indice = Annotated[int, Field(ge=1, le=255, strict=True)]


class PaletteEntry(Strict):
    index: Annotated[int, Field(ge=0, le=255, strict=True)]
    id: Id
    rgba: Annotated[list[Annotated[int, Field(ge=0, le=255, strict=True)]], Field(min_length=4, max_length=4)]


class MaterialTexture(Strict):
    """Sulcos em traço curto a cada ``period_px`` fileiras, desencontrados, de ``length_px`` px; ``density_permille``
    das células têm traço; o sulco desce a luz em ``depth_permille`` e às vezes o pixel acima sobe ``lift_permille``;
    ``jitter_permille`` quebra a fronteira entre os tons. ``grain``: no sólido de revolução, os sulcos deitados em
    volta dele (``across``) ou em pé, ao longo da altura (``along``: o veio da casca)."""

    kind: Literal["dashes"]
    grain: Literal["across", "along"] = "across"
    period_px: Annotated[int, Field(ge=2, le=8, strict=True)]
    length_px: Annotated[list[Annotated[int, Field(ge=1, le=16, strict=True)]], Field(min_length=2, max_length=2)]
    density_permille: Annotated[int, Field(ge=0, le=1000, strict=True)]
    depth_permille: Annotated[int, Field(ge=0, le=1000, strict=True)]
    lift_permille: Annotated[int, Field(ge=0, le=1000, strict=True)]
    jitter_permille: Annotated[int, Field(ge=0, le=500, strict=True)]
    seed: Annotated[int, Field(ge=0, le=65535, strict=True)]


class MaterialDef(Strict):
    """``cast_material``: o degrau de baixo da família (tábua clara → tábua → tábua escura); a peça chapada deste
    material desce a ele na sombra e na face de costas para a luz."""

    id: Id
    ramp: Annotated[list[Indice], Field(min_length=2, max_length=6)]
    outline_index: Indice
    texture: MaterialTexture | None = None
    cast_material: Id | None = None


class ShadingDef(Strict):
    """As faixas de luz e sombra da peça lisa e até onde a sombra projetada entre peças anda na tela (a luz é da
    câmera: ``views.camera.LUZ``)."""

    shadow_band_px: Annotated[int, Field(ge=0, le=4, strict=True)]
    highlight_band_px: Annotated[int, Field(ge=0, le=4, strict=True)]
    highlight_min_area_px: Annotated[int, Field(ge=0, le=4096, strict=True)]
    cast_shadow_px: Annotated[int, Field(ge=1, le=32, strict=True)]


class StyleDoc(Strict):
    id: Id
    revision: PosInt
    palette: Annotated[list[PaletteEntry], Field(min_length=2)]
    materials: list[MaterialDef]
    shading: ShadingDef
    max_opaque_colors: Annotated[int, Field(ge=1, le=255, strict=True)]
