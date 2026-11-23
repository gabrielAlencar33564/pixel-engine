"""A composição vira a IR do asset: validada pelo tipo dela, montada só com peças do kit."""

from __future__ import annotations

from ..contracts.carregar import validar
from ..contracts.composicao import Composicao
from ..contracts.ir import AssetIR
from .prop import ir_do_prop, validar_prop


def ir_da_composicao(comp: Composicao) -> AssetIR:
    validar_prop(comp)
    return validar(ir_do_prop(comp), AssetIR, f"IR de '{comp.id}'")
