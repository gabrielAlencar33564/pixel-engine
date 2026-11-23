"""A copa: a folhagem em cachos pontilhados (a folhagem de copa vigente), a copa da conífera em galhos em pena e as
cortinas de ramos pendentes. A copa é a elipse ``[meia largura, meia altura, altura do centro]``; as massas escolhem o
osso pela altura, e o tom delas vem da posição na copa em relação à luz do alto-esquerda."""

from __future__ import annotations

import math
from typing import Any

from ...core.rng import Stream
from ..construtor import Parte, polygon, q, qv
from ..escala import K
from .folhagem import Lugar, Pena, Pontos, Tira, Tons, TonsDaPena, cacho, frond, strand
from .peca import Arg, Ctx, Peca

TESTE = "tests/test_kit.py::test_cada_variacao_monta"
PESO_U, PESO_Y, PESO_SORTE = -0.8, 0.08, 0.15  # o tom pela posição: a esquerda é a luz; a frente, um pouco
CANDIDATOS = 12  # o sorteio do melhor candidato (a copa sem aglomerados)
Massa = tuple[float, float, int, float, str, bool, float]  # (y, z, i, x, classe, pende, raio)
X = Arg


def _classe(st: Stream, uvy: tuple[float, float, float], tom: tuple[float, ...]) -> str:
    u, v, y = uvy
    peso_v, claro, escuro = tom[:3]
    s = PESO_U * u + peso_v * v + PESO_Y * y + PESO_SORTE * st.randint(-100, 100) / 100
    return "light" if s > claro else "dark" if s < escuro else "mid"


def _pontos_no_oval(st: Stream, n: int, eixos: tuple[float, float]) -> list[tuple[float, float]]:
    """``n`` pontos no oval, cada um o candidato mais longe dos de antes (a copa sem aglomerado)."""
    pts: list[tuple[float, float]] = []
    for _ in range(n):
        best, best_d = (0.0, 0.0), -1.0
        for _ in range(CANDIDATOS):
            while True:
                u, v = st.randint(-100, 100) / 100, st.randint(-100, 100) / 100
                if u * u + v * v <= 1.0:
                    break
            d = min((math.hypot((u - pu) * eixos[0], (v - pv) * eixos[1]) for pu, pv in pts), default=math.inf)
            if d > best_d:
                best, best_d = (u, v), d
        pts.append(best)
    return pts


def massas(c: Ctx, a: dict[str, Any]) -> list[Massa]:
    """As massas da copa, cada uma com profundidade, classe de tom, queda (a metade de baixo pende) e raio, e os cachos
    nas âncoras de ``cachos``; da frente para trás."""
    st = c.st
    meia_l, meia_a, cz = a["copa"]
    pts = _pontos_no_oval(st, a["n"], (meia_l, meia_a))
    lo, hi = a["raio"]
    v_cai, queda = a["caida"]
    out: list[Massa] = []
    for i, (u, v) in enumerate(pts):
        y = st.randint(round(a["profundidade"][0] * 10), round(a["profundidade"][1] * 10)) / 10
        cls = _classe(st, (u, v, y / K), a["tom"])
        z = cz + v * meia_a * a["escala_v"] - (queda if v < v_cai else 0.0)
        out.append((y, z, i, u * meia_l * a["espalha"], cls, v < v_cai, lo + (hi - lo) * st.randint(0, 100) / 100))
    for j, (tx, tz, ty) in enumerate(c.ancora(a["cachos"])):  # um cacho na ponta de cada galho
        z = tz + 1.0 * K
        u = tx / (meia_l * a["espalha"])
        v = max(-1.0, min(1.0, (z - cz) / (meia_a * a["escala_v"])))
        cls = _classe(st, (u, v, (ty + 1.0 * K) / K), a["tom"])
        out.append((ty + 1.0 * K, z, len(pts) + j, tx, cls, False, lo + (hi - lo) * st.randint(0, 100) / 100))
    return sorted(out)


def _pontilhado(c: Ctx, a: dict[str, Any]) -> None:
    """Cachos pontilhados (folha ou flor miúda pixel a pixel); o 4º material da linha do tom é o brilho daquela
    classe. ``pontos`` = [densidade ‰, achatado (0 = cacho redondo), brilho ‰]."""
    dens, achata, brilho = a["pontos"]
    for y, z, i, x, cls, _, r in massas(c, a):
        bone, zl = c.osso(z)
        linha = a["tons"][cls]
        luz = (linha[3], round(brilho)) if len(linha) > 3 and brilho >= 1 else None
        cacho(c, f"{c.pid}_{i:02d}", Lugar(bone, qv(0, y, zl), x, 0.0), Tons(*linha[:3]),
              Pontos(r, round(dens), luz, achata or None))


