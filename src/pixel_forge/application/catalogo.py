"""O catálogo do kit: para que serve cada peça, o schema dos argumentos e a prancha das 3 variações, no estilo do jogo.
Só existe o vigente: a peça substituída não está no registro."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from ..contracts.carregar import validar
from ..contracts.composicao import Composicao
from ..design.asset import ir_da_composicao
from ..design.kit.registro import PECAS
from ..export.imagem import salvar_png
from ..raster.estilo import estilo_render
from .estilo import estilo_base
from .quadros import quadro_de_repouso

FUNDO = (112, 116, 104, 255)  # o tom médio do chão, para a prancha ler como no jogo
AMPLIA = 3


def de_uma_peca(peca: str, args: dict[str, Any]) -> Composicao:
    """Uma composição de um nó só, na vista S (a prancha e o teste da peça)."""
    tipo = PECAS[peca].tipo
    return validar({"id": "kit_peca", "revision": 1, "description": f"A peça {peca} sozinha",
                    "reference": "o catálogo do kit", "tipo": tipo, "categoria": "objeto", "semente": 11,
                    "nos": [{"id": "n", "peca": peca, "args": args}], "vistas": {"S": {}}, "movimento": ["static"],
                    "tracos": []}, Composicao, f"variação de {peca}")


def _rgba_da_variacao(peca: str, args: dict[str, Any]) -> np.ndarray[Any, np.dtype[np.uint8]]:
    style = estilo_base()
    q = quadro_de_repouso(ir_da_composicao(de_uma_peca(peca, args)), estilo_render(style), "S")
    rgba = q.to_rgba({p.index: (p.rgba[0], p.rgba[1], p.rgba[2], p.rgba[3]) for p in style.palette})
    fundo = np.empty_like(rgba)
    fundo[...] = FUNDO
    fundo[rgba[..., 3] == 255] = rgba[rgba[..., 3] == 255]
    return np.repeat(np.repeat(fundo, AMPLIA, axis=0), AMPLIA, axis=1)


def _prancha(peca: str, destino: Path) -> Path:
    imagens = [_rgba_da_variacao(peca, args) for _, args in PECAS[peca].variacoes]
    alto = max(i.shape[0] for i in imagens)
    linha = np.zeros((alto, sum(i.shape[1] for i in imagens) + 4 * (len(imagens) - 1), 4), dtype=np.uint8)
    x = 0
    for img in imagens:
        linha[alto - img.shape[0]:, x:x + img.shape[1]] = img
        x += img.shape[1] + 4
    alvo = destino / f"{peca}.png"
    salvar_png(alvo, linha)
    return alvo


def catalogo(destino: Path) -> Path:
    """O ``index.json`` (cada peça com a descrição, os argumentos, as vistas, as âncoras e a prancha) e as pranchas."""
    pecas = []
    for pid, p in sorted(PECAS.items()):
        pecas.append({"id": pid, "tipo": p.tipo, "descricao": p.descricao, "vistas": list(p.vistas),
                      "ancoras": list(p.ancoras), "variacoes": [n for n, _ in p.variacoes],
                      "args": [{"nome": a.nome, "tipo": a.tipo, "descricao": a.descricao, "padrao": a.padrao}
                               for a in p.args],
                      "prancha": _prancha(pid, destino).name})
    alvo = destino / "index.json"
    alvo.write_text(json.dumps({"pecas": pecas, "materiais": [m.id for m in estilo_base().materials]},
                               ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return alvo
