"""As formas da folhagem: o cacho pontilhado (flores ou folhas miúdas pixel a pixel), o galho em pena da conífera e a
tira pendente do ramo que cai. Todas no plano xz, presas a um osso numa origem (q8)."""

from __future__ import annotations

import math
from dataclasses import dataclass

from ...core.rng import Stream
from ..construtor import LINE, Parte, polygon, polyline, q
from ..escala import K
from .peca import Ctx

Verts = list[tuple[float, float]]


@dataclass(frozen=True)
class Lugar:
    """Onde a forma fica: o osso, a origem no osso (q8) e o ponto de partida (x, z) em px."""

    bone: str
    origin: list[int]
    x: float
    z: float


@dataclass(frozen=True)
class Tons:
    """O miolo, a luz e a sombra de uma forma (sombreada como uma bola: um tom acima e um abaixo do miolo)."""

    core: str
    lit: str
    shade: str


def _disco(st: Stream, centro: tuple[float, float], rr: float, achata: float | None) -> list[list[int]]:
    """O disco de borda irregular (10 lados), achatado na almofada."""
    vs = []
    for i in range(10):
        a = 2 * math.pi * (i + st.randint(-25, 25) / 100) / 10
        ri = rr * (0.78 + st.randint(0, 30) / 100)
        vz = math.sin(a) * ri if achata is None else math.sin(a) * ri * achata
        vs.append([q(centro[0] + math.cos(a) * ri), q(centro[1] + vz)])
    return vs


@dataclass(frozen=True)
class Pontos:
    """O pontilhado do cacho: o raio, a densidade (‰), o brilho (o material e a densidade, ou nenhum) e o achatado (a
    almofada, ``None`` = o cacho redondo)."""

    raio: float
    densidade: int
    brilho: tuple[str, int] | None
    achata: float | None


def cacho(c: Ctx, pid: str, lg: Lugar, tons: Tons, pts: Pontos) -> None:
    """O cacho pontilhado em camadas sem contorno, de trás para a frente: a sombra (o disco inteiro deslocado para
    baixo-direita), o miolo, a luz no alto-esquerda e, com brilho, os pontos ralos claros. Na almofada, a base escura
    desce, a luz vira a faixa do topo e o brilho são os brotos no alto."""
    r, sq = pts.raio, 1.0 if pts.achata is None else pts.achata
    alm = pts.achata is not None
    camadas = [  # (sufixo, material, deslocamento, raio, densidade)
        ("", tons.shade, (0.4 * K, -0.35 * r * sq) if alm else (0.5 * K, -0.6 * K), r, pts.densidade),
        ("_m", tons.core, (-0.2 * K, 0.05 * r * sq) if alm else (-0.2 * K, 0.1 * K), r * (0.9 if alm else 0.86),
         pts.densidade - 40),
        ("_l", tons.lit, (-0.2 * r, 0.45 * r * sq) if alm else (-0.45 * r, 0.4 * r), r * (0.72 if alm else 0.55),
         pts.densidade - (160 if alm else 120))]
    if pts.brilho is not None:
        camadas.append(("_s", pts.brilho[0], (-0.15 * r, 0.6 * r * sq) if alm else (-0.35 * r, 0.35 * r),
                        r * (0.7 if alm else 0.6), pts.brilho[1]))
    for i, (suf, mat, (dx, dz), rr, dens) in enumerate(camadas):
        vs = _disco(c.st, (lg.x + dx, lg.z + dz), rr, pts.achata)
        geo = {"type": "stipple", "plane": "xz", "origin_q8": lg.origin, "vertices_q8": vs, "density_permille": dens,
               "seed": c.st.randint(0, 65535), "cell_px": 1}
        c.b.part(f"{pid}{suf}", mat, geo,
                 Parte(bone=lg.bone, group=c.grupo, tags=("flat", "no_outline", "pixel_detail")))
        if i:
            c.regras.append({"front": f"{pid}{suf}", "back": f"{pid}{camadas[i - 1][0]}"})


@dataclass(frozen=True)
class TonsDaPena:
    """O corpo do galho em pena, a agulha de cima, a de baixo e a sombra projetada."""

    body: str
    upper: str
    lower: str
    drop: str


@dataclass(frozen=True)
class Pena:
    """O galho em pena: a direção (rad), o comprimento, a meia largura e quanto a ponta cai (px)."""

    ang: float
    length: float
    half_w: float
    droop: float


def _eixo(lg: Lugar, p: Pena, s: float) -> tuple[float, float, float, float]:
    """O ponto do eixo em s ∈ [0, 1] (a ponta cai ``droop``) e a normal unitária de cima."""
    dx, dz = math.cos(p.ang), math.sin(p.ang)
    x = lg.x + p.length * s * dx
    z = lg.z + p.length * s * dz - p.droop * s * s
    tx, tz = p.length * dx, p.length * dz - 2 * p.droop * s
    n = math.hypot(tx, tz) or 1.0
    nx, nz = -tz / n, tx / n
    if nz < 0 or (abs(nz) < 1e-9 and nx > 0):
        nx, nz = -nx, -nz
    return x, z, nx, nz


