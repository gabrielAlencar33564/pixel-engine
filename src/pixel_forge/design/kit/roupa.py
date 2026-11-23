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
from .humano import SIDES, taper

Regra = dict[str, str]


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


def _surface_y(e: tuple[float, float, float, float], z: float) -> float:
    """A frente (+y) da elipse (cy, ry, cz, rz) no plano x = 0, na altura ``z``."""
    cy, ry, cz, rz = e
    u = (z - cz) / rz
    return cy + ry * math.sqrt(max(0.0, 1 - u * u))


def jaqueta(v: Veste) -> Vista:
    """A blusa ou jaqueta cruzada, a aba esquerda sobre a direita (a gola em V), com mangas."""
    c, t, lw = v.c, v.c["tronco"], v.pct("largura_pct", 140)
    peito = (0.1, c["peito_y"] * 1.12 + 0.35, 0.68 * t, 0.36 * t)
    v.part("jacket_chest", ellipse(qv(0, peito[0], peito[2]), qv(c["peito_x"] * 1.1 + 0.4, peito[1], peito[3])),
           ("torso", "jacket"))
    v.part("jacket_waist", ellipse(qv(0, 0, 0.22 * t), qv(c["cintura_x"] * 1.15 + 0.45, c["peito_y"] * 0.85 + 0.45,
                                                          0.26 * t)), ("torso", "jacket"))
    for pid, (x0, x1, z1) in (("lapel_l", (-0.9, 1.8, 0.30)), ("lapel_r", (0.9, 0.0, 0.55))):
        pts = [qv(x0, _surface_y(peito, 0.98 * t) + 0.1, 0.98 * t), qv(x1, _surface_y(peito, z1 * t) + 0.25, z1 * t)]
        v.part(pid, polyline(pts, 1), ("torso", "jacket"), v.mat2)
    manga = v.op.get("manga", 2)
    cobre, rules = ["chest", "waist"], []
    for side, _ in SIDES:
        boca = c["r_cotovelo"] * (0.9 + 0.45 * lw) + 0.3
        if manga >= 1:
            v.part(f"sleeve_{side}", taper((-0.05, 1.04), c["braco"], (c["r_braco"] * 1.25 + 0.3, boca)),
                   (f"upper_arm_{side}", f"sleeve_{side}"))
            cobre += [f"upper_arm_{side}", f"j_shoulder_{side}"]
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


def _skull(c: dict[str, float]) -> tuple[float, float, float, float, float]:
    cab = c["cabeca"]
    return -0.06 * cab, 0.43 * cab, c["cabeca_larg"] / 2, 0.41 * cab, 0.33 * cab


def olhos(v: Veste) -> Vista:
    """Dois olhos na frente do crânio, a meio caminho entre o centro e o alto (a 45° o olho sobe); somem de costas, e
    de perfil o do lado de lá some."""
    cy, cz, rx, ry, rz = _skull(v.c)
    z = cz + 0.5 * rz
    for side, sx in SIDES:
        x = sx * 0.42 * rx
        y = cy + ry * math.sqrt(max(0.0, 1 - (x / rx) ** 2 - ((z - cz) / rz) ** 2))
        v.part(f"eye_{side}", ellipse(qv(x, y, z), qv(0.6, 0.5, 0.9)), ("head", "eyes"))
    return Vista(hide_back=["eye_l", "eye_r"], hide_w=["eye_r"], hide_e=["eye_l"],
                 front_rules=[regra(f"eye_{s}", o) for s in ("l", "r") for o in ("skull", "hair_cap", "scarf")])


def cabelo_preso(v: Veste) -> Vista:
    """O cabelo puxado para trás, cobrindo o alto e a nuca e deixando a testa, com o coque no alto."""
    cab = v.c["cabeca"]
    cy, cz, rx, ry, rz = _skull(v.c)
    v.part("hair_cap", ellipse(qv(0, cy - 0.20 * cab, cz + 0.13 * cab), qv(rx + 0.25, ry + 0.05, rz)), ("head", "hair"))
    v.part("topknot", ellipse(qv(0, cy - 0.16 * cab, cz + 0.42 * cab), qv(0.14 * cab, 0.16 * cab, 0.13 * cab)),
           ("head", "hair"))
    return Vista(rules=[regra("topknot", "hair_cap")], front_rules=[regra("skull", "hair_cap")],
                 back_rules=[regra("hair_cap", "skull")])


