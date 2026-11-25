"""O penedo: a pedra solta com forma de pedra, não de ovo. Um poliedro convexo sorteado pela semente (anéis de pontos
na base, na cintura e no ombro, e o topo), com as faces quase no mesmo plano fundidas numa face só: a pedra tem
quinas, arestas e faces grandes e pequenas. Só as faces de frente para a câmera se desenham (as do convexo nunca se
cobrem), cada uma com o tom pela normal da família do material; as de cima podem levar o musgo, e as maiores, uma
fenda.

O sorteio é da semente do nó: a mesma composição dá a mesma pedra, e outra semente dá outra pedra do mesmo tipo.
"""

from __future__ import annotations

import math
from itertools import combinations
from typing import Any

from ..construtor import FLAT, LIT, Vec
from .construcao import DESVIO
from .peca import Arg, Ctx, Peca

TESTE = "tests/test_penedo.py"
X = Arg
# a direção da câmera (o 3/4 oblíquo: o chão a 0,6 e a altura a cos 45°): a face de frente para ela se vê
CAMERA = (0.0, math.sqrt(0.5) / math.hypot(math.sqrt(0.5), 0.6), 0.6 / math.hypot(math.sqrt(0.5), 0.6))
VISTA_MIN = 0.04  # a face quase de lado vira um risco: não se desenha
AREA_MIN = 3.0  # nem a face menor que 3 px² na tela: o contorno das vizinhas a cobre
FUNDE = math.cos(math.radians(13))  # as faces vizinhas a menos de 13° uma da outra viram uma face só
# os anéis: (a altura, em fração da altura; o raio, em fração do meio; a parte dos pontos)
ANEIS = ((0.0, 1.0, 0.36), (0.42, 1.04, 0.32), (0.80, 0.62, 0.32))
TOPO = 0.42  # o raio do anel do topo, em fração do meio, na pedra sem ponta
# a luz (do alto, da esquerda e um pouco da frente) para o tom do musgo, que não tem família de degraus
LUZ = (-0.45, 0.35, 0.82)
MUSGO = ((0.72, "capim_claro"), (0.25, "musgo"), (-2.0, "capim_escuro"))


def _pontos(c: Ctx, a: dict[str, Any]) -> list[Vec]:
    """Os pontos do poliedro: os anéis, cada um girado e com os raios e as alturas sorteados, e o topo."""
    (cx, cy, cz), (w, d, h) = a["centro"], a["tamanho"]
    irr, agudo, inclina = a["irregular"], a["agudo"], a["inclina"]
    n = max(6, min(24, a["facetas"]))

    def sorte(amp: float) -> float:
        return (c.st.randint(-1000, 1000) / 1000) * amp

    pts: list[Vec] = []
    for zf, rf, parte in ANEIS:
        k = max(3, round(n * parte))
        giro = c.st.randint(0, 359) * math.pi / 180
        rf = rf * (1 - 0.55 * agudo) if zf > 0.5 else rf
        for i in range(k):
            ang = giro + 2 * math.pi * i / k + sorte(math.pi / k * irr)
            r = rf * (1 + sorte(irr))
            z = 0.0 if zf == 0 else h * min(0.97, max(0.05, zf + sorte(0.22 * irr)))
            pts.append((cx + w * r * math.cos(ang) + inclina * w * z / h, cy + d * r * math.sin(ang), cz + z))
    # o topo: um anel pequeno e chato (o bloco, a laje) que fecha num ponto quando a pedra é aguda
    rt = TOPO * (1 - agudo) * (1 + sorte(irr))
    meio = (cx + sorte(0.3 * irr) * w + inclina * w, cy + sorte(0.3 * irr) * d)
    k = 1 if rt < 0.08 else c.st.randint(3, 4)
    giro = c.st.randint(0, 359) * math.pi / 180
    for i in range(k):
        ang = giro + 2 * math.pi * i / k + sorte(math.pi / k * irr)
        z = h * (1 - (sorte(0.08 * irr) + 0.08 * irr if k > 1 else 0))
        pts.append((meio[0] + w * rt * math.cos(ang) * (k > 1), meio[1] + d * rt * math.sin(ang) * (k > 1), cz + z))
    return pts