def shade_class(tip_x: float, half_w: float, u: float, front: bool, jitter: float) -> str:
    """O tom do galho em pena: a ponta à esquerda (a luz) e o alto clareiam; à direita e embaixo escurecem; o galho da
    frente ganha um pouco de luz."""
    score = -0.75 * tip_x / max(half_w, 1e-6) + 0.55 * (u - 0.35) + (0.2 if front else 0.0) + 0.18 * jitter
    return "light" if score > 0.6 else "dark" if score < -0.2 else "mid"


def _miolo(c: Ctx, a: dict[str, Any]) -> None:
    """O miolo escuro em cone atrás de todos os galhos (e o fundo dele)."""
    base, hgt, rad = a["base"], a["altura"], a["raio"]
    bone0, zl0 = c.osso(base)
    for nome, frac, mat, alto in (("miolo", 0.55, a["miolo"], 0.96), ("miolo_fundo", 0.2, a["fundo"], 0.32)):
        pid = f"{c.pid}_{nome}"
        c.b.part(pid, mat, polygon(qv(0, -1.0 * K, zl0), [[q(-rad * frac), q(1.5 * K)], [q(rad * frac), q(1.5 * K)],
                                                         [0, q((hgt - base) * alto)]]),
                 Parte(bone=bone0, group=c.grupo, tags=("flat", "no_inner_outline"),
                       priority=-5 if nome == "miolo" else -4))
        c.por_vista.setdefault("S", {}).setdefault("depth_bias", {})[pid] = -65536
    c.regras.append({"front": f"{c.pid}_miolo_fundo", "back": f"{c.pid}_miolo"})


def _andares(a: dict[str, Any]) -> list[float]:
    base, hgt, n = a["base"], a["altura"], a["andares"]
    pesos = [(n - t) ** 0.6 for t in range(n)]
    zs, z = [], base + 2.5 * K
    for t in range(n):
        zs.append(z)
        z += (hgt - 6 * K - base - 2.5 * K) * pesos[t] / sum(pesos)
    return zs


def _andar(c: Ctx, a: dict[str, Any], t: int, zt: float) -> None:
    """Um galho para cada lado (ângulo, alcance e queda sorteados, nunca espelhados) e, fora o do topo, dois da frente
    cobrindo o miolo."""
    st, base, hgt, rad, n = c.st, a["base"], a["altura"], a["raio"], a["andares"]
    u = (zt - base) / (hgt - base)
    alcance = rad * (1 - u) ** 0.95 + 4.0 * K
    topo = t == n - 1
    bone, zl = c.osso(zt)
    for lado in (-1, 1):
        ang = math.radians(90 + lado * -((30 if topo else 100) + st.randint(0, 15 if topo else 25)))
        ln = alcance * (0.6 + st.randint(0, 20) / 100) + 2 * K if topo else alcance * (0.9 + st.randint(0, 25) / 100)
        hw = max(2.2 * K, min(6.0 * K, ln * 0.24 * a["_cheio"] * (0.9 + st.randint(0, 20) / 100)))
        queda = ln * (0.05 if topo else 0.18) * (0.8 + st.randint(0, 40) / 100)
        cls = shade_class(ln * math.cos(ang), rad, u, False, st.randint(-100, 100) / 100)
        frond(c, f"{c.pid}_{t}_{'l' if lado < 0 else 'r'}", Lugar(bone, qv(0, 0, zl), lado * 0.6 * K, 0.0),
              Pena(ang, ln, hw, queda), a["_tons"][cls])
    if topo:
        return
    for lado in (-1, 1):
        x0 = lado * st.randint(0, 15) / 10 * K
        ang = math.radians(-90 + lado * (35 + st.randint(0, 30)))
        ln = alcance * (0.55 + st.randint(0, 20) / 100)
        cls = shade_class(x0 + ln * math.cos(ang), rad, u, True, st.randint(-100, 100) / 100)
        frond(c, f"{c.pid}_{t}_f{'l' if lado < 0 else 'r'}", Lugar(bone, qv(0, 1.0 * K, zl), x0, 2.5 * K),
              Pena(ang, ln, max(2.2 * K, min(5.0 * K, ln * 0.28)), ln * 0.08), a["_tons"][cls])


