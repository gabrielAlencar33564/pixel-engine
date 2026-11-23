"""O corpo canino como peça do kit: o quadrúpede de pernas em Z (o rig ``canino``, quatro segmentos por perna) e as
massas do corpo, na régua do corpo canino (px), escaladas pelas medidas do animal em metros:

- a altura na cernelha escala o que é vertical (as pernas, a altura do corpo) e a largura;
- o comprimento escala o que vai de trás para a frente (o tronco, onde nascem as pernas, o pescoço e a cauda);
- a cabeça e a cauda têm o tamanho delas; ``espessura`` engrossa o corpo e as pernas.

As marcas são materiais: ``ventre`` (a barriga, o peito e a mandíbula), ``meias`` (as canelas, as patas e a ponta da
orelha em pé; vazio = a pelagem) e ``dorso`` (a manta nas costas; vazio = sem manta). ``orelha`` 1 é em pé; 0, caída
para a frente, com a aba no ``dorso``. ``cauda_alta`` 0 é a cauda caída, de ponta no ``dorso`` (ou, sem ele, no
``ventre``); 1, enrolada por cima da garupa, de ponta no ``ventre``.
"""

from __future__ import annotations

from typing import Any

from ..construtor import AssetBuilder, Parte, ellipse, polyline, q, qv
from .esqueleto import monta
from .peca import Arg, Ctx, Peca

TESTE = "tests/test_quadrupede.py::test_cada_variacao_do_corpo_cabe_nas_8_direcoes"
OITO = ("S", "SW", "W", "NW", "N", "NE", "E", "SE")
FRENTE, COSTAS = ("S", "SW", "SE", "W", "E"), ("N", "NE", "NW")
# a régua (px): a altura na cernelha, do peito à garupa, a cabeça (do occipício ao focinho) e a cauda
CERNELHA, COMPRIMENTO, CABECA, CAUDA = 18.2, 20.6, 9.7, 7.5
OSSOS = {  # as medidas do rig na régua (px) e o eixo que escala cada uma: z vertical, y comprimento, x largura,
    # c cabeça, t cauda
    "corpo_z": (13.1953125, "z"), "corpo_comp": (25.59375, "y"), "pescoco_y": (10.3984375, "y"),
    "pescoco_z": (4.80078125, "z"), "cabeca": (5.203125, "c"), "crista_x": (2.28125, "x"), "crista_y": (-1.28125, "y"),
    "crista_z": (4.203125, "z"), "crista": (3.953125, "z"), "cauda_y": (-10.0, "y"), "cauda_z": (1.6015625, "z"),
    "cauda": (5.203125, "t"), "ombro_x": (4.21484375, "x"), "ombro_y": (5.6015625, "y"), "perna_z": (-1.9609375, "z"),
    "umero": (3.3984375, "z"), "antebraco": (5.6015625, "z"), "metacarpo": (1.8984375, "z"), "pata": (1.0, "z"),
    "femur": (4.6015625, "z"), "tibia": (5.0, "z"), "metatarso": (3.3984375, "z")}
REPOUSO = {"umero_mdeg": -30000.0, "antebraco_mdeg": 30000.0, "metacarpo_mdeg": 15000.0, "pata_f_mdeg": -15000.0,
           "femur_mdeg": 35000.0, "tibia_mdeg": -85000.0, "metatarso_mdeg": 58000.0, "pata_b_mdeg": -8000.0}
Massa = tuple[str, str, tuple[float, float, float], tuple[float, float, float]]
# as massas na régua (px): id, papel do material, centro, raios (e as marcas)
TRONCO: list[tuple[str, str, tuple[float, float, float], tuple[float, float, float], tuple[str, ...]]] = [
    ("chest", "pelagem", (0, 3.8, 1.2), (4.0, 6.2, 3.8), ()),
    ("body", "pelagem", (0, -5.2, 1.6), (3.4, 5.4, 3.0), ()),
    ("belly", "ventre", (0, 1.0, -2.0), (2.2, 5.5, 0.9), ("detail_light", "flat")),
    ("neck", "pelagem", (0, 8.8, 3.2), (3.0, 3.0, 3.7), ()),
    ("bib", "ventre", (0, 9.9, 1.0), (2.1, 1.4, 3.0), ("flat",))]
CABECA_P: list[tuple[str, str, tuple[float, float, float], tuple[float, float, float], tuple[str, ...]]] = [
    ("head", "pelagem", (0, 0.4, 0), (2.9, 3.0, 2.7), ()),
    ("muzzle", "pelagem", (0, 4.0, -0.8), (1.5, 2.8, 1.3), ()),
    ("jaw", "ventre", (0, 3.4, -1.7), (1.3, 2.4, 0.7), ("flat",))]
