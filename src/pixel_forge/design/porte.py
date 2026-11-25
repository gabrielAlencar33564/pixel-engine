"""O porte por categoria, em relação ao humano de 1,65 m (~44 px na tela): a altura do asset no mundo tem de cair na
faixa da categoria dele. Fora dela, a recusa diz o porte esperado: o tamanho vem dos metros, nunca do canvas."""

from __future__ import annotations

from typing import Any

from ..contracts.ir import AssetIR
from ..core.recusa import Recusa
from .escala import ESTATURA_M, PPM
from .vistas import no_mundo, pontos

# (mínimo, máximo, típico) em humanos de 1,65 m
FAIXAS = {
    "arvore_grande": (1.8, 4.0, "~2,5× (~4 m no jogo)"), "arvore_pequena": (1.0, 2.0, "~1,5×"),
    "arbusto": (0.25, 1.0, "~0,6×"), "casa": (1.3, 3.0, "~2×"), "estrutura": (0.3, 2.5, "de 0,3× a 2,5×"),
    "objeto": (0.1, 1.5, "de 0,1× a 1,5×"), "prop_de_mao": (0.03, 0.6, "~0,3×"), "humano": (0.6, 1.25, "~1×"),
    "quadrupede": (0.15, 1.2, "~0,5×"),
}


def _topo(g: dict[str, Any]) -> float:
    """O z mais alto da geometria (px)."""
    if g["type"] == "ellipse":
        return float(g["center_q8"][2] + g["radii_q8"][2]) / 256
    zs = [p[2] for p in pontos(g)]
    if "points_q8" in g:
        zs = [z + g.get("thickness_px", 1) / 2 for z in zs]
    if "stations" in g:
        zs += [(g["origin_q8"][2] + e[0]) / 256 for e in g["stations"]]
    return max(zs, default=0.0)


def altura_m(ir: AssetIR) -> float:
    """A altura do asset em metros: o ponto mais alto da geometria no repouso."""
    d = ir.model_dump(mode="json")
    return max((_topo(p["geometry"]) for p in no_mundo(d["parts"], d["bones"])), default=0.0) / PPM


def conferir_porte(categoria: str, ir: AssetIR) -> None:
    """Recusa o asset cuja altura no mundo cai fora da faixa da categoria, com o porte esperado na dica."""
    lo, hi, tipico = FAIXAS[categoria]
    altura = altura_m(ir)
    rel = altura / ESTATURA_M
    if not lo <= rel <= hi:
        raise Recusa("PORTE", f"'{ir.id}': {altura:.2f} m de altura é {rel:.2f}× o humano de 1,65 m; a categoria "
                     f"'{categoria}' vai de {lo}× a {hi}×.", f"Uma '{categoria}' tem {tipico}: ajuste as medidas em "
                     "metros ou a categoria (o canvas não define o tamanho).", "/categoria")