def _faces(pts: list[Vec]) -> list[tuple[list[int], Vec]]:
    """As faces do fecho convexo (os triângulos com todos os outros pontos de um lado), com a normal de fora."""
    meio = [sum(p[i] for p in pts) / len(pts) for i in range(3)]
    out: list[tuple[list[int], Vec]] = []
    for i, j, k in combinations(range(len(pts)), 3):
        a, b, c = pts[i], pts[j], pts[k]
        u, v = [b[t] - a[t] for t in range(3)], [c[t] - a[t] for t in range(3)]
        nrm = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
        tam = math.sqrt(sum(x * x for x in nrm))
        if tam < 1e-6:
            continue
        nrm = (nrm[0] / tam, nrm[1] / tam, nrm[2] / tam)
        lado = [sum(nrm[t] * (p[t] - a[t]) for t in range(3)) for p in pts]
        if all(s <= 1e-6 for s in lado) or all(s >= -1e-6 for s in lado):
            if sum(nrm[t] * (meio[t] - a[t]) for t in range(3)) > 0:
                nrm = (-nrm[0], -nrm[1], -nrm[2])
            out.append(([i, j, k], nrm))
    return out


def _fundir(faces: list[tuple[list[int], Vec]]) -> list[tuple[set[int], Vec]]:
    """As faces vizinhas (com uma aresta em comum) quase no mesmo plano numa só, com a normal média."""
    pai = list(range(len(faces)))

    def raiz(i: int) -> int:
        while pai[i] != i:
            pai[i] = pai[pai[i]]
            i = pai[i]
        return i

    for i, j in combinations(range(len(faces)), 2):
        (fi, ni), (fj, nj) = faces[i], faces[j]
        if len(set(fi) & set(fj)) >= 2 and sum(ni[t] * nj[t] for t in range(3)) > FUNDE:
            pai[raiz(i)] = raiz(j)
    grupos: dict[int, tuple[set[int], list[float]]] = {}
    for i, (f, nrm) in enumerate(faces):
        vs, soma = grupos.setdefault(raiz(i), (set(), [0.0, 0.0, 0.0]))
        vs.update(f)
        for t in range(3):
            soma[t] += nrm[t]
    out = []
    for vs, soma in grupos.values():
        tam = math.sqrt(sum(x * x for x in soma)) or 1.0
        out.append((vs, (soma[0] / tam, soma[1] / tam, soma[2] / tam)))
    return out


def _em_volta(pts: list[Vec], nrm: Vec) -> list[Vec]:
    """Os vértices da face em ordem, em volta do meio dela, no plano da normal."""
    meio = [sum(p[t] for p in pts) / len(pts) for t in range(3)]
    ref = (1.0, 0.0, 0.0) if abs(nrm[0]) < 0.9 else (0.0, 1.0, 0.0)
    e1 = (ref[1] * nrm[2] - ref[2] * nrm[1], ref[2] * nrm[0] - ref[0] * nrm[2], ref[0] * nrm[1] - ref[1] * nrm[0])
    e2 = (nrm[1] * e1[2] - nrm[2] * e1[1], nrm[2] * e1[0] - nrm[0] * e1[2], nrm[0] * e1[1] - nrm[1] * e1[0])

    def ang(p: Vec) -> float:
        d = [p[t] - meio[t] for t in range(3)]
        return math.atan2(sum(d[t] * e2[t] for t in range(3)), sum(d[t] * e1[t] for t in range(3)))

    return sorted(pts, key=ang)


def _material(a: dict[str, Any], nrm: Vec, musgo: bool) -> tuple[str, tuple[str, ...]]:
    """O musgo (o tom pela luz, à mão: o verde não tem família de degraus); a pedra pela normal, um degrau abaixo nas
    faces de costas para a luz (a quarta cor da pedra) e com o ``tom`` da pedra toda."""
    if musgo:
        lam = sum(nrm[t] * LUZ[t] for t in range(3)) / math.sqrt(sum(x * x for x in LUZ))
        return next(m for lim, m in MUSGO if lam > lim), FLAT
    desvio = a["tom"] - (1 if nrm[0] > 0.55 or nrm[2] < 0.15 and nrm[0] > 0.2 else 0)
    return a["material"], (*FLAT, LIT, *((DESVIO[max(-1, min(1, desvio))],) if desvio else ()))


