"""Os ossos de um modelo de rig (``dados/rigs``) nas medidas do corpo: as expressões de posição, comprimento e repouso
avaliadas em px, o pai que existe e os limites em miligraus."""

from __future__ import annotations

from ...rig.modelo import modelo
from ..construtor import AssetBuilder, Junta, q, qv
from ..expressao import valor


def monta(b: AssetBuilder, nome: str, medidas: dict[str, float]) -> None:
    presentes: set[str] = set()
    for o in modelo(nome).ossos:
        env = {**medidas, "lado": float(o.lado)}
        pai = next((p for p in o.pai if p in presentes), None)
        pos = qv(*(valor(t, env) for t in o.pos))
        b.bone(o.id, pai, pos, Junta(o.eixo, q(valor(o.comp, env)), (o.limites[0] * 1000, o.limites[1] * 1000),
                                     round(valor(o.repouso, env))))
        presentes.add(o.id)
