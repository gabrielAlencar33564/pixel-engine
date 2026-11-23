"""O registro das peças do kit: ``PECAS[id]``. Uma peça nova só entra quando uma ficha pede uma forma que o kit não
faz, com schema, prancha (3 variações) e teste; o registro recusa a peça acima do teto (12 argumentos, 250 linhas)."""

from __future__ import annotations

import inspect

from .peca import MAX_ARGS, MAX_LINHAS, Peca
from .pecas_carpintaria import PECAS_CARPINTARIA
from .pecas_formas import PECAS_FORMAS
from .pecas_madeira import PECAS_MADEIRA
from .pecas_pedra import PECAS_PEDRA
from .pecas_telhado import PECAS_TELHADO
from .pecas_vaos import PECAS_VAOS


def conferida(p: Peca) -> Peca:
    """A peça, se cabe no teto e tem a prancha; senão, o erro de quem a escreveu (não do pedido)."""
    linhas = sum(len(inspect.getsource(f).splitlines()) for f in {p.desenha, *p.funcoes})
    if len(p.args) > MAX_ARGS or linhas > MAX_LINHAS or len(p.variacoes) < 3:
        raise ValueError(f"peça '{p.id}': {len(p.args)} argumentos, {linhas} linhas, {len(p.variacoes)} variações "
                         f"(teto: {MAX_ARGS}, {MAX_LINHAS}, pelo menos 3)")
    return p


PECAS: dict[str, Peca] = {p.id: conferida(p) for p in (*PECAS_MADEIRA, *PECAS_PEDRA, *PECAS_TELHADO,
                                                        *PECAS_CARPINTARIA, *PECAS_VAOS, *PECAS_FORMAS)}
