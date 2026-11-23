"""A projeção da pose numa vista: cada peça vira um comando de desenho (a primitiva 2D, a profundidade, a superfície
para o z-buffer e a normal da face chapada), na ordem de desenho da vista."""

from __future__ import annotations

import heapq
from dataclasses import dataclass

from ..contracts.base import Direcao
from ..contracts.ir import (
    AssetIR,
    BoundPolygonGeom,
    EllipseGeom,
    Geometry,
    PartDef,
    PolygonGeom,
    PolylineGeom,
    RevolutionGeom,
    StippleGeom,
    TaperedPolylineGeom,
)
from ..core.direcoes import AZIMUTE_MDEG
from ..core.q8 import ONE_PX_POS, Q30_SHIFT, pos_to_q8, q8_to_pos
from ..core.recusa import Recusa
from ..rig.fk import BoneWorld, Vec3i, mat_t_vec, mat_vec, vadd
from ..rig.pose import Pose
from .camera import Camera
from .primitivas import (
    CapsulePrim,
    DrawCommand,
    EllipsePrim,
    FanPrim,
    OrientedEllipsePrim,
    PolygonPrim,
    Prim,
    RevolutionPrim,
    Scene2D,
    StipplePrim,
    SupElipsoide,
    Superficie,
    SupLeque,
    SupPlana,
    SupTubo,
    TaperedPrim,
)


@dataclass(frozen=True)
class _Peca:
    """O que a geometria precisa para ser projetada: a câmera, a pose, o osso da peça e o deslocamento do render."""

    cam: Camera
    pose: Pose
    bw: BoneWorld
    offset: Vec3i

    def no_osso(self, bw: BoneWorld, p: list[int] | Vec3i) -> Vec3i:
        local = (q8_to_pos(p[0]), q8_to_pos(p[1]), q8_to_pos(p[2]))
        return vadd(vadd(bw.pos, mat_vec(bw.rot, local)), self.offset)

    def tela(self, p: list[int] | Vec3i) -> Vec3i:
        return self.cam.project(self.no_osso(self.bw, p))


@dataclass(frozen=True)
class _Projetada:
    prim: Prim
    surface: Superficie
    depth: int
    facing: Vec3i | None = None


def ellipsoid_inverse(m: tuple[float, float, float, float, float, float]
                      ) -> tuple[float, float, float, float, float, float] | None:
    """A inversa simétrica de [[m11 m12 m13] [m12 m22 m23] [m13 m23 m33]] pela adjunta."""
    m11, m12, m13, m22, m23, m33 = m
    c11 = m22 * m33 - m23 * m23
    c12 = m13 * m23 - m12 * m33
    c13 = m12 * m23 - m13 * m22
    det = m11 * c11 + m12 * c12 + m13 * c13
    if det <= 0:
        return None
    c22 = m11 * m33 - m13 * m13
    c23 = m12 * m13 - m11 * m23
    c33 = m11 * m22 - m12 * m12
    return (c11 / det, c12 / det, c13 / det, c22 / det, c23 / det, c33 / det)


def _elipse(g: EllipseGeom, pc: _Peca, orientada: bool) -> _Projetada:
    """A elipse alinhada à tela (a caixa da projeção) ou, com ``oriented``, girada com o osso (a forma exata)."""
    u, v, depth = pc.tela(g.center_q8)
    cam, rot = pc.cam, pc.bw.rot
    prim: EllipsePrim | OrientedEllipsePrim = (
        OrientedEllipsePrim(u, v, *cam.shape_q8(rot, g.radii_q8)) if orientada
        else EllipsePrim(u, v, cam.extent_q8(rot, g.radii_q8, cam.eu), cam.extent_q8(rot, g.radii_q8, cam.ev)))
    w = [mat_t_vec(rot, ax) for ax in (cam.eu, cam.ev, cam.ed)]
    rv = [[r * x for r, x in zip(g.radii_q8, wi, strict=True)] for wi in w]

    def m(i: int, j: int) -> float:
        return float(sum(a * b for a, b in zip(rv[i], rv[j], strict=True))) / float(1 << 60)

    inv = ellipsoid_inverse((m(0, 0), m(0, 1), m(0, 2), m(1, 1), m(1, 2), m(2, 2)))
    surface: Superficie = SupPlana(pos_to_q8(depth)) if inv is None else SupElipsoide(u, v, pos_to_q8(depth), inv)
    return _Projetada(prim, surface, depth)


