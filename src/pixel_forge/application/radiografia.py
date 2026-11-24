"""A radiografia do modelo: o asset ampliado (até 4×, pela geometria, não pelo pixel), no repouso, em elevação (a
frente, o perfil e as costas sem a câmera do jogo: a altura inteira, a profundidade nula) e, na fileira de baixo, na
câmera do jogo. É como se analisa a forma: a 47 px um rosto tem 5 px, e o defeito do modelo se confunde com a perda da
redução. Do humano saem também as medidas do corpo, cada uma com a faixa do corpo real (``quality.anatomia``).

A lente da elevação é só de diagnóstico: nenhum quadro do build passa por ela.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import numpy as np

from ..contracts.base import Direcao
from ..contracts.carregar import validar
from ..contracts.composicao import Composicao
from ..contracts.ir import MAX_CANVAS, AssetIR
from ..core.recusa import Recusa
from ..design.asset import ir_da_composicao
from ..export.imagem import salvar_png
from ..quality.anatomia import medidas_do_humano
from ..raster.estilo import EstiloRender, estilo_render
from ..raster.grade import Mascara
from ..raster.renderer import mascaras
from ..rig.fk import Skeleton
from ..rig.pose import rest_pose
from ..views.projetor import project_view
from .estilo import estilo_base
from .prancha import Rgba, grade
from .quadros import quadro_de_repouso

ELEVACAO = (0, 0)  # a lente sem a câmera: a elevação de 0° e a profundidade nula
VISTAS = ("S", "W", "N")  # a frente, o perfil e as costas (as que o asset tiver)
FOLGA = 1.42  # 1 / cos 45°: na elevação a altura não é achatada, e o alto do canvas cresce com ela
# os campos da IR em px ou q8 que crescem com o asset
ESCALAM = frozenset({"rest_translation_q8", "length_q8", "origin_q8", "vertices_q8", "stations", "center_q8",
                     "radii_q8", "points_q8", "thickness_px", "point_q8", "pivot_px", "width", "height"})


def _vezes(v: Any, k: int) -> Any:
    if isinstance(v, list):
        return [_vezes(x, k) for x in v]
    return v * k if isinstance(v, int) and not isinstance(v, bool) else v


def _ampliar(dado: Any, k: int) -> Any:
    """A IR (em dicionário) com toda medida ``k`` vezes maior."""
    if isinstance(dado, list):
        return [_ampliar(x, k) for x in dado]
    if not isinstance(dado, dict):
        return dado
    return {c: _vezes(v, k) if c in ESCALAM else {p: b * k for p, b in v.items()} if c == "depth_bias"
            else _ampliar(v, k) for c, v in dado.items()}


def ampliada(ir: AssetIR) -> tuple[AssetIR, int]:
    """A IR na maior ampliação (de 4 a 1) que cabe nos limites do motor, com o alto do canvas folgado para a
    elevação."""
    for k in (4, 3, 2, 1):
        dado = _ampliar(ir.model_dump(mode="json"), k)
        canvas = dado["canvas"]
        sobe = min(math.ceil(canvas["pivot_px"][1] * FOLGA), MAX_CANVAS - (canvas["height"] - canvas["pivot_px"][1]))
        canvas["height"] += sobe - canvas["pivot_px"][1]
        canvas["pivot_px"][1] = sobe
        try:
            return validar(dado, AssetIR, "radiografia"), k
        except Recusa:
            continue
    return ir, 1


def _mascaras(ir: AssetIR, est: EstiloRender, vista: Direcao) -> dict[str, Mascara]:
    """A máscara inteira de cada parte na elevação da vista, com as que a vista esconde (o corpo sob a roupa)."""
    nua = ir.model_copy(update={"views": {d: v.model_copy(update={"visibility": {}}) for d, v in ir.views.items()}})
    cena = project_view(nua, rest_pose(Skeleton(nua.bones)), vista, ELEVACAO)
    return mascaras(cena, est, nua.canvas.width, nua.canvas.height)


def anatomia(ir: AssetIR, est: EstiloRender) -> list[dict[str, Any]]:
    """As medidas do corpo do humano, de frente e de perfil, na elevação (``ir``: a IR ampliada)."""
    return medidas_do_humano(_mascaras(ir, est, "S"), _mascaras(ir, est, "W"))


def _no_recorte(fileiras: list[list[Rgba]]) -> list[list[Rgba]]:
    """Os quadros no mesmo recorte: a caixa de tudo o que é opaco em algum deles, com 4 px de folga."""
    opaco = np.logical_or.reduce([q[..., 3] == 255 for f in fileiras for q in f])
    ys, xs = np.nonzero(opaco.any(axis=1))[0], np.nonzero(opaco.any(axis=0))[0]
    y0, x0 = max(0, int(ys.min()) - 4), max(0, int(xs.min()) - 4)
    return [[q[y0:int(ys.max()) + 5, x0:int(xs.max()) + 5] for q in f] for f in fileiras]


def radiografia(comp: Composicao, acervo: Path) -> dict[str, Any]:
    style = estilo_base()
    est = estilo_render(style)
    pal = {p.index: (p.rgba[0], p.rgba[1], p.rgba[2], p.rgba[3]) for p in style.palette}
    ir, k = ampliada(ir_da_composicao(comp))
    vistas = [d for d in ir.views if d in VISTAS]
    fileiras = [[quadro_de_repouso(ir, est, d, lente).to_rgba(pal) for d in vistas] for lente in (ELEVACAO, None)]
    alvo = acervo / "radiografias" / f"{comp.id}.r{comp.revision}.png"
    salvar_png(alvo, grade(_no_recorte(fileiras), 1))
    out: dict[str, Any] = {"prancha": str(alvo), "amplia": k, "vistas": vistas,
                           "fileiras": ["elevação (sem a câmera do jogo)", "câmera do jogo"]}
    if comp.tipo == "humanoide":
        out["medidas"] = anatomia(ir, est)
    return out
