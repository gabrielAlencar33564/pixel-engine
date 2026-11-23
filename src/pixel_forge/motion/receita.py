"""As receitas de movimento em dado (``dados/receitas/<receita>.json``): o clipe, o tipo do gerador e as curvas de
cada canal por papel (``"<papel>.<junta>"``, nunca o nome do osso).

O valor de um canal é um inteiro ou ``{"termos": [...], "fator": "escala", "fixo": n}``: a soma dos termos, na ordem,
vezes a escala do corpo (``fator``), arredondada, mais o ``fixo``. Um termo é uma constante (``k``) ou uma amplitude
(``amp``, vezes o parâmetro de movimento ``par`` quando há; ``metros`` dá a amplitude em metros na escala do corpo)
vezes uma onda (``cos``, ``sin`` ou ``vale`` = −(1 − cos)/2, com ``freq`` e ``atraso_ms`` ou ``fase``, ``corte``
``pos``/``neg`` e ``pot``) ou uma curva por chaves (``curva``, sobre o ciclo ou o passo).
"""

from __future__ import annotations

import json
import math
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path
from typing import Any

from ..rig.fk import Skeleton
from ..rig.modelo import Papeis
from .canais import Channels, ClipWriter, bend_guess, q_, rest_ankles, solve_feet

DIR = Path(__file__).resolve().parents[1] / "dados" / "receitas"


@cache
def carregar(nome: str) -> dict[str, Any]:
    dado: dict[str, Any] = json.loads((DIR / f"{nome}.json").read_text(encoding="utf-8"))
    return dado


def _smooth(u: float) -> float:
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)


def chaves(keys: list[Any], u: float) -> float:
    """A interpolação suave entre (u, valor), u em [0, 1]."""
    for (u0, v0), (u1, v1) in zip(keys, keys[1:], strict=False):
        if u0 <= u <= u1:
            return float(v0 + (v1 - v0) * _smooth((u - u0) / (u1 - u0) if u1 > u0 else 1.0))
    return float(keys[-1][1])


@dataclass
class Instante:
    """O que o valor de um canal lê: o tempo, a duração, os parâmetros de movimento, a escala do corpo, a queda do
    quadril, o metro em q8 e as curvas por chaves da receita."""

    t: int
    total: int
    mp: dict[str, int]
    k: float = 1.0
    queda: float = 0.0
    metros: Callable[[float], float] = lambda v: v
    curvas: dict[str, Any] = field(default_factory=dict)

    def curva(self, nome: str) -> float:
        c = self.curvas[nome]
        p = self.t / self.total
        return chaves(c["chaves"], (2 * p) % 1.0 if c["sobre"] == "passo" else p)


def _onda(tm: dict[str, Any], t: int, duracao: int) -> float:
    f = tm.get("freq", 1)
    if "fase" in tm:
        ang = 2 * math.pi * f * (t / duracao - tm["fase"])
    else:
        ang = 2 * math.pi * f * (t - tm.get("atraso_ms", 0)) / duracao
    nome = tm["onda"]
    w = math.cos(ang) if nome == "cos" else math.sin(ang) if nome == "sin" else -(1 - math.cos(ang)) / 2
    if tm.get("corte") == "pos":
        w = max(0.0, w)
    elif tm.get("corte") == "neg":
        w = max(0.0, -w)
    if "pot" in tm:
        w = w ** tm["pot"]
    return w


def _termo(tm: dict[str, Any], i: Instante) -> float:
    if "k" in tm:
        return float(tm["k"])
    if "metros" in tm:
        amp = i.metros(tm["metros"])
    else:
        amp = tm["amp"]
        if "par" in tm:
            amp = amp * (i.mp.get(tm["par"], tm["padrao"]) if "padrao" in tm else i.mp[tm["par"]])
    return float(amp * (i.curva(tm["curva"]) if "curva" in tm else _onda(tm, i.t, i.total)))


def valor(spec: Any, i: Instante) -> int:
    if isinstance(spec, int):
        return spec
    if spec == "-queda":
        return q_(-i.queda)
    acc: Any = None
    for tm in spec["termos"]:
        v = _termo(tm, i)
        acc = v if acc is None else acc + v
    if spec.get("fator") == "escala":
        acc = acc * i.k
    return q_(acc) + int(spec.get("fixo", 0))


def canais(rec: dict[str, Any], r: Papeis, i: Instante) -> Channels:
    """Os canais da receita no instante, pelos ossos que os papéis dizem."""
    out: Channels = {}
    for chave, c in rec["canais"].items():
        papel, junta = chave.split(".")
        out[r.exige(papel, junta)] = ([valor(v, i) for v in c.get("tr", [0, 0, 0])], valor(c.get("rot", 0), i))
    return out


def skirt_follow(r: Papeis, mp: dict[str, int]) -> Callable[[Channels], Channels] | None:
    """Os ossos da saia seguem a rotação da coxa do mesmo lado com ``skirt_follow_pm`` ‰ do ângulo: a barra acompanha
    o joelho, amortecida. Sem a saia, ``None``."""
    f = mp.get("skirt_follow_pm")
    if f is None or r.osso("saia_l", "frente") is None or r.osso("saia_r", "frente") is None:
        return None
    pares = [(r.exige(f"perna_{s}", "frente"), r.exige(f"saia_{s}", "frente")) for s in ("l", "r")]

    def post(ch: Channels) -> Channels:
        out = dict(ch)
        for coxa, saia in pares:
            out[saia] = ([0, 0, 0], q_(ch.get(coxa, ([0, 0, 0], 0))[1] * f / 1000))
        return out

    return post


def parado(rec: dict[str, Any], r: Papeis, skel: Skeleton, mp: dict[str, int]) -> dict[str, Any]:
    """Em pé, os pés no repouso por IK, chaves com suavização (o ``idle``)."""
    duracao, k = rec["duracao_ms"], mp.get("scale_pm", 1000) / 1000
    feet = [r.exige(p, "pe") for p in rec["pes"]]
    rest = rest_ankles(skel, feet)
    w = ClipWriter(skel)
    guess = bend_guess(skel, feet)
    skirt = skirt_follow(r, mp)
    for t in rec["chaves_ms"]:
        ch: Channels = dict(guess)
        ch.update(canais(rec, r, Instante(t, duracao, mp, k)))
        ch = solve_feet(skel, ch, rest)
        if skirt is not None:
            ch = skirt(ch)
        w.key(t, rec["suave"], ch, ([0, 0, 0], list(rec.get("marcas", {}).get(str(t), []))))
    contacts = [{"bone_id": f, "start_ms": 0, "end_ms": duracao, "target_q8": list(rest[f])} for f in feet]
    return w.clip(rec["clip"], duracao, rec["amostras_ms"], contacts)
