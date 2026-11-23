"""O clipe de uma receita num asset: os papéis pelo modelo de rig dele e o gerador pelo tipo da receita."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ..contracts.carregar import validar
from ..contracts.clipe import Clipe
from ..contracts.ir import AssetIR
from ..core.recusa import Recusa
from ..rig.fk import Skeleton
from ..rig.modelo import Papeis, papeis_do_asset
from .caminhada import passada_poses
from .passo import passada_apoio
from .prop import balanco, giro
from .receita import carregar, parado

Gerador = Callable[[dict[str, Any], Papeis, Skeleton, dict[str, int]], dict[str, Any]]
GERADORES: dict[str, Gerador] = {"parado": parado, "passada_poses": passada_poses, "passada_apoio": passada_apoio}
DO_PROP: dict[str, Callable[[Skeleton, dict[str, int]], dict[str, Any]]] = {"balanco": balanco, "giro": giro}


def gerar_clipe(asset: AssetIR, receita: str, mp: dict[str, int]) -> Clipe:
    if receita in DO_PROP:
        return validar(DO_PROP[receita](Skeleton(asset.bones), mp), Clipe, f"clipe '{receita}'")
    if asset.modelo is None:
        raise Recusa("CLIPE_SEM_RIG", f"O asset '{asset.id}' não tem rig de quem anda; a receita '{receita}' não "
                     "serve.", "O prop tem 'static'; os clipes de andar são do humano.")
    rec = carregar(receita)
    skel = Skeleton(asset.bones)
    dado = GERADORES[rec["tipo"]](rec, papeis_do_asset(asset.modelo, set(skel.bones)), skel, mp)
    return validar(dado, Clipe, f"clipe '{rec['clip']}'")
