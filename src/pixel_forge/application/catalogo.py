"""O catálogo do kit, em dois níveis: o resumo (as famílias, as peças e para que serve cada uma) e, por família, o
schema dos argumentos, as variações, as partes e a prancha de cada peça, no estilo do jogo. Só existe o vigente: a
peça substituída não está no registro."""

from __future__ import annotations

import json
import re
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from ..contracts.carregar import validar
from ..contracts.composicao import Composicao
from ..core.direcoes import DIRECOES
from ..core.recusa import Recusa
from ..design.asset import ir_da_composicao
from ..design.kit.registro import FAMILIAS, PECAS
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
    apoio_da_peca = PECAS[peca].apoio
    apoio = [{"id": i, "peca": p, "args": a}
             for i, p, a in (apoio_da_peca(args) if callable(apoio_da_peca) else apoio_da_peca)]
    return validar({"id": "kit_peca", "revision": 1, "description": f"A peça {peca} sozinha",
                    "reference": "o catálogo do kit", "tipo": "prop", "categoria": "objeto", "semente": 11,
                    "nos": [*apoio, {"id": "n", "peca": peca, "args": args}], "vistas": {"S": {}},
                    "movimento": ["static"], "tracos": []}, Composicao, f"variação de {peca}")


def _prancha(peca: str, destino: Path) -> Path:
    """As 3 variações da peça, a 3×, na vista S."""
    style = estilo_base()
    est, pal = estilo_render(style), {p.index: (p.rgba[0], p.rgba[1], p.rgba[2], p.rgba[3]) for p in style.palette}
    imagens = [quadro_de_repouso(ir_da_composicao(de_uma_peca(peca, args)), est, "S").to_rgba(pal)
               for _, args in PECAS[peca].variacoes]
    alvo = destino / f"{peca}.png"
    salvar_png(alvo, grade([imagens], AMPLIA))
    return alvo


def em_faixas(ids: Sequence[str]) -> list[str]:
    """Os ids com as sequências numeradas de 3 ou mais numa faixa só (``copa_00..copa_29``): a lista de partes de
    uma copa tem dezenas de ids que só mudam no número."""
    out: list[str] = []
    i = 0
    while i < len(ids):
        j = i
        m = re.fullmatch(r"(.*?)(\d+)", ids[i])
        while m and j + 1 < len(ids) and ids[j + 1] == f"{m[1]}{int(m[2]) + j + 1 - i:0{len(m[2])}d}":
            j += 1
        out += [f"{ids[i]}..{ids[j]}"] if j - i >= 2 else list(ids[i:j + 1])
        i = j + 1
    return out


def _registro(pid: str, destino: Path) -> dict[str, Any]:
    """A peça inteira: a descrição, os argumentos, as variações, as partes, as âncoras e a prancha (gravada)."""
    p = PECAS[pid]
    partes = [pt.id for pt in ir_da_composicao(de_uma_peca(pid, p.variacoes[0][1])).parts]
    return {"id": pid, "tipo": p.tipo, "descricao": p.descricao, "vistas": list(p.vistas),
            "ancoras": list(p.ancoras), "variacoes": [{"nome": n, "args": args} for n, args in p.variacoes],
            "args": [{"nome": a.nome, "tipo": a.tipo, "descricao": a.descricao, "padrao": a.padrao} for a in p.args],
            "partes": em_faixas(partes), "prancha": _prancha(pid, destino).name}


def _linhas(itens: Sequence[Any]) -> str:
    """Uma lista em JSON, um item por linha e sem espaço a mais: quem lê o arquivo paga por caractere."""
    return "[\n" + ",\n".join(json.dumps(i, ensure_ascii=False, separators=(",", ":")) for i in itens) + "\n]"


def catalogo(destino: Path, familias: Sequence[str] = ()) -> dict[str, Any]:
    """O catálogo em dois níveis: o ``index.json`` (o resumo: cada família com as peças dela, a descrição de cada
    uma e os materiais do estilo) e um ``<família>.json`` com as peças inteiras e as pranchas, só das famílias
    pedidas (todas, sem pedido). Quem faz uma planta lê o resumo e a flora, não o kit inteiro."""
    estranhas = [f for f in familias if f not in FAMILIAS]
    if estranhas:
        raise Recusa("FAMILIA", f"O kit não tem a família {', '.join(estranhas)}.",
                     f"As famílias são {', '.join(FAMILIAS)}; sem nenhuma, o catálogo grava todas.")
    arquivos = {}
    for familia in familias or FAMILIAS:
        alvo = destino / f"{familia}.json"
        alvo.write_text(_linhas([_registro(pid, destino) for pid in FAMILIAS[familia]]) + "\n", encoding="utf-8")
        arquivos[familia] = str(alvo)
    resumo = [{"familia": f, "pecas": {pid: PECAS[pid].descricao for pid in ids}} for f, ids in FAMILIAS.items()]
    index = destino / "index.json"
    index.write_text('{"familias":' + _linhas(resumo) + ',\n"materiais":'
                     + json.dumps([m.id for m in estilo_base().materials]) + "}\n", encoding="utf-8")
    return {"index": str(index), "familias": arquivos}