def _galhos_em_pena(c: Ctx, a: dict[str, Any]) -> None:
    """A copa da conífera: o miolo, os andares (mais juntos para cima, o alcance caindo com a altura) e a guia por
    cima. O tom de cada galho vem da ponta em relação à luz. Deixa a âncora ``topo``."""
    st = c.st
    cheio = a["cheio"][0] + (a["cheio"][1] - a["cheio"][0]) * st.randint(0, 35) / 35
    a = {**a, "_cheio": cheio, "_tons": {cls: TonsDaPena(*a["tons"][cls][:4]) for cls in ("light", "mid", "dark")}}
    _miolo(c, a)
    for t, zt in enumerate(_andares(a)):
        _andar(c, a, t, zt)
    bone, zl = c.osso(a["altura"] - a["guia"])
    frond(c, f"{c.pid}_guia", Lugar(bone, qv(0, 0.5 * K, zl), 0.0, 0.0),
          Pena(math.radians(90 + st.randint(-6, 6)), a["guia"], 2.0 * K, 0.0), a["_tons"]["mid"])
    c.deixa("topo", [(0.0, a["altura"], 0.5 * K)])


def _faixa(st: Stream, f: tuple[float, float]) -> float:
    return f[0] + (f[1] - f[0]) * st.randint(0, 100) / 100


def _cortinas(c: Ctx, a: dict[str, Any]) -> None:
    """Cortinas de ramos pendentes espalhadas na largura, presas na metade de baixo da copa (mais baixas na borda),
    cada uma com comprimento, largura, profundidade, curva e tom pela posição."""
    meia_l, meia_a, cz = a["copa"]
    st, m = c.st, a["n"]
    claro, escuro = a["tom"]
    for j in range(m):
        u = (-1 + (2 * j + 1) / m + st.randint(-40, 40) / 100 / m) * a["espalha"]
        z0 = cz + _faixa(st, a["topo_v"]) * meia_a * math.sqrt(max(0.0, 1 - u * u))
        ln = min(2 * meia_a * _faixa(st, a["comprimento"]), z0 - 2 * K)  # a ponta não entra no chão
        w, y = _faixa(st, a["largura"]), _faixa(st, a["profundidade"])
        curva = (1 if u >= 0 else -1) * _faixa(st, a["curva"])
        s = PESO_U * u + 0.1 * y / K + 0.3 * st.randint(-100, 100) / 100
        cls = "light" if s > claro else "dark" if s < escuro else "mid"
        bone, zl = c.osso(z0)
        strand(c, f"{c.pid}_{j:02d}", Lugar(bone, qv(0, y, zl), u * meia_l, 0.0), Tira(ln, w, curva),
               Tons(*a["tons"][cls][:3]))


COPA = X("copa", "ponto", "a copa: meia largura, meia altura e a altura do centro")
COPA_V = ["1.1m", "1.3m", "2.6m"]
TONS_FOLHA = [["folha_clara", "folha_clara", "folha"], ["folha", "folha_clara", "folha_escura"],
              ["folha_escura", "folha", "pedra_escura"]]
TONS_FOLHOSA = [["folhosa_clara", "folhosa_clara", "folhosa"], ["folhosa", "folhosa_clara", "folhosa_escura"],
                ["folhosa_escura", "folhosa", "folhosa_funda"]]
TONS_AGULHA = [["agulha_clara", "agulha", "agulha", "agulha_escura"], ["agulha", "agulha_clara", "agulha_escura",
               "agulha_escura"], ["agulha_escura", "agulha", "pedra_escura", "pedra_escura"]]
TONS_CAPIM = [["capim_claro", "agulha", "agulha", "capim_escuro"], ["agulha", "capim_claro", "capim_escuro",
              "capim_escuro"], ["capim_escuro", "agulha", "pedra_escura", "pedra_escura"]]