CAUDA_P: list[Massa] = [("tail", "pelagem", (0, -2.0, -0.4), (1.3, 2.6, 1.4)),
                        ("tail_brush", "pelagem", (0, -3.6, -3.4), (1.8, 2.0, 2.9)),
                        ("tail_tip", "ponta", (0, -4.2, -6.2), (1.2, 1.3, 1.3))]
# a cauda enrolada: sobe da garupa, dobra para a frente por cima dela e a ponta cai de lado
CAUDA_ALTA: list[Massa] = [("tail", "pelagem", (0, -1.4, 2.0), (1.0, 1.6, 2.0)),
                           ("tail_brush", "pelagem", (0, 0.4, 4.0), (1.2, 1.8, 1.1)),
                           ("tail_tip", "ventre", (1.0, 1.8, 3.4), (0.8, 0.9, 0.8))]
# as pernas: (peça, osso, raio de cima, raio de baixo) e a massa do ombro ou da anca, girada com o osso
PERNA = {"f": [("arm", "upper", 1.70, 1.30), ("forearm", "lower", 1.15, 0.95), ("cannon", "cannon", 0.90, 0.80)],
         "b": [("thigh", "upper", 1.90, 1.30), ("shin", "lower", 1.25, 0.85), ("cannon", "cannon", 0.85, 0.75)]}
MASSA = {"f": ("shoulder", (0, 0.1, -0.8), (1.3, 1.6, 2.2)), "b": ("haunch", (0, -0.4, -0.8), (1.4, 2.0, 2.2))}
LADOS = (("l", 1), ("r", -1))
Escala = tuple[float, float, float]


def _el(cen: tuple[float, ...], r: tuple[float, ...], k: Escala) -> dict[str, Any]:
    return ellipse(qv(cen[0] * k[0], cen[1] * k[1], cen[2] * k[2]), qv(r[0] * k[0], r[1] * k[1], r[2] * k[2]))


def _cabeca(b: AssetBuilder, a: dict[str, Any], mat: dict[str, str], kc: float) -> None:
    for pid, m, cen, r, tags in CABECA_P:
        b.part(pid, mat[m], _el(cen, r, (kc * a["espessura"], kc, kc)), Parte(bone="head", group="head", tags=tags))
    cab = (kc, kc, kc)
    b.part("nose", "olho", _el((0, 6.6, -0.5), (0.5, 0.5, 0.5), cab),
           Parte(bone="head", group="nose", tags=("detail", "pixel_detail")))
    for s, sx in LADOS:
        b.part(f"eye_{s}", a["olhos"], _el((sx * 1.5, 2.3, 0.7), (0.5, 0.5, 0.5), cab),
               Parte(bone="head", group=f"eye_{s}", tags=("detail", "eye", "pixel_detail")))
        b.part(f"ear_{s}", mat["pelagem"], _el((sx * 1.6, -0.4, 2.6), (1.0, 0.7, 1.4), cab),
               Parte(bone="head", group="head"))
        ponta = (sx * 1.8, -0.7, 5.0) if a["orelha"] else (sx * 1.9, 1.0, 2.2)  # em pé; caída para a frente
        b.part(f"ear_tip_{s}", mat["meias" if a["orelha"] else "dorso"],
               polyline([qv(sx * 1.6 * kc, -0.4 * kc, 3.0 * kc), qv(ponta[0] * kc, ponta[1] * kc, ponta[2] * kc)], 1),
               Parte(bone="head", group="head"))


def _pernas(b: AssetBuilder, mat: dict[str, str], k: Escala) -> None:
    kx, _, kz = k
    for fb in ("f", "b"):
        for s, _ in LADOS:
            leg = f"{fb}{s}"
            for nome, osso, r0, r1 in PERNA[fb]:
                comp = b.bones[[o["id"] for o in b.bones].index(f"{osso}_{leg}")]["length_q8"]
                b.part(f"{nome}_{leg}", mat["meias" if osso == "cannon" else "pelagem"],
                       {"type": "tapered_polyline", "points_q8": [[0, 0, 0], [0, 0, -comp]],
                        "radii_q8": [q(r0 * kx), q(r1 * kx)]}, Parte(bone=f"{osso}_{leg}", group=f"leg_{leg}"))
            nome, cen, r = MASSA[fb]
            b.part(f"{nome}_{leg}", mat["pelagem"], _el(cen, r, (kx, kz, kz)),
                   Parte(bone=f"upper_{leg}", group=f"leg_{leg}", tags=("oriented",)))
            b.part(f"paw_{leg}", mat["meias"], _el((0, 0.6, -0.2), (1.0, 1.5, 0.7), (kx, kz, kz)),
                   Parte(bone=f"foot_{leg}", group=f"paw_{leg}"))