def _bordas_da_pena(c: Ctx, lg: Lugar, p: Pena, steps: int) -> tuple[Verts, Verts]:
    up: Verts = []
    lo: Verts = []
    for i in range(steps + 1):
        s = i / steps
        prof = math.sin(math.pi * min(1.0, s ** 0.75)) * p.half_w + 0.6 * K * (1 - s)  # base presa, meio largo
        bite = 0.72 if i % 2 else 1.0  # a borda em tufos
        x, z, nx, nz = _eixo(lg, p, s)
        jit = 1 + c.st.randint(-8, 8) / 100
        up.append((x + nx * prof * bite * jit, z + nz * prof * bite * jit))
        lo.append((x - nx * prof * bite * jit, z - nz * prof * bite * jit))
    return up, lo


def frond(c: Ctx, pid: str, lg: Lugar, p: Pena, tons: TonsDaPena) -> None:
    """O corpo com a borda em tufos, a sombra projetada (o corpo encurtado deslocado para baixo-direita) e as agulhas
    em espinha da nervura para a borda, inclinadas para a ponta."""
    steps = max(4, round(p.length / (2.6 * K)))
    up, lo = _bordas_da_pena(c, lg, p, steps)
    tip = _eixo(lg, Pena(p.ang, p.length * 1.06, p.half_w, p.droop * 1.1), 1.0)
    body = up + [(tip[0], tip[1])] + lo[::-1]
    c.b.part(pid, tons.body, polygon(lg.origin, [[q(x), q(z)] for x, z in body]),
             Parte(bone=lg.bone, group=c.grupo, tags=("flat", "no_inner_outline")))
    shade = [(lg.x + (x - lg.x) * 0.88 + 1.5 * K, lg.z + (z - lg.z) * 0.88 - 1.5 * K) for x, z in body]
    c.b.part(f"{pid}_drop", tons.drop, polygon(lg.origin, [[q(x), q(z)] for x, z in shade]),
             Parte(bone=lg.bone, group=c.grupo, tags=("flat", "no_inner_outline", "no_outline", "no_cast")))
    c.regras.append({"front": pid, "back": f"{pid}_drop"})
    o = lg.origin
    for side, edge, mat in (("up", up, tons.upper), ("lo", lo, tons.lower)):
        pts: list[list[int]] = []
        for i in range(1, steps - 1, 2):
            sx, sz, _, _ = _eixo(lg, p, i / steps)
            ex, ez = sx + (edge[i + 1][0] - sx) * 0.8, sz + (edge[i + 1][1] - sz) * 0.8  # o contorno fica limpo
            pts += [[o[0] + q(sx), o[1], o[2] + q(sz)], [o[0] + q(ex), o[1], o[2] + q(ez)]]
        if len(pts) >= 2:
            c.b.part(f"{pid}_{side}", mat, polyline(pts, 1), Parte(bone=lg.bone, group=c.grupo, tags=LINE))
            c.regras.append({"front": f"{pid}_{side}", "back": pid})


@dataclass(frozen=True)
class Tira:
    """A tira pendente: o comprimento, a largura no alto e a curva para o lado no fim (px)."""

    length: float
    width: float
    bend: float


def strand(c: Ctx, pid: str, lg: Lugar, t: Tira, tons: Tons) -> None:
    """A tira que cai e afina até a franja, com as bordas serrilhadas (as folhas estreitas), a borda da direita em
    sombra e, na tira comprida, a ponta clara (a luz pega a franja)."""
    steps = max(3, int(t.length / (2 * K)))
    left, right, edge = [], [], []
    for i in range(steps + 1):
        f = i / steps
        x, z, w = lg.x + t.bend * f * f, lg.z - t.length * f, t.width * (1 - 0.8 * f * f)
        jl = (0.5 if i % 2 else 0.0) * K * c.st.randint(60, 100) / 100
        jr = (0.5 if (i + 1) % 2 else 0.0) * K * c.st.randint(60, 100) / 100
        left.append((x - w / 2 - jl, z))
        right.append((x + w / 2 + jr, z))
        edge.append((x + w / 2 - 0.4 * K, z))
    o = lg.origin
    c.b.part(pid, tons.core, polygon(o, [[q(x), q(z)] for x, z in left + right[::-1]]),
             Parte(bone=lg.bone, group=c.grupo, tags=("flat", "no_inner_outline")))
    c.b.part(f"{pid}_s", tons.shade, polyline([[o[0] + q(x), o[1], o[2] + q(z)] for x, z in edge], 1),
             Parte(bone=lg.bone, group=c.grupo, tags=LINE))
    c.regras.append({"front": f"{pid}_s", "back": pid})
    if t.length > 10 * K:
        n = max(2, steps // 4)
        tip = [left[i] for i in range(steps - n, steps + 1)] + [right[i] for i in range(steps, steps - n - 1, -1)]
        c.b.part(f"{pid}_t", tons.lit, polygon(o, [[q(x), q(z)] for x, z in tip]),
                 Parte(bone=lg.bone, group=c.grupo, tags=("flat", "no_inner_outline")))
        c.regras.append({"front": f"{pid}_t", "back": pid})
