"""A conferência dos quadros do build: nada cortado pelo canvas, as cores dentro do limite do estilo e os traços
declarados lendo de fato no sprite (o traço observável tem pixel em alguma vista; o de silhueta, na borda)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np

from ..contracts.composicao import Traco
from ..contracts.estilo import StyleDoc
from ..core.recusa import Recusa
from ..raster.renderer import Quadro

NA_DICA = 16  # as partes que a dica de uma recusa lista


def conferir_quadro(q: Quadro, style: StyleDoc, nome: str) -> None:
    if q.clipping_px:
        e, c, d, b = q.overflow_px
        raise Recusa("QUADRO_CORTADO", f"{nome}: {q.clipping_px} px do desenho saem do canvas (esquerda {e}, cima {c}, "
                     f"direita {d}, baixo {b}).", "Aumente o canvas ou mova o pivô para o desenho caber.")
    cores = len(np.unique(q.index[q.alpha == 255]))
    if cores > style.max_opaque_colors:
        raise Recusa("CORES_DEMAIS", f"{nome}: {cores} cores opacas, o estilo permite {style.max_opaque_colors}.",
                     "Use menos materiais ou materiais com rampas menores.")


def leitura_dos_tracos(tracos: Sequence[Traco], quadros: Mapping[str, Sequence[Quadro]]) -> dict[str, dict[str, int]]:
    """Por traço e por vista, os pixels das partes dele que aparecem (o maior valor entre os quadros da vista)."""
    return {t.id: {v: max(sum(q.visiveis.get(p, 0) for p in t.parts) for q in qs) for v, qs in quadros.items()}
            for t in tracos}


def conferir_tracos(tracos: Sequence[Traco], quadros: Mapping[str, Sequence[Quadro]]) -> None:
    """Recusa o traço observável sem pixel em nenhuma vista e o traço de silhueta que nunca toca a borda da figura."""
    leitura = leitura_dos_tracos(tracos, quadros)
    for i, t in enumerate(tracos):
        partes = ", ".join(t.parts)
        if t.verification == "observable" and not any(leitura[t.id].values()):
            raise Recusa("TRACO_ESCONDIDO", f"O traço '{t.id}' é observável, mas as partes dele ({partes}) não têm "
                         "pixel em nenhuma vista.", "Outra parte as cobre ou elas são pequenas demais: veja "
                         "'escondidas' na prévia e corrija a composição (ou a peça); não declare o que não se vê.",
                         f"/tracos/{i}")
        if t.reads_in_silhouette and not any(q.na_silhueta.get(p, 0) for qs in quadros.values() for q in qs
                                             for p in t.parts):
            na_borda = sorted({p for qs in quadros.values() for q in qs for p in q.na_silhueta})
            raise Recusa("TRACO_SEM_SILHUETA", f"O traço '{t.id}' devia ler na silhueta, mas as partes dele "
                         f"({partes}) não tocam a borda da figura em nenhuma vista.", "Faça a forma sair do "
                         "contorno do corpo, ou tire 'reads_in_silhouette' do traço. Partes na borda: "
                         f"{', '.join(na_borda[:NA_DICA])}{' ...' if len(na_borda) > NA_DICA else ''}.",
                         f"/tracos/{i}")