PECAS_COPA = [
    Peca("pontilhado", "A folhagem de copa: cachos pontilhados de folha ou flor miúda, redondos ou em almofada, com um "
         "cacho na ponta de cada galho", (
             COPA, X("n", "inteiro", "massas na copa"),
             X("espalha", "escalar", "fração da largura que elas ocupam", "1"),
             X("escala_v", "escalar", "fração da altura que elas ocupam", "0.85"),
             X("raio", "faixa", "o raio de cada massa (sorteado)"),
             X("profundidade", "faixa", "a profundidade de cada massa", ["-3px", "3px"]),
             X("tons", "tons", "núcleo, luz e sombra (e o brilho) de cada classe: clara, média e escura"),
             X("tom", "fracoes", "o tom pela posição: o peso da altura, o limiar do claro e o do escuro",
               ["0.9", "0.45", "-0.15"]),
             X("caida", "fracoes", "a metade de baixo pende: abaixo de v, desce tanto", ["-1", "0"]),
             X("cachos", "ancora", "as pontas dos galhos onde sai um cacho a mais ('<nó>.pontas')", ""),
             X("pontos", "fracoes", "a densidade ‰ (0 a 1000), o achatado (fator da altura do cacho: 0 = redondo, "
          "0.52 = almofada) e o brilho ‰ (0 a 1000)", ["660", "0", "70"])),
        _pontilhado, (("copa de folha", {"copa": COPA_V, "n": "30", "raio": ["19cm", "26cm"], "tons": TONS_FOLHOSA,
                                         "pontos": ["700", "0", "0"]}),
                      ("almofada", {"copa": COPA_V, "n": "4", "raio": ["37cm", "44cm"], "tons": TONS_AGULHA,
                                    "pontos": ["860", "0.52", "90"]}),
                      ("rala", {"copa": COPA_V, "n": "8", "raio": ["15cm", "20cm"], "tons": TONS_FOLHA,
                                "pontos": ["500", "0", "0"]})),
        TESTE, (_pontilhado, massas, _pontos_no_oval, _classe, cacho)),
    Peca("galhos_em_pena", "A copa da conífera: o miolo escuro e os andares de galhos em pena, a guia no topo", (
        X("base", "comprimento", "a altura do primeiro andar (o topo do tronco à vista)"),
        X("altura", "comprimento", "a altura da ponta"), X("raio", "comprimento", "o alcance dos galhos de baixo"),
        X("andares", "inteiro", "os andares de galhos (verticilos)", "10"),
        X("cheio", "faixa", "a largura dos galhos (sorteada uma vez: a conífera rala ou cheia)", ["0.85", "1.2"]),
        X("guia", "comprimento", "o comprimento da guia (a ponta para cima)", "28cm"),
        X("tons", "tons", "corpo, agulha de cima, agulha de baixo e sombra de cada classe: clara, média e escura"),
        X("miolo", "material", "o cone escuro atrás dos galhos"), X("fundo", "material", "o fundo do miolo")),
        _galhos_em_pena, (("alta", {"base": "28cm", "altura": "4m", "raio": "71cm", "andares": "12",
                                    "tons": TONS_AGULHA, "miolo": "agulha_escura", "fundo": "pedra_escura"}),
                          ("jovem", {"base": "20cm", "altura": "2.4m", "raio": "50cm", "andares": "8",
                                     "tons": TONS_CAPIM, "miolo": "capim_escuro", "fundo": "pedra_escura"}),
                          ("rala", {"base": "40cm", "altura": "3.4m", "raio": "60cm", "cheio": ["0.6", "0.7"],
                                    "tons": TONS_CAPIM, "miolo": "capim_escuro", "fundo": "pedra_escura"})),
        TESTE, (_galhos_em_pena, _miolo, _andares, _andar, shade_class, frond), ancoras=("topo",)),
    Peca("cortinas", "Cortinas de ramos pendentes, presas na metade de baixo da copa (o chorão)", (
        COPA, X("n", "inteiro", "cortinas"), X("espalha", "escalar", "a fração da largura", "0.95"),
        X("topo_v", "faixa", "onde ela prende (de -1 a 0)", ["-0.7", "0"]),
        X("comprimento", "faixa", "o comprimento (fração da altura da copa)", ["0.45", "0.8"]),
        X("largura", "faixa", "a largura no alto"), X("profundidade", "faixa", "a profundidade", ["-4px", "6px"]),
        X("curva", "faixa", "a curva para fora no fim", ["0px", "2px"]), X("tons", "tons", "as três classes"),
        X("tom", "fracoes", "os limiares do claro e do escuro", ["0.35", "-0.3"])),
        _cortinas, (("cheias", {"copa": ["1.2m", "75cm", "1.9m"], "n": "24", "largura": ["5cm", "8cm"],
                                "tons": TONS_FOLHA}),
                    ("poucas", {"copa": ["1.2m", "75cm", "1.9m"], "n": "6", "largura": ["6cm", "9cm"],
                                "tons": TONS_FOLHA}),
                    ("curtas", {"copa": ["1m", "60cm", "1.6m"], "n": "14", "comprimento": ["0.2", "0.4"],
                                "largura": ["4cm", "6cm"], "tons": TONS_FOLHOSA})),
        TESTE, (_cortinas, _faixa, strand)),
]
