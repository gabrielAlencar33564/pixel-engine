"""A composição vira a IR do asset: validada pelo tipo dela, montada só com peças do kit."""

from __future__ import annotations

from ..contracts.carregar import validar
from ..contracts.composicao import Composicao
from ..contracts.ir import AssetIR
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
    return validar(dado, AssetIR, f"IR de '{comp.id}'")


def movimento(comp: Composicao) -> tuple[dict[str, str], dict[str, int]]:
    """Os clipes que o build gera (o clipe e a receita) e os parâmetros do movimento; o prop é o estático."""
    if comp.tipo == "humanoide":
        return clipes(comp), movimento_do_humano(comp)
    if comp.tipo == "quadrupede":
        return clipes_do_quadrupede(comp), movimento_do_quadrupede(comp)
    return movimento_do_prop(comp)
