"""O registro das peças do kit: ``PECAS[id]``. Uma peça nova só entra quando uma ficha pede uma forma que o kit não
faz, com schema, prancha (3 variações) e teste; o registro recusa a peça acima do teto (12 argumentos, 250 linhas)."""

from __future__ import annotations

import inspect

from .peca import MAX_ARGS, MAX_LINHAS, Peca
from .pecas_carpintaria import PECAS_CARPINTARIA
from .pecas_copa import PECAS_COPA
from .pecas_ervas import PECAS_ERVAS
from .pecas_formas import PECAS_FORMAS
from .pecas_humano import PECAS_HUMANO
from .pecas_madeira import PECAS_MADEIRA
from .pecas_pedra import PECAS_PEDRA
from .pecas_quadrupede import PECAS_QUADRUPEDE
from .pecas_rocha import PECAS_ROCHA
from .pecas_telhado import PECAS_TELHADO
from .pecas_tronco import PECAS_TRONCO
from .pecas_vaos import PECAS_VAOS


def conferida(p: Peca) -> Peca:
    """A peça, se cabe no teto e tem a prancha; senão, o erro de quem a escreveu (não do pedido)."""
    linhas = sum(len(inspect.getsource(f).splitlines()) for f in {p.desenha, *p.funcoes})
    if len(p.args) > MAX_ARGS or linhas > MAX_LINHAS or len(p.variacoes) < 3:
        raise ValueError(f"peça '{p.id}': {len(p.args)} argumentos, {linhas} linhas, {len(p.variacoes)} variações "
                         f"(teto: {MAX_ARGS}, {MAX_LINHAS}, pelo menos 3)")
    return p


# as famílias do kit: quem faz um tipo de asset lê só a dele no catálogo
_FAMILIAS = {
    "construcao": (*PECAS_MADEIRA, *PECAS_PEDRA, *PECAS_TELHADO, *PECAS_CARPINTARIA, *PECAS_VAOS),
    "formas": (*PECAS_FORMAS,), "flora": (*PECAS_TRONCO, *PECAS_COPA, *PECAS_ERVAS), "rocha": (*PECAS_ROCHA,),
    "humano": (*PECAS_HUMANO,), "quadrupede": (*PECAS_QUADRUPEDE,),
}
PECAS: dict[str, Peca] = {p.id: conferida(p) for pecas in _FAMILIAS.values() for p in pecas}
FAMILIAS: dict[str, tuple[str, ...]] = {f: tuple(sorted(p.id for p in pecas)) for f, pecas in _FAMILIAS.items()}