def chapeu(v: Veste) -> Vista:
    """O chapéu mole de aba larga: a copa baixa sobre o crânio e a aba em disco, um pouco caída para a frente;
    ``largura_pct`` é a aba sobre a largura da cabeça."""
    cab, aba = v.c["cabeca"], v.pct("largura_pct", 180)
    cy, cz, rx, ry, _ = _skull(v.c)
    v.part("hat_crown", ellipse(qv(0, cy - 0.02 * cab, cz + 0.30 * cab), qv(rx + 0.35, ry + 0.3, 0.24 * cab)),
           ("head", "hat"))
    v.part("hat_brim", ellipse(qv(0, cy + 0.06 * cab, cz + 0.16 * cab), qv(rx * aba, ry * aba, 0.05 * cab + 0.3)),
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
        v.part(f"strap_{side}", ellipse(qv(0, 0.20 * pe, -0.55 * az), qv(rc * 1.45, 0.10 * pe, 0.72 * az * 0.6 + 0.3)),
               (f"foot_{side}", f"sandal_{side}"), v.mat2)
    return Vista(rules=[regra(f"strap_{s}", f"foot_{s}") for s, _ in SIDES])


def tabi(v: Veste) -> Vista:
    """O calçado fechado de pano ou couro sobre o pé e o tornozelo (o contorno do pé, um pouco maior)."""
    pe, az, rc = v.c["pe"], v.c["tornozelo_z"], v.c["r_canela"]
    for side, _ in SIDES:
        v.part(f"tabi_{side}", ellipse(qv(0, 0.02 * pe, -0.40 * az),
                                       qv(rc * 1.4 + 0.2, 0.30 * pe + 0.2, 0.72 * az + 0.5)),
               (f"foot_{side}", f"tabi_{side}"))
        v.part(f"tabi_toe_{side}", ellipse(qv(0, 0.42 * pe, -0.60 * az), qv(rc * 1.3 + 0.2, 0.28 * pe + 0.2,
                                                                             0.45 * az + 0.3)),
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
    abre = v.pct("largura_pct", 160)
    for side, sx in SIDES:
        v.b.bone(f"skirt_{side}", "pelvis_tilt", qv(sx * c["quadril_x"], 0, 0), Junta("x", q(queda),
                                                                                       (-35_000, 35_000)))
        v.part(f"skirt_{side}", taper((0.0, 1.0), queda, (c["quadril_larg_x"] * 0.72, c["r_coxa"] * abre + 0.6)),
               (f"skirt_{side}", "skirt"))
    v.part("skirt_mid", taper((0.0, 1.0), queda, (c["quadril_larg_x"] * 0.9, c["r_coxa"] * abre * 1.15 + 0.6)),
           ("pelvis_tilt", "skirt"))
    v.part("skirt_waist", ellipse(qv(0, -0.1, 0.6), qv(c["quadril_larg_x"] * 1.12 + 0.4, c["peito_y"] * 0.95 + 0.4,
                                                       0.05 * c["estatura"] + 0.4)), ("pelvis_tilt", "skirt"))
    v.part("skirt_hem", polyline([qv(-c["r_coxa"] * abre * 1.4, c["r_coxa"] * 0.9, -queda + 0.6),
                                  qv(c["r_coxa"] * abre * 1.4, c["r_coxa"] * 0.9, -queda + 0.6)], 1),
           ("pelvis_tilt", "skirt"), v.mat2)
    cobre = ["pelvis_block"] + [f"{p}_{s}" for s, _ in SIDES for p in ("thigh", "j_hip", "j_knee", "shin")]
    return Vista(cobre=cobre, rules=[regra("skirt_waist", "skirt_mid"), regra("skirt_waist", "skirt_l"),
                                     regra("skirt_waist", "skirt_r"), regra("jacket_waist", "skirt_waist")],
                 front_rules=[regra("skirt_hem", "skirt_mid")], hide_back=["skirt_hem"])


def lenco(v: Veste) -> Vista:
    """O lenço na cabeça: cobre o alto, os lados e a nuca e deixa o rosto, com o nó atrás, na nuca, e as duas pontas
    pendendo no segundo material."""
    cab = v.c["cabeca"]
    cy, cz, rx, ry, rz = _skull(v.c)
    v.part("scarf", ellipse(qv(0, cy - 0.12 * cab, cz + 0.08 * cab), qv(rx + 0.45, ry + 0.25, rz + 0.35)),
           ("head", "scarf"))
    nuca = cy - ry - 0.2
    v.part("scarf_knot", ellipse(qv(0, nuca, cz - 0.30 * cab), qv(0.16 * cab, 0.12 * cab, 0.12 * cab)),
           ("head", "scarf"))
    for side, sx in SIDES:
        v.part(f"scarf_tail_{side}", polyline([qv(sx * 0.4, nuca, cz - 0.36 * cab),
                                               qv(sx * 1.4, nuca - 0.8, cz - 0.75 * cab)], 1), ("head", "scarf"),
               v.mat2)
    return Vista(cobre=["hair_cap", "topknot"], rules=[regra("scarf_knot", "scarf")],
                 front_rules=[regra("skull", "scarf"), regra("jaw", "scarf"), regra("chin", "scarf")],
                 back_rules=[regra("scarf", "skull"), regra("scarf_knot", "neck")])


PECAS: dict[str, Callable[[Veste], Vista]] = {
    "jaqueta": jaqueta, "faixa": faixa, "calca": calca, "olhos": olhos, "cabelo_preso": cabelo_preso,
    "chapeu": chapeu, "bolsa": bolsa, "sandalia": sandalia, "tabi": tabi, "saia": saia, "lenco": lenco,
}
