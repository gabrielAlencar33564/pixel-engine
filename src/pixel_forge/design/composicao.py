"""A composição antes de montar: as medidas em ordem, a repetição dos nós, a semente de cada nó e as recusas além do
schema (a peça que o kit não tem, o argumento fora do schema, a medida não declarada, a âncora fora de ordem).

- **Semente por nó:** cada nó (e cada repetição dele) sorteia com a própria semente, tirada da semente do asset e do
  id; mexer num nó não muda o sorteio dos outros.
- **Âncoras:** um nó cita o ponto que um nó de antes deixou (``'<nó>.<âncora>'``, as pontas dos galhos).
"""

from __future__ import annotations

import hashlib
import math
from typing import Any

from ..contracts.composicao import Composicao, No
from ..core.recusa import Recusa
from .expressao import compilar, valor, variaveis
from .kit.peca import Peca, ancoras_pedidas, vars_dos_args
from .kit.registro import PECAS

VARS_REPETICAO = {"linha": {"i", "n", "t"}, "lados": {"i", "n", "lado"}, "anel": {"i", "n", "cos", "sen"}}


def semente_do_no(semente: int, pid: str) -> int:
    return int.from_bytes(hashlib.sha256(f"{semente}/{pid}".encode()).digest()[:4], "big")


def repeticoes(no: No) -> list[tuple[str, dict[str, float]]]:
    if no.repete is None:
        return [(no.id, {})]
    n = no.repete.n
    out = []
    for i in range(n):
        v: dict[str, float] = {"i": float(i), "n": float(n)}
        if no.repete.sobre == "linha":
            v["t"] = i / (n - 1) if n > 1 else 0.0
        elif no.repete.sobre == "lados":
            v["lado"] = -1.0 if i == 0 else 1.0
        else:
            a = 2 * math.pi * i / n
            v["cos"], v["sen"] = math.cos(a), math.sin(a)
        out.append((f"{no.id}_{i}", v))
    return out


def medidas(comp: Composicao) -> dict[str, float]:
    env: dict[str, float] = {}
    for nome, texto in comp.medidas.items():
        env[nome] = valor(texto, env, f"/medidas/{nome}")
    return env


def _faltam(textos: list[Any], conhecidas: set[str], onde: str) -> set[str]:
    out: set[str] = set()
    for t in textos:
        if isinstance(t, str):
            out |= variaveis(compilar(t, onde)) - conhecidas
    return out


def conferir_medidas(comp: Composicao) -> set[str]:
    """As medidas em ordem: cada uma usa só as de cima. Devolve os nomes declarados."""
    conhecidas: set[str] = set()
    for nome, texto in comp.medidas.items():
        falta = _faltam([texto], conhecidas, f"/medidas/{nome}")
        if falta:
            raise Recusa("EXPRESSAO", f"A medida '{nome}' usa {', '.join(sorted(falta))} antes de declarar.",
                         "Declare a medida antes de quem a usa (a ordem do arquivo vale).", f"/medidas/{nome}")
        conhecidas.add(nome)
    for nome, ponto in comp.landmarks.items():
        falta = _faltam(list(ponto), conhecidas, f"/landmarks/{nome}")
        if falta:
            raise Recusa("EXPRESSAO", f"O ponto '{nome}' usa {', '.join(sorted(falta))}.", "Declare em 'medidas'.",
                         f"/landmarks/{nome}")
    return conhecidas


def _peca(no: No, onde: str, tipo: str) -> Peca:
    peca = PECAS.get(no.peca)
    if peca is None or peca.tipo != tipo:
        nomes = ", ".join(sorted(k for k, p in PECAS.items() if p.tipo == tipo))
        raise Recusa("PECA", f"Nó '{no.id}': a peça '{no.peca}' não existe no kit do {tipo}.",
                     f"Peças: {nomes}. A forma que o kit não faz vira peça nova do kit.", f"{onde}/peca")
    return peca


def conferir_no(no: No, onde: str, contexto: dict[str, Any]) -> Peca:
    """O nó contra o kit: a peça do tipo, as vistas que ela desenha, as âncoras deixadas antes e as medidas que os
    argumentos usam. ``contexto``: o tipo, as vistas, as medidas conhecidas e as âncoras já deixadas."""
    peca = _peca(no, onde, contexto["tipo"])
    if no.repete and no.repete.sobre == "lados" and no.repete.n != 2:
        raise Recusa("REPETICAO", f"Nó '{no.id}': 'lados' repete 2 vezes.", "Use n = 2.", f"{onde}/repete/n")
    nao_faz = [v for v in contexto["vistas"] if v not in peca.vistas]
    if nao_faz:
        raise Recusa("VISTA", f"Nó '{no.id}': a peça '{no.peca}' desenha só a(s) vista(s) {', '.join(peca.vistas)}; "
                     f"a composição pede {', '.join(nao_faz)}.",
                     "Declare só as vistas que todas as peças desenham, ou troque a peça.", f"{onde}/peca")
    for ref in ancoras_pedidas(peca, no.args):
        if ref not in contexto["deixadas"]:
            raise Recusa("ANCORA", f"Nó '{no.id}': a âncora '{ref}' não foi deixada por um nó de antes.",
                         "Cite '<nó>.<âncora>' de um nó acima cuja peça deixa a âncora (veja `pfe catalogo`).",
                         f"{onde}/args")
    contexto["deixadas"].update(f"{no.id}.{a}" for a in peca.ancoras)
    nomes = {a.nome for a in peca.args}
    sobra = sorted(set(no.args) - nomes)
    if sobra:
        raise Recusa("ARGUMENTO", f"Peça '{no.peca}': argumento desconhecido {', '.join(sobra)} (aceita: "
                     f"{', '.join(sorted(nomes))}).", "Veja o schema da peça em `pfe catalogo`.",
                     f"{onde}/args/{sobra[0]}")
    rep = VARS_REPETICAO[no.repete.sobre] if no.repete else set()
    falta = vars_dos_args(peca, no.args) - contexto["conhecidas"] - rep
    if falta:
        raise Recusa("EXPRESSAO", f"O nó '{no.id}' usa {', '.join(sorted(falta))}, que não foi declarada.",
                     "Declare em 'medidas' ou use a variável da repetição "
                     f"({', '.join(sorted(rep)) or 'sem repetição'}).", f"{onde}/args")
    return peca


def conferir_nos(comp: Composicao, conhecidas: set[str]) -> None:
    contexto: dict[str, Any] = {"tipo": comp.tipo, "vistas": list(comp.vistas), "conhecidas": conhecidas,
                                "deixadas": set()}
    ids: set[str] = set()
    for i, no in enumerate(comp.nos):
        if no.id in ids:
            raise Recusa("NO", f"O nó '{no.id}' está repetido.", "Cada nó tem id próprio; para repetir a peça, use "
                         "'repete'.", f"/nos/{i}/id")
        ids.add(no.id)
        conferir_no(no, f"/nos/{i}", contexto)
