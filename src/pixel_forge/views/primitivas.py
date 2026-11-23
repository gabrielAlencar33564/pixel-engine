"""As primitivas 2D projetadas (q8 de tela), a superfície de profundidade de cada uma, o comando de desenho e a cena
2D que o projetor entrega ao render."""

from __future__ import annotations

from dataclasses import dataclass

Ponto = tuple[int, int]
Ponto3 = tuple[int, int, int]


@dataclass(frozen=True)
class EllipsePrim:
    cu: int
    cv: int
    hu: int
    hv: int


@dataclass(frozen=True)
class CapsulePrim:
    points: tuple[Ponto, ...]
    radius: int


@dataclass(frozen=True)
class TaperedPrim:
    points: tuple[Ponto, ...]
    radii: tuple[int, ...]


@dataclass(frozen=True)
class PolygonPrim:
    points: tuple[Ponto, ...]


@dataclass(frozen=True)
class StipplePrim:
    """O polígono pontilhado, com a origem projetada (``ou``, ``ov``) de onde as células contam."""

    points: tuple[Ponto, ...]
    density: int
    seed: int
    cell: int
    ou: int
    ov: int


@dataclass(frozen=True)
class FanPrim:
    """Polígono preenchido como a união dos triângulos (p0, pi, pi+1): robusto às dobras da perspectiva."""

    points: tuple[Ponto, ...]


@dataclass(frozen=True)
class RevolutionPrim:
    """Por estação, de baixo para cima, (u, v, profundidade, r, z) em px; ``sd`` e ``ce`` = quanto a profundidade
    aparece na tela e quanto ela avança para a câmera."""

    stations: tuple[tuple[float, float, float, float, float], ...]
    sd: float
    ce: float

    @property
    def points(self) -> tuple[Ponto, ...]:
        return tuple((round(s[0] * 256), round(s[1] * 256)) for s in self.stations)


Prim = EllipsePrim | CapsulePrim | TaperedPrim | PolygonPrim | StipplePrim | FanPrim | RevolutionPrim


@dataclass(frozen=True)
class SupPlana:
    d: int


@dataclass(frozen=True)
class SupElipsoide:
    """Elipsoide de centro projetado (cu, cv) e profundidade dc; ``inv`` = a inversa simétrica da matriz de forma 3×3
    nos eixos de câmera (a11, a12, a13, a22, a23, a33)."""

    cu: int
    cv: int
    dc: int
    inv: tuple[float, float, float, float, float, float]


@dataclass(frozen=True)
class SupTubo:
    """O membro: os pontos (u, v, d) e os raios de tela; a profundidade é o eixo interpolado no ponto mais perto mais
    √(r² − perp²), um tubo de seção circular."""

    pts: tuple[Ponto3, ...]
    radii: tuple[int, ...]


@dataclass(frozen=True)
class SupLeque:
    pts: tuple[Ponto3, ...]


Superficie = SupPlana | SupElipsoide | SupTubo | SupLeque


@dataclass(frozen=True)
class DrawCommand:
    part_id: str
    material: str
    group: str
    tags: tuple[str, ...]
    depth: int
    prim: Prim
    surface: Superficie
    facing: Ponto3 | None = None  # a normal da face chapada (×1000, eixos de câmera), virada para a câmera


@dataclass(frozen=True)
class Scene2D:
    direction: str
    azimuth_mdeg: int
    commands: list[DrawCommand]
    pivot_q8: Ponto
    depth_bias_q8: dict[str, int]
    front_back: tuple[tuple[str, str], ...]
    landmarks: dict[str, Ponto3]  # os pontos do jogo, em q8 de tela (u, v) e a profundidade
