"""O catálogo do kit: para que serve cada peça, o schema dos argumentos e a prancha das 3 variações, no estilo do jogo.
Só existe o vigente: a peça substituída não está no registro."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..contracts.carregar import validar
from ..contracts.composicao import Composicao
from ..core.direcoes import DIRECOES
from ..design.asset import ir_da_composicao
from ..design.kit.registro import PECAS
from ..export.imagem import salvar_png
from ..raster.estilo import estilo_render
from .estilo import estilo_base
from .prancha import grade
from .quadros import quadro_de_repouso

AMPLIA = 3


def de_uma_peca(peca: str, args: dict[str, Any]) -> Composicao:
    """Uma composição de um nó só, na vista S (a prancha e o teste da peça); a roupa, no corpo de madeira."""
    if PECAS[peca].tipo == "humanoide":
        nos = [{"id": "corpo", "peca": "corpo_humano", "args": args if peca == "corpo_humano" else {}}]
        nos += [] if peca == "corpo_humano" else [{"id": "n", "peca": peca, "args": args}]
        return validar({"id": "kit_peca", "revision": 1, "description": f"A peça {peca} no corpo de madeira",
                        "reference": "o catálogo do kit", "tipo": "humanoide", "categoria": "humano", "semente": 11,
                        "nos": nos, "vistas": dict.fromkeys(DIRECOES, {}), "movimento": ["idle"], "tracos": []},
                       Composicao, f"variação de {peca}")
    if PECAS[peca].tipo == "quadrupede":
        return validar({"id": "kit_peca", "revision": 1, "description": f"O corpo {peca}",
                        "reference": "o catálogo do kit", "tipo": "quadrupede", "categoria": "quadrupede",
                        "semente": 11,
                        "nos": [{"id": "corpo", "peca": peca, "args": args}], "vistas": dict.fromkeys(DIRECOES, {}),
                        "movimento": ["idle"], "tracos": []}, Composicao, f"variação de {peca}")
    return validar({"id": "kit_peca", "revision": 1, "description": f"A peça {peca} sozinha",
                    "reference": "o catálogo do kit", "tipo": "prop", "categoria": "objeto", "semente": 11,
                    "nos": [{"id": "n", "peca": peca, "args": args}], "vistas": {"S": {}}, "movimento": ["static"],
                    "tracos": []}, Composicao, f"variação de {peca}")


def _prancha(peca: str, destino: Path) -> Path:
    """As 3 variações da peça, a 3×, na vista S."""
    style = estilo_base()
    est, pal = estilo_render(style), {p.index: (p.rgba[0], p.rgba[1], p.rgba[2], p.rgba[3]) for p in style.palette}
    imagens = [quadro_de_repouso(ir_da_composicao(de_uma_peca(peca, args)), est, "S").to_rgba(pal)
               for _, args in PECAS[peca].variacoes]
    alvo = destino / f"{peca}.png"
    salvar_png(alvo, grade([imagens], AMPLIA))
    return alvo


def catalogo(destino: Path) -> Path:
    """O ``index.json`` (cada peça com a descrição, os argumentos, as vistas, as âncoras e a prancha) e as pranchas."""
    pecas = []
    for pid, p in sorted(PECAS.items()):
        pecas.append({"id": pid, "tipo": p.tipo, "descricao": p.descricao, "vistas": list(p.vistas),
                      "ancoras": list(p.ancoras), "variacoes": [{"nome": n, "args": args} for n, args in p.variacoes],
                      "args": [{"nome": a.nome, "tipo": a.tipo, "descricao": a.descricao, "padrao": a.padrao}
                               for a in p.args],
                      "prancha": _prancha(pid, destino).name})
    alvo = destino / "index.json"
    alvo.write_text(json.dumps({"pecas": pecas, "materiais": [m.id for m in estilo_base().materials]},
                               ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return alvo