def _penedo(c: Ctx, a: dict[str, Any]) -> None:
    pts = _pontos(c, a)
    vistas = []
    for vs, nrm in _fundir(_faces(pts)):
        frente = sum(nrm[t] * CAMERA[t] for t in range(3))
        face = _em_volta([pts[i] for i in vs], nrm)
        if frente > VISTA_MIN and nrm[2] > -0.5 and _na_tela(face) >= AREA_MIN:
            fundo = sum(sum(p[t] for p in face) / len(face) * CAMERA[t] for t in range(3))
            vistas.append((fundo, face, nrm))
    vistas.sort(key=lambda f: f[0])  # do fundo para a frente
    # o musgo nas faces mais deitadas: a parte ``musgo`` das que se veem, só as que olham para cima
    por_cima = sorted(range(len(vistas)), key=lambda i: -vistas[i][2][2])
    musgo = {i for i in por_cima[: round(a["musgo"] * len(vistas))] if vistas[i][2][2] > 0.25}
    areas = []
    for i, (_, face, nrm) in enumerate(vistas):
        mat, tags = _material(a, nrm, i in musgo)
        c.poly(f"{c.pid}_{i:02d}", mat, face, min(i, 90), tags)
        if mat == a["material"]:
            areas.append((_area(face), i, face))
    for k, (_, i, face) in enumerate(sorted(areas, reverse=True)[: a["fendas"]]):
        de, ate = _fenda(c, face)
        c.line(f"{c.pid}_fenda_{k}", "rejunte", [de, ate], min(i, 90) + 1)


def _na_tela(face: list[Vec]) -> float:
    """A área da face na tela (px²): x de lado, o chão a 0,6 e a altura a cos 45°."""
    pts = [(p[0], 0.6 * p[1] - math.sqrt(0.5) * p[2]) for p in face]
    return abs(sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(pts, pts[1:] + pts[:1], strict=True))) / 2


def _area(face: list[Vec]) -> float:
    soma = [0.0, 0.0, 0.0]
    for p, q in zip(face, face[1:] + face[:1], strict=True):
        soma[0] += p[1] * q[2] - p[2] * q[1]
        soma[1] += p[2] * q[0] - p[0] * q[2]
        soma[2] += p[0] * q[1] - p[1] * q[0]
    return math.sqrt(sum(x * x for x in soma)) / 2


def _fenda(c: Ctx, face: list[Vec]) -> tuple[Vec, Vec]:
    """A fenda: de um ponto de uma aresta até perto do meio da face (a rachadura que entra pela quina)."""
    n = len(face)
    i = c.st.randint(0, n - 1)
    p, q = face[i], face[(i + 1) % n]
    t = c.st.randint(30, 70) / 100
    de = tuple(p[k] + (q[k] - p[k]) * t for k in range(3))
    meio = [sum(v[k] for v in face) / n for k in range(3)]
    f = c.st.randint(55, 85) / 100
    ate = tuple(de[k] + (meio[k] - de[k]) * f for k in range(3))
    return (de[0], de[1], de[2]), (ate[0], ate[1], ate[2])


PECAS_ROCHA = [
    Peca("penedo", "Penedo: a pedra solta com forma de pedra (faces, quinas e arestas sorteadas pela semente), com o "
         "tom pela normal, o musgo nas faces de cima e fendas nas maiores", (
             X("centro", "ponto", "o meio da base", ["0", "0", "0"]),
             X("tamanho", "ponto", "a meia largura, o meio fundo e a altura"),
             X("facetas", "inteiro", "os pontos do poliedro (de 6 a 24: mais, mais faces e mais redonda)", "11"),
             X("irregular", "escalar", "quanto os pontos fogem dos anéis (0 = regular; 0,5 = lascada)", "0.3"),
             X("agudo", "escalar", "quanto o ombro fecha para a ponta (0 = bloco; 1 = ponta)", "0"),
             X("inclina", "escalar", "quanto o topo se desloca em x, em fração da meia largura", "0"),
             X("material", "material", "a família da pedra (alvenaria: granito; palha: arenito)", "alvenaria"),
             X("musgo", "escalar", "a parte das faces vistas que leva musgo, das mais deitadas (0 = nada)", "0"),
             X("fendas", "inteiro", "as fendas nas faces maiores", "0"),
             X("tom", "inteiro", "o degrau da pedra toda na família (-1 escura, 0, 1 clara)", "0")),
        _penedo, (("bloco", {"tamanho": ["60cm", "45cm", "70cm"]}),
                  ("ponta com musgo", {"tamanho": ["40cm", "35cm", "1.1m"], "agudo": "0.8", "musgo": "0.35",
                                       "fendas": "1"}),
                  ("laje de arenito", {"tamanho": ["80cm", "55cm", "30cm"], "facetas": "12", "irregular": "0.35",
                                       "inclina": "0.15", "material": "palha", "fendas": "2", "tom": "-1"})),
        TESTE, (_pontos, _faces, _fundir, _em_volta, _material, _na_tela, _area, _fenda)),
]