def _q8(pts: list[Vec3i]) -> tuple[Vec3i, ...]:
    return tuple((p[0], p[1], pos_to_q8(p[2])) for p in pts)


def _afunilada(g: TaperedPolylineGeom, pc: _Peca) -> _Projetada:
    pts = [pc.tela(p) for p in g.points_q8]
    return _Projetada(TaperedPrim(tuple((p[0], p[1]) for p in pts), tuple(g.radii_q8)),
                      SupTubo(_q8(pts), tuple(g.radii_q8)), sum(p[2] for p in pts) // len(pts))


def _polilinha(g: PolylineGeom, pc: _Peca) -> _Projetada:
    pts = [pc.tela(p) for p in g.points_q8]
    raio = g.thickness_px * 128
    return _Projetada(CapsulePrim(tuple((p[0], p[1]) for p in pts), raio), SupTubo(_q8(pts), (raio,) * len(pts)),
                      sum(p[2] for p in pts) // len(pts))


def _plano(g: PolygonGeom | StippleGeom, v: list[int]) -> Vec3i:
    o = g.origin_q8
    if g.plane == "xz":
        return (o[0] + v[0], o[1], o[2] + v[1])
    if g.plane == "yz":
        return (o[0], o[1] + v[0], o[2] + v[1])
    return (o[0] + v[0], o[1] + v[1], o[2])


def _poligono(g: PolygonGeom, pc: _Peca) -> _Projetada:
    pts = [pc.tela(_plano(g, v)) for v in g.vertices_q8]
    return _Projetada(PolygonPrim(tuple((p[0], p[1]) for p in pts)), SupLeque(_q8(pts)),
                      sum(p[2] for p in pts) // len(pts))


def _pontilhado(g: StippleGeom, pc: _Peca) -> _Projetada:
    pts = [pc.tela(_plano(g, v)) for v in g.vertices_q8]
    ou, ov, _ = pc.tela(_plano(g, [0, 0]))
    prim = StipplePrim(tuple((p[0], p[1]) for p in pts), g.density_permille, g.seed, g.cell_px, ou, ov)
    return _Projetada(prim, SupLeque(_q8(pts)), sum(p[2] for p in pts) // len(pts))


def _revolucao(g: RevolutionGeom, pc: _Peca) -> _Projetada:
    o = g.origin_q8
    sts = []
    for z, r, dx in g.stations:
        u, v, d = pc.tela((o[0] + dx, o[1], o[2] + z))
        sts.append((u / 256, v / 256, d / ONE_PX_POS, r / 256, z / 256))
    depth = sum(int(s[2] * ONE_PX_POS) for s in sts) // len(sts)
    prim = RevolutionPrim(tuple(sts), pc.cam.sd / (1 << Q30_SHIFT), pc.cam.ce / (1 << Q30_SHIFT))
    return _Projetada(prim, SupPlana(pos_to_q8(depth)), depth)


def _leque(g: BoundPolygonGeom, pc: _Peca, chapada: bool) -> _Projetada:
    """O polígono de vértices em ossos; a face chapada guarda a normal (a luz e a sombra pelo plano)."""
    body = [pc.no_osso(pc.pose.world[vx.bone_id], vx.point_q8) for vx in g.vertices]
    pts = [pc.cam.project(p) for p in body]
    facing = pc.cam.facing_permille(body) if chapada else None
    return _Projetada(FanPrim(tuple((p[0], p[1]) for p in pts)), SupLeque(_q8(pts)), sum(p[2] for p in pts) // len(pts),
                      facing)


def _projetar(g: Geometry, part: PartDef, pc: _Peca) -> _Projetada:
    if isinstance(g, EllipseGeom):
        return _elipse(g, pc, "oriented" in part.tags)
    if isinstance(g, RevolutionGeom):
        return _revolucao(g, pc)
    if isinstance(g, PolylineGeom):
        return _polilinha(g, pc)
    if isinstance(g, TaperedPolylineGeom):
        return _afunilada(g, pc)
    if isinstance(g, PolygonGeom):
        return _poligono(g, pc)
    if isinstance(g, StippleGeom):
        return _pontilhado(g, pc)
    return _leque(g, pc, "flat" in part.tags)


def _comando(part: PartDef, g: Geometry, pc: _Peca) -> DrawCommand:
    p = _projetar(g, part, pc)
    return DrawCommand(part.id, part.material, part.outline_group, tuple(part.tags), p.depth, p.prim, p.surface,
                       p.facing)


def order_commands(cmds: list[DrawCommand], rules: list[tuple[str, str]], biases: dict[str, int],
                   priorities: dict[str, int], direction: str) -> list[DrawCommand]:
    """Ordena pela profundidade com o viés, a prioridade e o id; as regras frente/trás por topologia estável."""
    base = sorted(cmds, key=lambda c: (c.depth + biases.get(c.part_id, 0), priorities.get(c.part_id, 0), c.part_id))
    if not rules:
        return base
    index = {c.part_id: i for i, c in enumerate(base)}
    succ: dict[str, set[str]] = {c.part_id: set() for c in base}
    indeg = {c.part_id: 0 for c in base}
    for front, back in rules:
        if front in index and back in index and front not in succ[back]:
            succ[back].add(front)
            indeg[front] += 1
    heap = [(index[p], p) for p, d in indeg.items() if d == 0]
    heapq.heapify(heap)
    out: list[DrawCommand] = []
    by_id = {c.part_id: c for c in base}
    while heap:
        _, p = heapq.heappop(heap)
        out.append(by_id[p])
        for q in sorted(succ[p]):
            indeg[q] -= 1
            if indeg[q] == 0:
                heapq.heappush(heap, (index[q], q))
    if len(out) != len(base):
        raise Recusa("OCLUSAO_CICLO", f"As regras de oclusão da vista {direction} formam um ciclo.",
                     "Tire uma das regras frente/trás do ciclo.")
    return out


def project_view(asset: AssetIR, pose: Pose, direction: Direcao) -> Scene2D:
    view = asset.views.get(direction)
    if view is None:
        raise Recusa("VISTA_AUSENTE", f"O asset não declara a vista {direction}.",
                     f"As vistas dele são {', '.join(asset.views)}.")
    cam = Camera(AZIMUTE_MDEG[direction], asset.canvas.pivot_px)
    offset = pose.render_offset_pos()
    cmds = [_comando(part, view.geometria.get(part.id, part.geometry),
                     _Peca(cam, pose, pose.world[part.bone_id], offset))
            for part in asset.parts if part.id not in view.visibility]
    pontos = {lm.id: _Peca(cam, pose, pose.world[lm.bone_id], offset).tela(lm.point_q8) for lm in asset.landmarks}
    rules = [(r.front, r.back) for r in view.occlusion_rules]
    q8bias = {k: q8_to_pos(v) for k, v in view.depth_bias.items()}
    prio = {p.id: p.draw_priority for p in asset.parts}
    ordered = order_commands(cmds, rules, q8bias, prio, direction)
    return Scene2D(direction, AZIMUTE_MDEG[direction], ordered, (cam.pu, cam.pv), dict(view.depth_bias),
                   tuple(rules), pontos)
