"""O corpo humano do cânone: as medidas em frações da estatura (Drillis & Contini), o rig pelo modelo em dado e as
massas do corpo (cabeça, tronco, membros e uma esfera em cada junta). A cabeça é estilizada (1/6 em vez de 1/7,5,
para o rosto ler a 54 px), e a altura que ela toma sai do que fica entre o queixo e o quadril, não das pernas: o
tronco e o braço têm ~0,90 do real. Coordenadas: +X = esquerda anatômica, +Y = frente, +Z = altura; px do mundo na
régua do kit."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from ..construtor import AssetBuilder, Parte, ellipse, q, qv
from ..escala import PX_POR_M
from .esqueleto import monta

# o pé tem 0,12 da estatura (o real, 0,152): na câmera de cima o pé comprido aponta para baixo como um bloco, e de
# perfil lê como sapato de palhaço
PESCOCO, BRACO, ANTEBRACO, MAO, TORNOZELO_Z, PE = 0.028, 0.167, 0.131, 0.108, 0.039, 0.12
# o tornozelo fica sob a junta do quadril (a perna desce reta): mais aberto, de frente as canelas passam da largura
# do tronco, e de perfil a câmera a 45° sobe o pé de lá na tela (a 0,080 ele flutuava no meio da canela)
OMBRO_X, QUADRIL_X, TORNOZELO_X = 0.105, 0.050, 0.050
# o tronco é um bloco: a cintura e o quadril quase da largura do peito (com a cintura a 0,075 e o quadril a 0,095,
# as medidas do corpo real, o tronco afinava e abria como uma ampulheta)
PEITO_X, CINTURA_X, QUADRIL_LARG_X, PEITO_Y = 0.090, 0.082, 0.088, 0.060
COXA_DA_PERNA = 0.499
# a perna é um tubo que afina pouco (a canela real afina até 0,021 da estatura: na tela, um palito de 2 px)
R_COXA, R_JOELHO, R_CANELA_BAIXO, R_BRACO, R_COTOVELO, R_PUNHO, R_PESCOCO = (0.045, 0.034, 0.025, 0.027, 0.023, 0.018,
                                                                           0.032)
# as juntas e os membros são formas simples, para a câmera de cima. A esfera de cada junta tem o raio do segmento
# (o cotovelo, o punho, o quadril, o joelho, o tornozelo): maior, vira uma bola no meio do membro. O antebraço e a
# canela começam com o raio da junta. A mão é uma forma curta da largura do punho (os raios x e y sobre o do punho
# e a meia altura sobre o comprimento dela): mais fina, na tela é um risco de 1 px. O pé é baixo (a meia altura do
# calcanhar e a da ponta, sobre a altura do tornozelo). Cada membro sombreia como uma massa só
R_JUNTAS = (1.0, 1.0, 0.95, 1.0, 1.0)
DEPOIS_DA_JUNTA, MAO_FORMA, PE_ALTO = (1.0, 1.0), (0.9, 1.2, 0.38), (0.55, 0.40)
MASSA_DO_MEMBRO: tuple[str, ...] = ("shade_group",)
# o quadril é do tronco: o mesmo grupo de contorno e a mesma massa (à parte, a linha em volta dele lia como sunga)
QUADRIL: tuple[str, tuple[str, ...]] = ("torso", ("shade_group",))
# o ombro: a junta fica OMBRO_CAI abaixo da base do pescoço (o alto do ombro, 3 % da estatura abaixo do queixo), e
# a esfera dela tem R_OMBRO vezes o raio do braço
OMBRO_CAI, R_OMBRO = 0.035, 1.25
# a cintura: o centro e a meia altura da massa, em frações do tronco. O peito é uma cunha, não uma bola: o alto e o
# baixo dela, cada um com a altura no tronco e o raio (a meia profundidade) sobre o fundo do peito, e a meia largura
# de baixo sobre a da cintura. O baixo fica a 0,43 do tronco: mais baixo, a cunha da jaqueta cobre a faixa
CINTURA, PEITO_ALTO, PEITO_BAIXO, PEITO_NA_CINTURA = (0.28, 0.30), (0.78, 0.95), (0.43, 0.80), 1.05
# a cabeça é um ovo: um elipsoide só, não a anatomia de uma cabeça. O humano é uma figura para a câmera de cima, a
# 54 px: o que se mede é o pixel do sprite, e nele o crânio, a face, o queixo e o nariz viravam ressaltos. O centro
# (y, z) e os raios (y, z) em frações da cabeça, no osso dela (0,25 acima do queixo); a meia largura é
# ``cabeca_larg``. Mais alto que fundo, para de perfil não ler deitado
CRANIO = (-0.04, 0.25, 0.38, 0.50)
SIDES = (("l", 1), ("r", -1))
FRONT_VIEWS = ("S", "SW", "W", "E", "SE")
CANVAS, PIVOT, TALL_EXTRA = 96, (48, 60), 16
TALL_PX = 1.72 * 54 / 1.65  # acima de ~1,70 m o canvas cresce para cima
# a abertura do braço no repouso: a 15° (o pixel-engine) a câmera, que achata a altura, mostrava ~21° e as mãos caíam
# longe do corpo; a 6° elas caem junto do quadril
ABRE_BRACO_MDEG = 6_000.0


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
        "queixo_z": queixo, "ombro_cai": OMBRO_CAI * h, "ombro_x": OMBRO_X * h * (0.85 + 0.15 * w),
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


def trapezio(c: dict[str, float], sx: int, folga: float = 0.0, ate: float = 1.0) -> dict[str, Any]:
    """A linha do ombro de um lado: o fuso da base do pescoço à junta do ombro, que fica ``ombro_cai`` abaixo dela.
    A ponta tem um nada menos que o raio da esfera do ombro (é a esfera que dá o canto, sem degrau). ``folga`` é a
    da roupa que veste por cima, e ``ate`` a fração da linha que ela cobre (a alça para antes do ombro)."""
    t, rp = c["tronco"], c["r_pescoco"]
    de, junta = (sx * 0.3 * rp, 0.0, t - 0.2 * rp), (sx * c["ombro_x"], 0.0, t - c["ombro_cai"])
    ponta = [a + ate * (b - a) for a, b in zip(de, junta, strict=True)]
    r0, r1 = 0.9 * rp, 0.96 * R_OMBRO * c["r_braco"]
    return {"type": "tapered_polyline", "points_q8": [qv(*de), qv(*ponta)],
            "radii_q8": [q(r0 + folga), q(r0 + ate * (r1 - r0) + folga)]}


def _raios_do_peito(c: dict[str, float], folga: float) -> tuple[float, float]:
    return c["peito_y"] * PEITO_ALTO[1] + folga, c["peito_y"] * PEITO_BAIXO[1] + folga


def peito(c: dict[str, float], folga: float = 0.0, larg: tuple[float, float] = (1.0, 0.0)) -> dict[str, Any]:
    """O peito em cunha: um fuso de cada lado e um no meio, do alto do peito à cintura, fechados em cima e embaixo.
    A seção é um estádio (a frente e as costas chapadas) e os lados e a frente são retas: não há a bola que lia
    como busto. ``folga`` é a da roupa na profundidade, e ``larg`` (vezes, mais) a dela na largura."""
    t = c["tronco"]
    ra, rb = _raios_do_peito(c, folga)
    xa = max(0.2, c["peito_x"] * larg[0] + larg[1] - ra)
    xb = max(0.2, c["cintura_x"] * PEITO_NA_CINTURA * larg[0] + larg[1] - rb)
    za, zb = PEITO_ALTO[0] * t, PEITO_BAIXO[0] * t
    # a volta pelos dois lados e, no fim, o meio de baixo para cima: sem ele fica um sulco entre os lados, e a sombra
    # da cabeça cai dentro dele
    volta = ((xb, zb, rb), (xa, za, ra), (-xa, za, ra), (-xb, zb, rb), (xb, zb, rb), (0.0, zb, rb), (0.0, za, ra))
    return {"type": "tapered_polyline", "points_q8": [qv(x, 0, z) for x, z, _ in volta],
            "radii_q8": [q(r) for _, _, r in volta]}


def frente_do_peito(c: dict[str, float], z: float, folga: float = 0.0) -> float:
    """A frente (+y) do peito no meio do corpo, na altura ``z`` (onde a roupa põe a gola); abaixo da cunha, a do
    baixo dela."""
    t = c["tronco"]
    ra, rb = _raios_do_peito(c, folga)
    za, zb = PEITO_ALTO[0] * t, PEITO_BAIXO[0] * t
    if z >= za:
        return math.sqrt(max(0.0, ra * ra - (z - za) ** 2))
    return rb + (ra - rb) * max(0.0, z - zb) / (za - zb)


def cranio(c: dict[str, float]) -> tuple[float, float, float, float, float]:
    """(o centro y, o centro z, o raio x, o raio y, o raio z) do ovo da cabeça em px, no osso dela."""
    cab = c["cabeca"]
    return CRANIO[0] * cab, CRANIO[1] * cab, c["cabeca_larg"] / 2, CRANIO[2] * cab, CRANIO[3] * cab


def frente_da_cabeca(c: dict[str, float], x: float, z: float) -> float:
    """A frente (+y) do ovo da cabeça em (x, z) do osso dela (onde o olho assenta)."""
    cy, cz, rx, ry, rz = cranio(c)
    return cy + ry * math.sqrt(max(0.0, 1 - (x / rx) ** 2 - ((z - cz) / rz) ** 2))


def neck_len(c: dict[str, float]) -> float:
    return c["pescoco"] + 0.25 * c["cabeca"]  # a base do crânio fica um quarto da cabeça acima do queixo


def esqueleto(b: AssetBuilder, c: dict[str, float]) -> None:
    """Os ossos do modelo ``humano`` nas medidas do corpo: os pés sob as juntas do quadril, os braços afastados
    :data:`ABRE_BRACO_MDEG` e os cotovelos dobrados ~12° no repouso."""
    abre = round(math.degrees(math.atan2(c["tornozelo_x"] - c["quadril_x"], c["quadril_z"] - c["tornozelo_z"])) * 1000)
    monta(b, "humano", {**c, "abre_perna_mdeg": float(abre), "abre_braco_mdeg": ABRE_BRACO_MDEG,
                        "dobra_cotovelo_mdeg": 12_000.0})


def _tronco(b: AssetBuilder, c: dict[str, float], pele: str) -> None:
    t = c["tronco"]
    b.part("pelvis_block", pele, ellipse(qv(0, -0.2, 0.9), qv(c["quadril_larg_x"], c["peito_y"] * 0.85,
                                                             0.11 * c["estatura"] * 0.5)),
           Parte(bone="pelvis_tilt", group=QUADRIL[0], tags=QUADRIL[1]))
    massa = Parte(bone="torso", group="torso", tags=("shade_group",))  # o peito e a cintura: uma massa só
    b.part("waist", pele, ellipse(qv(0, 0, CINTURA[0] * t), qv(c["cintura_x"], c["peito_y"] * 0.75, CINTURA[1] * t)),
           massa)
    b.part("chest", pele, peito(c), massa)
    for side, sx in SIDES:  # no grupo do braço e sem linha interna: o ombro lê como uma forma só, do pescoço ao braço
        b.part(f"trap_{side}", pele, trapezio(c, sx),
               Parte(bone="torso", group=f"arm_{side}", tags=("no_inner_outline",)))
    nl = neck_len(c)
    b.part("neck", pele, taper((-0.1, 1.0), -nl, (c["r_pescoco"], c["r_pescoco"] * 0.9)),
           Parte(bone="neck", group="neck"))


def _cabeca(b: AssetBuilder, c: dict[str, float], pele: str) -> None:
    """A cabeça: o ovo (``skull``), uma parte só."""
    cy, cz, rx, ry, rz = cranio(c)
    b.part("skull", pele, ellipse(qv(0, cy, cz), qv(rx, ry, rz)), Parte(bone="head", group="head"))


def _membros(b: AssetBuilder, c: dict[str, float], pele: str, side: str) -> None:
    def em(osso: str, grupo: str) -> Parte:
        return Parte(bone=f"{osso}_{side}", group=f"{grupo}_{side}", tags=MASSA_DO_MEMBRO)

    b.part(f"upper_arm_{side}", pele, taper((0.08, 1.0), c["braco"], (c["r_braco"], c["r_cotovelo"])),
           em("upper_arm", "arm"))
    b.part(f"forearm_{side}", pele, taper((0.08, 1.0), c["antebraco"], (c["r_cotovelo"] * DEPOIS_DA_JUNTA[0],
                                                                       c["r_punho"])), em("forearm", "arm"))
    mx, my, mz = MAO_FORMA
    b.part(f"hand_{side}", pele, ellipse(qv(0, 0.1, -mz * c["mao"]), qv(c["r_punho"] * mx, c["r_punho"] * my,
                                                                         mz * c["mao"])), em("hand", "hand"))
    b.part(f"thigh_{side}", pele, taper((0.06, 1.0), c["coxa"], (c["r_coxa"], c["r_joelho"])), em("thigh", "leg"))
    b.part(f"shin_{side}", pele, taper((0.06, 1.0), c["canela"], (c["r_joelho"] * DEPOIS_DA_JUNTA[1], c["r_canela"])),
           em("shin", "leg"))
    pe, az, rc = c["pe"], c["tornozelo_z"], c["r_canela"]
    b.part(f"foot_{side}", pele, ellipse(qv(0, 0.02 * pe, -0.40 * az), qv(rc * 1.4, 0.30 * pe, PE_ALTO[0] * az + 0.3)),
           em("foot", "foot"))
    b.part(f"toe_{side}", pele, ellipse(qv(0, 0.42 * pe, -0.60 * az), qv(rc * 1.3, 0.28 * pe, PE_ALTO[1] * az + 0.15)),
           em("foot", "foot"))


def _juntas(b: AssetBuilder, c: dict[str, float], junta: str, side: str) -> None:
    for jid, bone, r, grp in ((f"j_shoulder_{side}", f"upper_arm_{side}", c["r_braco"] * R_OMBRO, f"arm_{side}"),
                              (f"j_elbow_{side}", f"forearm_{side}", c["r_cotovelo"] * R_JUNTAS[0], f"arm_{side}"),
                              (f"j_wrist_{side}", f"hand_{side}", c["r_punho"] * R_JUNTAS[1], f"hand_{side}"),
                              (f"j_hip_{side}", f"thigh_{side}", c["r_coxa"] * R_JUNTAS[2], f"leg_{side}"),
                              (f"j_knee_{side}", f"shin_{side}", c["r_joelho"] * R_JUNTAS[3], f"leg_{side}"),
                              (f"j_ankle_{side}", f"foot_{side}", c["r_canela"] * R_JUNTAS[4], f"foot_{side}")):
        b.part(jid, junta, ellipse(qv(0, 0, 0), qv(r, r, r)),
               Parte(bone=bone, group=grp, tags=("joint", *MASSA_DO_MEMBRO)))


def corpo(b: AssetBuilder, c: dict[str, float], pele: str, junta: str) -> None:
    """As massas do corpo em ``pele`` (o tronco numa massa só, sem linha nem sombra entre o peito e a cintura, a
    linha do ombro de cada lado e a cabeça) e uma esfera em cada junta em ``junta``."""
    _tronco(b, c, pele)
    _cabeca(b, c, pele)
    for side, _ in SIDES:
        _membros(b, c, pele, side)
        _juntas(b, c, junta, side)
    b.part("j_neck", junta, ellipse(qv(0, 0, 0), qv(c["r_pescoco"] * 1.1, c["r_pescoco"] * 1.1, c["r_pescoco"] * 1.1)),
           Parte(bone="neck", group="neck", tags=("joint",)))


def regras(d: str) -> list[dict[str, str]]:
    """O peito sobre a cintura sobre o quadril; de frente, a cabeça sobre o pescoço."""
    out = [{"front": "chest", "back": "waist"}, {"front": "waist", "back": "pelvis_block"}]
    return [*out, {"front": "skull", "back": "neck"}] if d in FRONT_VIEWS else out


def landmarks(c: dict[str, float]) -> list[dict[str, Any]]:
    """O alto da cabeça, o queixo, as mãos e os pés (os pontos do jogo e das medidas de pose)."""
    cy, cz, _, ry, rz = cranio(c)
    out = [{"id": "head_top", "bone_id": "head", "point_q8": qv(0, cy, cz + rz)},
           {"id": "chin", "bone_id": "head", "point_q8": qv(0, cy + 0.5 * ry, cz - rz)}]
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
