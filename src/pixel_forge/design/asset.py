"""A composição vira a IR do asset: validada pelo tipo dela, montada só com peças do kit. O que a composição pede e a
engine não faz é recusado aqui, com a medida e a dica (o tamanho do sprite, a parte que o traço cita); a IR que ainda
assim sai inválida é defeito do motor, e a recusa diz isso."""

from __future__ import annotations

import difflib
from typing import Any

from ..contracts.carregar import validar
from ..contracts.composicao import Composicao
from ..contracts.ir import MAX_CANVAS, AssetIR
from ..core.recusa import Recusa
from .escala import PPM
from .humano import clipes, ir_do_humano, movimento_do_humano, validar_humano
from .prop import ir_do_prop, movimento_do_prop, validar_prop
from .quadrupede import clipes as clipes_do_quadrupede
from .quadrupede import ir_do_quadrupede, movimento_do_quadrupede, validar_quadrupede


def ir_da_composicao(comp: Composicao) -> AssetIR:
    if comp.tipo == "humanoide":
        validar_humano(comp)
        dado = ir_do_humano(comp)
    elif comp.tipo == "quadrupede":
        validar_quadrupede(comp)
        dado = ir_do_quadrupede(comp)
    else:
        validar_prop(comp)
        dado = ir_do_prop(comp)
    _conferir_tamanho(comp, dado["canvas"])
    _conferir_tracos(comp, [p["id"] for p in dado["parts"]])
    try:
        return validar(dado, AssetIR, f"IR de '{comp.id}'")
    except Recusa as r:
        raise Recusa("MOTOR", f"A engine montou uma IR inválida para '{comp.id}': {r.mensagem}",
                     "É defeito do motor, não da composição: pare e registre a composição e esta mensagem.",
                     r.onde) from None


def _conferir_tamanho(comp: Composicao, canvas: dict[str, Any]) -> None:
    w, h = canvas["width"], canvas["height"]
    if max(w, h) > MAX_CANVAS:
        raise Recusa("TAMANHO", f"'{comp.id}' mede {w}×{h} px na tela (com a folga do canvas e a sombra no chão); o "
                     f"sprite vai até {MAX_CANVAS}×{MAX_CANVAS}.", f"A escala é {PPM:.1f} px por metro (o humano de "
                     "1,65 m tem 54 px): confira as medidas em metros, ou faça o asset em partes menores.", "/medidas")


def _conferir_tracos(comp: Composicao, partes: list[str]) -> None:
    for i, t in enumerate(comp.tracos):
        for j, pid in enumerate(t.parts):
            if pid not in partes:
                perto = difflib.get_close_matches(pid, partes, 4, 0.4)
                todas = ", ".join(partes[:80]) + (" ..." if len(partes) > 80 else "")
                raise Recusa("TRACO", f"O traço '{t.id}' cita a parte '{pid}', que o asset não tem.",
                             f"Parecidas: {', '.join(perto) or 'nenhuma'}. As partes do asset: {todas}.",
                             f"/tracos/{i}/parts/{j}")


def movimento(comp: Composicao) -> tuple[dict[str, str], dict[str, int]]:
    """Os clipes que o build gera (o clipe e a receita) e os parâmetros do movimento; o prop é o estático."""
    if comp.tipo == "humanoide":
        return clipes(comp), movimento_do_humano(comp)
    if comp.tipo == "quadrupede":
        return clipes_do_quadrupede(comp), movimento_do_quadrupede(comp)
    return movimento_do_prop(comp)
