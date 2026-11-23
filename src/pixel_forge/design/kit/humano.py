"""O corpo humano do cânone: as medidas em frações da estatura (Drillis & Contini; só a cabeça é estilizada, 1/6 em
vez de 1/7,5, para o rosto ler a 54 px), o rig pelo modelo em dado e as massas do corpo (cabeça, tronco, membros e uma
esfera em cada junta). Coordenadas: +X = esquerda anatômica, +Y = frente, +Z = altura; px do mundo na régua do kit."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from ..construtor import AssetBuilder, Parte, ellipse, q, qv
from ..escala import PX_POR_M
from .esqueleto import monta

PESCOCO, BRACO, ANTEBRACO, MAO, TORNOZELO_Z, PE = 0.028, 0.186, 0.146, 0.108, 0.039, 0.152
OMBRO_X, QUADRIL_X, TORNOZELO_X = 0.105, 0.050, 0.080
PEITO_X, CINTURA_X, QUADRIL_LARG_X, PEITO_Y = 0.090, 0.075, 0.095, 0.060
COXA_DA_PERNA = 0.499
R_COXA, R_JOELHO, R_CANELA_BAIXO, R_BRACO, R_COTOVELO, R_PUNHO, R_PESCOCO = (0.047, 0.034, 0.021, 0.027, 0.023, 0.018,
                                                                           0.024)
SIDES = (("l", 1), ("r", -1))
FRONT_VIEWS = ("S", "SW", "W", "E", "SE")
CANVAS, PIVOT, TALL_EXTRA = 96, (48, 60), 16
TALL_PX = 1.72 * 54 / 1.65  # acima de ~1,70 m o canvas cresce para cima


@dataclass(frozen=True)
class Corpo:
    """Uma pessoa no cânone: a estatura, as cabeças, a largura do tronco, a grossura dos segmentos e a altura da junta
    do quadril em fração da estatura."""

    estatura_m: float = 1.65
    cabecas: float = 6.0
    largura: float = 1.0
    espessura: float = 1.0
    quadril_z: float = 0.530


def medidas(c: Corpo) -> dict[str, float]:
    """As medidas em px do mundo; alturas do chão, larguras como meia distância do centro."""
    h = c.estatura_m * PX_POR_M
    cabeca = h / c.cabecas
    queixo, quadril_z, tornozelo_z = h - cabeca, c.quadril_z * h, TORNOZELO_Z * h
    perna, e, w = quadril_z - tornozelo_z, c.espessura, c.largura
    return {
        "estatura": h, "cabeca": cabeca, "cabeca_larg": 0.70 * cabeca, "cabeca_fundo": 0.82 * cabeca,
        "queixo_z": queixo, "ombro_z": queixo - PESCOCO * h, "ombro_x": OMBRO_X * h * (0.85 + 0.15 * w),
        "quadril_z": quadril_z, "quadril_x": QUADRIL_X * h * (0.85 + 0.15 * w), "tornozelo_z": tornozelo_z,
        "tronco": queixo - PESCOCO * h - quadril_z, "pescoco": PESCOCO * h, "braco": BRACO * h,
        "antebraco": ANTEBRACO * h, "mao": MAO * h, "coxa": perna * COXA_DA_PERNA,
        "canela": perna * (1 - COXA_DA_PERNA), "pe": PE * h, "peito_x": PEITO_X * h * w, "peito_y": PEITO_Y * h * w,
        "cintura_x": CINTURA_X * h * w, "quadril_larg_x": QUADRIL_LARG_X * h * w,
        "tornozelo_x": TORNOZELO_X * h * (0.85 + 0.15 * w), "r_coxa": R_COXA * h * e, "r_joelho": R_JOELHO * h * e,
        "r_canela": R_CANELA_BAIXO * h * e, "r_braco": R_BRACO * h * e, "r_cotovelo": R_COTOVELO * h * e,
        "r_punho": R_PUNHO * h * e, "r_pescoco": R_PESCOCO * h * e,
    }


def taper(span: tuple[float, float], length: float, raios: tuple[float, float]) -> dict[str, Any]:
    """O segmento em fuso ao longo de −z do osso, de ``span[0]`` a ``span[1]`` (frações do comprimento)."""
    return {"type": "tapered_polyline", "points_q8": [qv(0, 0, -span[0] * length), qv(0, 0, -span[1] * length)],
            "radii_q8": [max(32, q(raios[0])), max(32, q(raios[1]))]}


def neck_len(c: dict[str, float]) -> float:
    return c["pescoco"] + 0.25 * c["cabeca"]  # a base do crânio fica um quarto da cabeça acima do queixo


def esqueleto(b: AssetBuilder, c: dict[str, float]) -> None:
    """Os ossos do modelo ``humano`` nas medidas do corpo: os pés na largura do quadril, os braços afastados ~15° e os
    cotovelos dobrados ~12° no repouso."""
    abre = round(math.degrees(math.atan2(c["tornozelo_x"] - c["quadril_x"], c["quadril_z"] - c["tornozelo_z"])) * 1000)
    monta(b, "humano", {**c, "abre_perna_mdeg": float(abre), "abre_braco_mdeg": 15_000.0,
                        "dobra_cotovelo_mdeg": 12_000.0})


def _tronco(b: AssetBuilder, c: dict[str, float], pele: str) -> None:
    cab, t = c["cabeca"], c["tronco"]
    b.part("pelvis_block", pele, ellipse(qv(0, -0.2, 0.9), qv(c["quadril_larg_x"], c["peito_y"] * 0.85,
                                                             0.11 * c["estatura"] * 0.5)),
           Parte(bone="pelvis_tilt", group="pelvis"))
    b.part("waist", pele, ellipse(qv(0, 0, 0.30 * t), qv(c["cintura_x"], c["peito_y"] * 0.75, 0.16 * t)),
           Parte(bone="torso", group="waist"))
    b.part("chest", pele, ellipse(qv(0, 0.1, 0.70 * t), qv(c["peito_x"], c["peito_y"], 0.32 * t)),
           Parte(bone="torso", group="chest"))
    nl = neck_len(c)
    b.part("neck", pele, taper((-0.1, 1.0), -nl, (c["r_pescoco"], c["r_pescoco"] * 0.9)),
           Parte(bone="neck", group="neck"))
    b.part("skull", pele, ellipse(qv(0, -0.06 * cab, 0.43 * cab), qv(c["cabeca_larg"] / 2, 0.41 * cab, 0.33 * cab)),
           Parte(bone="head", group="head"))
    b.part("jaw", pele, ellipse(qv(0, 0.08 * cab, 0.02 * cab), qv(0.26 * cab, 0.30 * cab, 0.25 * cab)),
           Parte(bone="head", group="head"))
    b.part("chin", pele, ellipse(qv(0, 0.27 * cab, -0.15 * cab), qv(0.13 * cab, 0.10 * cab, 0.10 * cab)),
           Parte(bone="head", group="head"))


def _membros(b: AssetBuilder, c: dict[str, float], pele: str, side: str) -> None:
    b.part(f"upper_arm_{side}", pele, taper((0.08, 1.0), c["braco"], (c["r_braco"], c["r_cotovelo"])),
           Parte(bone=f"upper_arm_{side}", group=f"arm_{side}"))
    b.part(f"forearm_{side}", pele, taper((0.08, 1.0), c["antebraco"], (c["r_cotovelo"] * 0.95, c["r_punho"])),
           Parte(bone=f"forearm_{side}", group=f"arm_{side}"))
    b.part(f"hand_{side}", pele, ellipse(qv(0, 0.1, -0.45 * c["mao"]), qv(c["r_punho"] * 0.6, c["r_punho"] * 1.5,
                                                                           0.45 * c["mao"])),
           Parte(bone=f"hand_{side}", group=f"hand_{side}"))
    b.part(f"thigh_{side}", pele, taper((0.06, 1.0), c["coxa"], (c["r_coxa"], c["r_joelho"])),
           Parte(bone=f"thigh_{side}", group=f"leg_{side}"))
    b.part(f"shin_{side}", pele, taper((0.06, 1.0), c["canela"], (c["r_joelho"] * 0.92, c["r_canela"])),
           Parte(bone=f"shin_{side}", group=f"leg_{side}"))
    pe, az, rc = c["pe"], c["tornozelo_z"], c["r_canela"]
    b.part(f"foot_{side}", pele, ellipse(qv(0, 0.02 * pe, -0.40 * az), qv(rc * 1.4, 0.30 * pe, 0.72 * az + 0.3)),
           Parte(bone=f"foot_{side}", group=f"foot_{side}"))
    b.part(f"toe_{side}", pele, ellipse(qv(0, 0.42 * pe, -0.60 * az), qv(rc * 1.3, 0.28 * pe, 0.45 * az + 0.15)),
           Parte(bone=f"foot_{side}", group=f"foot_{side}"))


def _juntas(b: AssetBuilder, c: dict[str, float], junta: str, side: str) -> None:
    for jid, bone, r, grp in ((f"j_shoulder_{side}", f"upper_arm_{side}", c["r_braco"] * 1.25, f"arm_{side}"),
                              (f"j_elbow_{side}", f"forearm_{side}", c["r_cotovelo"] * 1.15, f"arm_{side}"),
                              (f"j_wrist_{side}", f"hand_{side}", c["r_punho"] * 1.0, f"hand_{side}"),
                              (f"j_hip_{side}", f"thigh_{side}", c["r_coxa"] * 0.95, f"leg_{side}"),
                              (f"j_knee_{side}", f"shin_{side}", c["r_joelho"] * 1.1, f"leg_{side}"),
                              (f"j_ankle_{side}", f"foot_{side}", c["r_canela"] * 1.1, f"foot_{side}")):
        b.part(jid, junta, ellipse(qv(0, 0, 0), qv(r, r, r)), Parte(bone=bone, group=grp, tags=("joint",)))


def corpo(b: AssetBuilder, c: dict[str, float], pele: str, junta: str) -> None:
    """A sombra de contato, as massas do corpo em ``pele`` e uma esfera em cada junta em ``junta``."""
    b.part("ground_shadow", "sombra", ellipse(qv(0, 0.3, 0), qv(c["quadril_larg_x"] * 1.1, 3.6, 0.3)),
           Parte(tags=("ground_shadow",), priority=-100))
    _tronco(b, c, pele)
    for side, _ in SIDES:
        _membros(b, c, pele, side)
        _juntas(b, c, junta, side)
    b.part("j_neck", junta, ellipse(qv(0, 0, 0), qv(c["r_pescoco"] * 1.1, c["r_pescoco"] * 1.1, c["r_pescoco"] * 1.1)),
           Parte(bone="neck", group="neck", tags=("joint",)))


def regras(d: str) -> list[dict[str, str]]:
    """O peito sobre a cintura sobre o quadril; de frente, o queixo e a mandíbula sobre o pescoço; de costas, o crânio
    sobre a mandíbula e o queixo."""
    out = [{"front": "chest", "back": "waist"}, {"front": "waist", "back": "pelvis_block"}]
    if d in FRONT_VIEWS:
        return [*out, {"front": "chin", "back": "neck"}, {"front": "jaw", "back": "neck"}]
    return [*out, {"front": "skull", "back": "jaw"}, {"front": "skull", "back": "chin"}]


def landmarks(c: dict[str, float]) -> list[dict[str, Any]]:
    """O alto da cabeça, o queixo, as mãos e os pés (os pontos do jogo e das medidas de pose)."""
    cab = c["cabeca"]
    out = [{"id": "head_top", "bone_id": "head", "point_q8": qv(0, -0.06 * cab, 0.75 * cab)},
           {"id": "chin", "bone_id": "head", "point_q8": qv(0, 0.30 * cab, -0.20 * cab)}]
    for side, _ in SIDES:
        out += [{"id": f"hand_{side}", "bone_id": f"hand_{side}", "point_q8": qv(0, 0, -0.45 * c["mao"])},
                {"id": f"foot_{side}", "bone_id": f"foot_{side}", "point_q8": qv(0, 0, 0)}]
    return out


def canvas_de(estatura_px: float) -> dict[str, Any]:
    """Até ~1,70 m, 96 × 96 com o pivô em (48, 60); acima, 16 px a mais em cima, com o pivô descendo junto."""
    if estatura_px <= TALL_PX:
        return {"width": CANVAS, "height": CANVAS, "pivot_px": list(PIVOT)}
    return {"width": CANVAS, "height": CANVAS + TALL_EXTRA, "pivot_px": [PIVOT[0], PIVOT[1] + TALL_EXTRA]}


def motion_params(c: dict[str, float]) -> dict[str, int]:
    """Os parâmetros que as receitas leem, na escala do corpo (o adulto padrão tem ``scale_pm`` 1000)."""
    s = c["estatura"] / 54.0
    return {"idle_bob_q8": q(0.5 * s), "hip_yaw_mdeg": 6000, "scale_pm": round(1000 * s)}
