"""Os tipos comuns dos documentos: o modelo estrito e imutável, ids e vetores inteiros."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

COORD_LIMIT = 16_777_216

Id = Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9_]{0,63}$")]
Coord = Annotated[int, Field(ge=-COORD_LIMIT, le=COORD_LIMIT, strict=True)]
Vec3 = Annotated[list[Coord], Field(min_length=3, max_length=3)]
Vec2 = Annotated[list[Coord], Field(min_length=2, max_length=2)]
PosInt = Annotated[int, Field(ge=1, strict=True)]
NonNegInt = Annotated[int, Field(ge=0, strict=True)]
Mdeg = Annotated[int, Field(ge=-360_000, le=360_000, strict=True)]
Direcao = Literal["S", "SW", "W", "NW", "N", "NE", "E", "SE"]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True, regex_engine="python-re")
