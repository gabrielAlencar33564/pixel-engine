"""O clipe: as chaves (o desvio de cada osso sobre o repouso, a trajetória da raiz, a suavização e as marcas), os
instantes amostrados (um quadro cada) e os contatos (o pé preso a um alvo no mundo, resolvido por IK no instante)."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field

from .base import Id, Mdeg, NonNegInt, PosInt, Strict, Vec3


class ChaveDoOsso(Strict):
    translation_q8: Vec3
    rotation_mdeg: Mdeg


class Chave(Strict):
    time_ms: NonNegInt
    easing: Literal["linear", "smoothstep", "hold"]
    root_q8: Vec3
    bones: dict[Id, ChaveDoOsso]
    markers: list[Id] = Field(default_factory=list)


class Contato(Strict):
    bone_id: Id
    start_ms: NonNegInt
    end_ms: NonNegInt
    target_q8: Vec3


class Clipe(Strict):
    id: Id
    duration_ms: PosInt
    loop: bool
    keyframes: Annotated[list[Chave], Field(min_length=1)]
    sample_times_ms: Annotated[list[NonNegInt], Field(min_length=1)]
    contacts: list[Contato] = Field(default_factory=list)
