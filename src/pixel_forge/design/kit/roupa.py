"""A roupa do humano: peças que vestem qualquer corpo do cânone, lendo as medidas dele (nenhum px solto: a mesma
calça veste o adulto, a criança e o forte). A roupa envolve o corpo: as peças do corpo ficam dentro, cobertas, e os
pontos do corpo continuam valendo. Cada peça diz às vistas o que cobre e o que fica por cima (:class:`Vista`).

Opções inteiras: ``largura_pct`` (100 = justo), ``manga`` (0 sem, 1 cotovelo, 2 meio do antebraço, 3 punho),
``barra`` (1 prende a canela), ``comprimento_pct`` (a saia: 100 = até o tornozelo).
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from ..construtor import AssetBuilder, Junta, Parte, ellipse, polyline, q, qv
from ..escala import PX_POR_M
from .humano import PE_ALTO, R_OMBRO, SIDES, cranio, frente_da_cabeca, frente_do_peito, peito, taper, trapezio

Regra = dict[str, str]
# a jaqueta sobre o tronco: a folga do peito dela na profundidade e na largura (vezes, mais), o centro e a meia
# altura da cintura dela, em frações do tronco, e onde a manga começa no braço (na junta do ombro: a ombreira fecha
# o alto, sem a manga fazer um gomo acima dela)
JAQUETA_FOLGA, JAQUETA_LARGA, JAQUETA_CINTURA, MANGA_DE = 0.45, (1.1, 0.4), (0.26, 0.30), 0.0
ALCA = 0.7  # sem manga, a ombreira cobre esta fração da linha do ombro
# o olho: a altura no osso da cabeça (0,38 da cabeça: na câmera de cima cai no meio do ovo na tela; a meia altura,
# como no corpo real, ele colava no queixo), a distância do meio sobre a meia largura da cabeça e os raios em px
# (1 px de largura na tela)
OLHO_Z, OLHO_X, OLHO_R = 0.38, 0.44, (0.5, 0.5, 0.9)
# o cabelo e o lenço são cascas sobre o ovo da cabeça: o centro recua e sobe (frações da cabeça) e os raios mudam
# (px), e o rosto sai pela frente de baixo. Sem linha de contorno na testa (e, no cabelo, sem a sombra: lia como aba)
Casca = tuple[float, float, tuple[float, float, float]]
CABELO: Casca = (-0.07, 0.12, (0.05, 0.2, -0.5))
# a mecha do cabelo em cada têmpora: o lado (sobre a meia largura da cabeça), o centro (y, z) a partir do centro do
# ovo e os raios, em frações da cabeça. Sem ela a casca acaba numa linha reta acima da testa, e o cabelo lê como
# gorro
MECHA = (0.92, 0.08, 0.13, (0.10, 0.15, 0.20))
LENCO: Casca = (-0.06, 0.06, (0.45, 0.4, -0.1))
# a copa e a aba do chapéu: o centro (y, z) a partir do centro do ovo, em frações da cabeça; e a altura do coque.
# O chapéu assenta um pouco para trás: centrado, na câmera de cima a aba cobre os olhos em qualquer largura
CHAPEU, COQUE = ((-0.06, 0.47), (-0.10, 0.31)), 0.57
SEM_LINHA = ("garment", "no_inner_outline")
# a espada: quantos graus a lâmina desce abaixo da linha da mão, a lâmina, o cabo e a guarda em metros, e os raios
# (px) da lâmina no pé e na ponta e o do cabo e da guarda. Com o contorno, a lâmina tem 2 a 3 px na tela
ESPADA_DESCE, ESPADA_M, ESPADA_R = 35.0, (0.70, 0.12, 0.17), (0.75, 0.35, 0.5)
ESPADA_TAGS = ("garment", "no_inner_outline", "no_cast")
MARCAS_DO_OLHO = (*SEM_LINHA, "no_outline", "eye")  # nem o contorno de fora: o olho é o pixel dele, e a limpeza o poupa


def regra(front: str, back: str) -> Regra:
    return {"front": front, "back": back}


@dataclass
class Vista:
    """O que a peça pede às vistas: as regras de ordem (todas, de frente, de costas), as peças escondidas de costas, as
    peças do corpo cobertas (somem em todas as vistas) e as de perfil (o olho do lado de lá)."""

    rules: list[Regra] = field(default_factory=list)
    front_rules: list[Regra] = field(default_factory=list)
    back_rules: list[Regra] = field(default_factory=list)
    hide_back: list[str] = field(default_factory=list)
    cobre: list[str] = field(default_factory=list)
    hide_w: list[str] = field(default_factory=list)
    hide_e: list[str] = field(default_factory=list)

    def merge(self, o: Vista) -> None:
        for nome in ("rules", "front_rules", "back_rules", "hide_back", "cobre", "hide_w", "hide_e"):
            getattr(self, nome).extend(getattr(o, nome))


@dataclass(frozen=True)
class Veste:
    """O que a peça de roupa recebe: o construtor, as medidas do corpo, o material, o segundo material e as opções."""

    b: AssetBuilder
    c: dict[str, float]
    mat: str
    mat2: str
    op: dict[str, int]

    def part(self, pid: str, geom: dict[str, Any], como: tuple[str, str], mat: str = "") -> None:
        """A parte no osso ``como[0]``, no grupo ``como[1]``, com a marca de roupa."""
        self.b.part(pid, mat or self.mat, geom, Parte(bone=como[0], group=como[1], tags=("garment",)))

    def pct(self, chave: str, padrao: int) -> float:
        return self.op.get(chave, padrao) / 100


def jaqueta(v: Veste) -> Vista:
    """A blusa ou jaqueta cruzada, a aba esquerda sobre a direita (a gola em V): o peito em cunha e a cintura numa
    massa só, a ombreira (a linha do ombro, do pescoço à manga, no grupo da manga e sem linha interna) e as mangas;
    sem manga, a ombreira é a alça, que para antes do ombro nu."""
    c, t, lw = v.c, v.c["tronco"], v.pct("largura_pct", 140)
    massa = Parte(bone="torso", group="jacket", tags=("garment", "shade_group"))
    v.b.part("jacket_chest", v.mat, peito(c, JAQUETA_FOLGA, JAQUETA_LARGA), massa)
    cintura = qv(c["cintura_x"] * 1.15 + 0.45, c["peito_y"] * 0.85 + 0.45, JAQUETA_CINTURA[1] * t)
    v.b.part("jacket_waist", v.mat, ellipse(qv(0, 0, JAQUETA_CINTURA[0] * t), cintura), massa)
    for pid, (x0, x1, z1) in (("lapel_l", (-0.9, 1.8, 0.30)), ("lapel_r", (0.9, 0.0, 0.55))):
        pts = [qv(x0, frente_do_peito(c, 0.98 * t, JAQUETA_FOLGA) + 0.1, 0.98 * t),
               qv(x1, frente_do_peito(c, z1 * t, JAQUETA_FOLGA) + 0.25, z1 * t)]
        v.part(pid, polyline(pts, 1), ("torso", "jacket"), v.mat2)
    manga = v.op.get("manga", 2)
    cobre, rules = ["chest", "waist"], []
    for side, sx in SIDES:
        boca = c["r_cotovelo"] * (0.9 + 0.45 * lw) + 0.3
        ate, grupo = (1.0, f"sleeve_{side}") if manga >= 1 else (ALCA, "jacket")
        v.b.part(f"jacket_yoke_{side}", v.mat, trapezio(c, sx, 0.3, ate),
                 Parte(bone="torso", group=grupo, tags=("garment", "no_inner_outline")))
        if manga >= 1:
            v.part(f"sleeve_{side}", taper((MANGA_DE, 1.04), c["braco"], (c["r_braco"] * R_OMBRO + 0.3, boca)),
                   (f"upper_arm_{side}", f"sleeve_{side}"))
            cobre += [f"upper_arm_{side}", f"j_shoulder_{side}", f"trap_{side}"]
        if manga >= 2:
            v.part(f"cuff_{side}", taper((0.0, 0.5 if manga == 2 else 0.92), c["antebraco"],
                                         (boca, c["r_punho"] * (0.9 + 0.6 * lw) + 0.3)),
                   (f"forearm_{side}", f"sleeve_{side}"))
            cobre.append(f"j_elbow_{side}")
            rules.append(regra(f"cuff_{side}", f"forearm_{side}"))
        if manga == 3:
            cobre.append(f"forearm_{side}")
    return Vista(cobre=cobre, rules=rules, front_rules=[regra("lapel_l", "lapel_r")])


def faixa(v: Veste) -> Vista:
    """A faixa na cintura, com o nó na frente do lado esquerdo e a ponta solta pendendo."""
    c, t = v.c, v.c["tronco"]
    rx, ry = c["cintura_x"] * 1.2 + 0.6, c["peito_y"] * 0.9 + 0.6
    v.part("sash", ellipse(qv(0, 0, 0.06 * t), qv(rx, ry, 0.07 * t + 0.4)), ("torso", "sash"))
    kx, ky = 0.45 * rx, ry * math.sqrt(1 - 0.45 ** 2) + 0.2
    v.part("sash_knot", ellipse(qv(kx, ky, 0.06 * t), qv(0.9, 0.6, 0.8)), ("torso", "sash"))
    v.part("sash_tail", polyline([qv(kx + 0.3, ky + 0.3, 0.02 * t), qv(kx + 0.9, ky + 0.6, -0.18 * t - 2.2)], 1),
           ("torso", "sash"), v.mat2)
    return Vista(rules=[regra("sash", "jacket_waist"), regra("sash", "pants_seat"), regra("sash", "skirt_waist")],
                 front_rules=[regra("sash_knot", "sash")])


def calca(v: Veste) -> Vista:
    """A calça em dois tubos que seguem a coxa e a canela; ``largura_pct`` abre a barra, ``barra`` 1 prende a canela
    com uma faixa no segundo material."""
    c, lw = v.c, v.pct("largura_pct", 150)
    v.part("pants_seat", ellipse(qv(0, -0.2, 1.4), qv(c["quadril_larg_x"] * 1.1 + 0.5, c["peito_y"] * 0.95 + 0.5,
                                                     0.06 * c["estatura"] + 0.6)), ("pelvis_tilt", "pants"))
    r_knee = c["r_joelho"] * (0.9 + 0.3 * lw) + 0.4
    for side, _ in SIDES:
        v.part(f"pants_thigh_{side}", taper((-0.08, 1.04), c["coxa"], (c["r_coxa"] * 1.15 + 0.4, r_knee)),
               (f"thigh_{side}", f"pants_{side}"))
        if v.op.get("barra", 0) == 1:
            v.part(f"pants_shin_{side}", taper((0.0, 0.78), c["canela"], (r_knee, c["r_canela"] * (0.8 + 0.5 * lw)
                                                                           + 0.3)), (f"shin_{side}", f"pants_{side}"))
            v.part(f"wrap_{side}", taper((0.72, 1.0), c["canela"], (c["r_canela"] * 1.25 + 0.35,
                                                                    c["r_canela"] * 1.15 + 0.3)),
                   (f"shin_{side}", f"pants_{side}"), v.mat2)
        else:
            v.part(f"pants_shin_{side}", taper((0.0, 1.06), c["canela"], (r_knee, c["r_canela"] * (1.0 + 0.9 * lw)
                                                                           + 0.4)), (f"shin_{side}", f"pants_{side}"))
    cobre = ["pelvis_block"] + [f"{p}_{s}" for s, _ in SIDES for p in ("thigh", "j_hip", "j_knee", "shin")]
    return Vista(cobre=cobre, rules=[regra("jacket_waist", "pants_seat")])


def _casca(v: Veste, pid: str, forma: Casca, marcas: tuple[str, ...]) -> float:
    """A casca ``pid`` sobre o ovo da cabeça, no grupo dela; devolve o fundo (−y) dela, onde fica a nuca."""
    cab = v.c["cabeca"]
    cy, cz, rx, ry, rz = cranio(v.c)
    y, (ax, ay, az) = cy + forma[0] * cab, forma[2]
    v.b.part(pid, v.mat, ellipse(qv(0, y, cz + forma[1] * cab), qv(rx + ax, ry + ay, rz + az)),
             Parte(bone="head", group={"hair_cap": "hair"}.get(pid, pid), tags=marcas))
    return y - ry - ay


def olhos(v: Veste) -> Vista:
    """Dois olhos de um pixel na frente da cabeça, sem contorno em volta (num rosto de 7 px o contorno de cada olho
    virava uma máscara, e de perfil o contorno do olho saía da borda da cabeça, como um ressalto). Não são detalhe:
    o chapéu, o cabelo e o lenço os cobrem pela profundidade. Somem de costas, e de perfil o do lado de lá some."""
    z, rx = OLHO_Z * v.c["cabeca"], cranio(v.c)[2]
    for side, sx in SIDES:
        x = sx * OLHO_X * rx
        v.b.part(f"eye_{side}", v.mat, ellipse(qv(x, frente_da_cabeca(v.c, x, z), z), qv(*OLHO_R)),
                 Parte(bone="head", group="eyes", tags=MARCAS_DO_OLHO))
    return Vista(hide_back=["eye_l", "eye_r"], hide_w=["eye_r"], hide_e=["eye_l"],
                 front_rules=[regra(f"eye_{s}", "skull") for s in ("l", "r")])


def cabelo_preso(v: Veste) -> Vista:
    """O cabelo puxado para trás: a casca rente à cabeça, que cobre o alto, os lados e a nuca e deixa a testa e o
    rosto, uma mecha em cada têmpora (emolduram o rosto) e o coque no alto."""
    cab = v.c["cabeca"]
    cy, cz, rx, _, _ = cranio(v.c)
    cabelo = Parte(bone="head", group="hair", tags=(*SEM_LINHA, "no_cast"))
    _casca(v, "hair_cap", CABELO, cabelo.tags)
    lado, my, mz, (rmx, rmy, rmz) = MECHA
    for side, sx in SIDES:
        v.b.part(f"hair_side_{side}", v.mat, ellipse(qv(sx * lado * rx, cy + my * cab, cz + mz * cab),
                                                     qv(rmx * cab, rmy * cab, rmz * cab)), cabelo)
    v.part("topknot", ellipse(qv(0, cy - 0.16 * cab, cz + COQUE * cab), qv(0.14 * cab, 0.16 * cab, 0.13 * cab)),
           ("head", "hair"))
    return Vista(rules=[regra("topknot", "hair_cap")])


def chapeu(v: Veste) -> Vista:
    """O chapéu mole de aba larga: a copa baixa sobre a cabeça e a aba em disco, assentados um pouco para trás;
    ``largura_pct`` é a aba sobre a largura da cabeça."""
    cab, aba = v.c["cabeca"], v.pct("largura_pct", 180)
    cy, cz, rx, ry, _ = cranio(v.c)
    (copa_y, copa_z), (aba_y, aba_z) = CHAPEU
    v.part("hat_crown", ellipse(qv(0, cy + copa_y * cab, cz + copa_z * cab), qv(rx + 0.35, ry + 0.3, 0.24 * cab)),
           ("head", "hat"))
    v.part("hat_brim", ellipse(qv(0, cy + aba_y * cab, cz + aba_z * cab), qv(rx * aba, ry * aba, 0.05 * cab + 0.3)),
           ("head", "hat"), v.mat2)
    return Vista(cobre=["topknot"], rules=[regra("hat_crown", "hat_brim"), regra("hat_crown", "hair_cap"),
                                           regra("hat_brim", "hair_cap"), regra("hat_brim", "skull"),
                                           regra("hat_crown", "scarf"), regra("hat_brim", "scarf")])


def bolsa(v: Veste) -> Vista:
    """A bolsa a tiracolo: a alça do ombro esquerdo ao quadril direito, por fora da roupa, e o saco no quadril."""
    c, t = v.c, v.c["tronco"]
    fy = c["peito_y"] * 1.12 + 0.75
    pts = [qv(c["ombro_x"] * 0.75, 0.2, 0.98 * t), qv(0, fy, 0.62 * t),
           qv(-c["quadril_larg_x"] * 0.9, fy * 0.6, 0.08 * t)]
    v.part("bag_strap", polyline(pts, 1), ("torso", "bag"), v.mat2)
    r = c["quadril_larg_x"] * 0.55
    v.part("bag", ellipse(qv(-c["quadril_larg_x"] * 1.05, fy * 0.35, -0.02 * t), qv(r, r * 0.8, r * 1.1)),
           ("torso", "bag"))
    return Vista(hide_back=["bag_strap"], rules=[regra("bag", "pants_seat"), regra("bag", "jacket_waist"),
                                                 regra("bag", "skirt_waist")],
                 front_rules=[regra("bag_strap", "jacket_chest"), regra("bag_strap", "sash")])


def sandalia(v: Veste) -> Vista:
    """A sola sob o pé, um pouco maior que ele, e a tira sobre o peito do pé."""
    pe, az, rc = v.c["pe"], v.c["tornozelo_z"], v.c["r_canela"]
    for side, _ in SIDES:
        v.part(f"sole_{side}", ellipse(qv(0, 0.18 * pe, -1.05 * az - 0.1), qv(rc * 1.6, 0.52 * pe, 0.35)),
               (f"foot_{side}", f"sandal_{side}"))
        tira = qv(rc * 1.45, 0.10 * pe, PE_ALTO[0] * az * 0.6 + 0.3)
        v.part(f"strap_{side}", ellipse(qv(0, 0.20 * pe, -0.55 * az), tira), (f"foot_{side}", f"sandal_{side}"), v.mat2)
    return Vista(rules=[regra(f"strap_{s}", f"foot_{s}") for s, _ in SIDES])


def tabi(v: Veste) -> Vista:
    """O calçado fechado de pano ou couro sobre o pé e o tornozelo (o contorno do pé, um pouco maior)."""
    pe, az, rc = v.c["pe"], v.c["tornozelo_z"], v.c["r_canela"]
    for side, _ in SIDES:
        v.part(f"tabi_{side}", ellipse(qv(0, 0.02 * pe, -0.40 * az),
                                       qv(rc * 1.4 + 0.2, 0.30 * pe + 0.2, PE_ALTO[0] * az + 0.5)),
               (f"foot_{side}", f"tabi_{side}"))
        v.part(f"tabi_toe_{side}", ellipse(qv(0, 0.42 * pe, -0.60 * az), qv(rc * 1.3 + 0.2, 0.28 * pe + 0.2,
                                                                             PE_ALTO[1] * az + 0.3)),
               (f"foot_{side}", f"tabi_{side}"))
    return Vista(cobre=[f"{p}_{s}" for s, _ in SIDES for p in ("foot", "toe", "j_ankle")])


def saia(v: Veste) -> Vista:
    """A saia em A da cintura até ``comprimento_pct`` da perna (100 = o tornozelo): a cintura na pelve e, de cada
    lado, a metade da saia num osso que segue a coxa com atraso (a barra acompanha o joelho da frente e a de trás
    recua, sem a saia abrir como calça); o painel do meio, na pelve, fecha a frente e as costas."""
    c = v.c
    hip_z, ankle_z = c["quadril_z"], c["tornozelo_z"]
    hem_z = hip_z - (hip_z - ankle_z) * v.pct("comprimento_pct", 100) + 0.5
    queda = hip_z - hem_z
    # a barra sobre a largura do quadril: 100 % cai reta, 160 % abre em A, 200 % bem rodada
    abre = v.pct("largura_pct", 160)
    meia = c["quadril_larg_x"] * 0.72
    for side, sx in SIDES:
        v.b.bone(f"skirt_{side}", "pelvis_tilt", qv(sx * c["quadril_x"], 0, 0), Junta("x", q(queda),
                                                                                       (-35_000, 35_000)))
        v.part(f"skirt_{side}", taper((0.0, 1.0), queda, (meia, meia * abre)), (f"skirt_{side}", "skirt"))
    v.part("skirt_mid", taper((0.0, 1.0), queda, (c["quadril_larg_x"] * 0.9, c["quadril_larg_x"] * 0.9 * abre)),
           ("pelvis_tilt", "skirt"))
    v.part("skirt_waist", ellipse(qv(0, -0.1, 0.6), qv(c["quadril_larg_x"] * 1.12 + 0.4, c["peito_y"] * 0.95 + 0.4,
                                                       0.05 * c["estatura"] + 0.4)), ("pelvis_tilt", "skirt"))
    borda = c["quadril_x"] + meia * abre - 0.5
    v.part("skirt_hem", polyline([qv(-borda, c["r_coxa"] * 0.9, -queda + 0.6),
                                  qv(borda, c["r_coxa"] * 0.9, -queda + 0.6)], 1),
           ("pelvis_tilt", "skirt"), v.mat2)
    cobre = ["pelvis_block"] + [f"{p}_{s}" for s, _ in SIDES for p in ("thigh", "j_hip", "j_knee", "shin")]
    return Vista(cobre=cobre, rules=[regra("skirt_waist", "skirt_mid"), regra("skirt_waist", "skirt_l"),
                                     regra("skirt_waist", "skirt_r"), regra("jacket_waist", "skirt_waist")],
                 front_rules=[regra("skirt_hem", "skirt_mid")], hide_back=["skirt_hem"])


def lenco(v: Veste) -> Vista:
    """O lenço na cabeça: a casca sobre a cabeça, que cobre o alto, os lados e a nuca e deixa o rosto, com o nó
    atrás, na nuca, e as duas pontas pendendo no segundo material."""
    cab, cz = v.c["cabeca"], cranio(v.c)[1]
    nuca = _casca(v, "scarf", LENCO, SEM_LINHA) + 0.3
    v.part("scarf_knot", ellipse(qv(0, nuca, cz - 0.15 * cab), qv(0.16 * cab, 0.12 * cab, 0.12 * cab)),
           ("head", "scarf"))
    for side, sx in SIDES:
        v.part(f"scarf_tail_{side}", polyline([qv(sx * 0.4, nuca, cz - 0.21 * cab),
                                               qv(sx * 1.4, nuca - 0.8, cz - 0.60 * cab)], 1), ("head", "scarf"),
               v.mat2)
    return Vista(cobre=["hair_cap", "topknot", "hair_side_l", "hair_side_r"], back_rules=[regra("scarf_knot", "neck")])


def espada(v: Veste) -> Vista:
    """A espada na mão direita: o cabo no punho fechado (no segundo material), a guarda atravessada e a lâmina, que
    sai para a frente e desce :data:`ESPADA_DESCE` graus abaixo da linha da mão (no repouso a ponta fica à frente,
    perto do chão; no golpe ela segue o braço e a mão). ``comprimento_pct`` é a lâmina sobre :data:`ESPADA_M`."""
    a = math.radians(ESPADA_DESCE)
    d = (0.0, math.cos(a), -math.sin(a))
    lamina, cabo, guarda = (m * PX_POR_M for m in ESPADA_M)
    lamina *= v.pct("comprimento_pct", 100)
    g = (0.0, 0.0, -0.42 * v.c["mao"])  # o meio do punho fechado

    def ao_longo(s: float) -> tuple[float, float, float]:
        return (g[0], g[1] + d[1] * s, g[2] + d[2] * s)

    def fuso(de: tuple[float, float, float], ate: tuple[float, float, float], r0: float, r1: float) -> dict[str, Any]:
        return {"type": "tapered_polyline", "points_q8": [qv(*de), qv(*ate)], "radii_q8": [q(r0), q(r1)]}

    base = ao_longo(cabo / 2)
    metal = Parte(bone="hand_r", group="sword", tags=ESPADA_TAGS)
    v.b.part("sword_blade", v.mat, fuso(base, ao_longo(cabo / 2 + lamina), ESPADA_R[0], ESPADA_R[1]), metal)
    v.b.part("sword_guard", v.mat, fuso((-guarda / 2, base[1], base[2]), (guarda / 2, base[1], base[2]),
                                        ESPADA_R[2], ESPADA_R[2]), metal)
    v.b.part("sword_grip", v.mat2 or v.mat, fuso(ao_longo(-cabo / 2), base, ESPADA_R[2], ESPADA_R[2]), metal)
    return Vista(rules=[regra("hand_r", "sword_grip"), regra("sword_guard", "sword_blade")])


PECAS: dict[str, Callable[[Veste], Vista]] = {
    "jaqueta": jaqueta, "faixa": faixa, "calca": calca, "olhos": olhos, "cabelo_preso": cabelo_preso,
    "chapeu": chapeu, "bolsa": bolsa, "sandalia": sandalia, "tabi": tabi, "saia": saia, "lenco": lenco,
    "espada": espada,
}