def _vistas(kc: float) -> dict[str, dict[str, Any]]:
    """De frente, o focinho, os olhos e a mandíbula sobre a cabeça; de costas, a barriga, o peito e a mandíbula somem;
    nas vistas de frente a cabeça e o focinho vêm 2 px para a câmera."""
    regras = [{"front": "nose", "back": "muzzle"}, {"front": "eye_l", "back": "head"},
              {"front": "eye_r", "back": "head"}, {"front": "jaw", "back": "muzzle"}]
    return {d: {"occlusion_rules": regras if d in FRENTE else [],
                "depth_bias": {"head": q(2 * kc), "muzzle": q(2 * kc)} if d in ("S", "SW", "SE") else {},
                "visibility": dict.fromkeys(("belly", "bib", "jaw"), "hidden") if d in COSTAS else {}}
            for d in OITO}


def _corpo_canino(c: Ctx, a: dict[str, Any]) -> None:
    e = a["espessura"]
    k = {"z": a["altura"] / CERNELHA, "y": a["comprimento"] / COMPRIMENTO, "c": a["cabeca"] / CABECA,
         "t": a["cauda"] / CAUDA}
    k["x"] = k["z"] * e
    monta(c.b, "canino", {**{n: v * k[eixo] for n, (v, eixo) in OSSOS.items()}, **REPOUSO})
    mat = {"pelagem": a["pelagem"], "ventre": a["ventre"], "meias": a["meias"] or a["pelagem"],
           "dorso": a["dorso"] or a["pelagem"], "ponta": a["dorso"] or a["ventre"]}
    b, kx, ky, kz = c.b, k["x"], k["y"], k["z"]
    b.part("ground_shadow", "sombra", _el((0, 0, 0), (5.0, 12.5, 0.6), (kx, ky, 1)),
           Parte(tags=("ground_shadow",), priority=-100))
    for pid, m, cen, r, tags in TRONCO:
        b.part(pid, mat[m], _el(cen, r, (kx, ky, kz)), Parte(bone="body", group="body", tags=tags))
    if a["dorso"]:
        b.part("saddle", mat["dorso"], _el((0.7, -1.6, 3.8), (2.8, 6.0, 1.0), (kx, ky, kz)),
               Parte(bone="body", group="body", tags=("flat",)))
    _cabeca(b, a, mat, k["c"])
    for pid, m, centro, raios in CAUDA_ALTA if a["cauda_alta"] else CAUDA_P:
        b.part(pid, mat[m], _el(centro, raios, (kz * e, k["t"], k["t"])), Parte(bone="tail", group="tail"))
    _pernas(b, mat, (kx, ky, kz))
    c.humano["vistas"] = _vistas(k["c"])


X = Arg
PECAS_QUADRUPEDE = [
    Peca("corpo_canino", "O quadrúpede canino: o rig de pernas em Z e as massas do corpo, nas medidas em metros", (
        X("altura", "comprimento", "a altura na cernelha"), X("comprimento", "comprimento", "do peito à garupa"),
        X("cabeca", "comprimento", "do occipício à ponta do focinho"), X("cauda", "comprimento", "da base à ponta"),
        X("espessura", "escalar", "a grossura do corpo e das pernas sobre a régua", "100%"),
        X("orelha", "inteiro", "1 em pé; 0 caída para a frente, a aba no dorso", "1"),
        X("cauda_alta", "inteiro", "0 caída; 1 enrolada por cima da garupa", "0"),
        X("pelagem", "material", "a pelagem"),
        X("ventre", "material", "a barriga, o peito e a mandíbula", "olho_claro"),
        X("meias", "material", "as patas, as canelas e a ponta da orelha em pé (vazio: a pelagem)", ""),
        X("dorso", "material", "a manta nas costas, a aba da orelha caída, a ponta da cauda caída (vazio: nada)", ""),
        X("olhos", "material", "os olhos", "ambar")),
        _corpo_canino,
        (("esguio, de orelha em pé e manta", {"altura": "0.56m", "comprimento": "0.63m", "cabeca": "0.30m",
                                              "cauda": "0.23m", "pelagem": "pedra", "dorso": "pano_cinza"}),
         ("pequeno, de orelha caída e cauda enrolada", {
             "altura": "0.48m", "comprimento": "0.54m", "cabeca": "0.23m", "cauda": "0.24m", "espessura": "90%",
             "orelha": "0", "cauda_alta": "1", "pelagem": "pelo_castanho", "meias": "olho_claro",
             "dorso": "pano_marrom", "olhos": "olho"}),
         ("alto, de orelha caída", {"altura": "0.66m", "comprimento": "0.72m", "cabeca": "0.27m", "cauda": "0.30m",
                                    "orelha": "0", "pelagem": "pano_cinza", "ventre": "pelo_castanho",
                                    "meias": "pelo_castanho", "olhos": "couro"})),
        TESTE, (_corpo_canino, _el, _cabeca, _pernas, _vistas, monta), vistas=OITO, tipo="quadrupede"),
]
