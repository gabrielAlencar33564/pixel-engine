"""A luz pela normal na face chapada: o tom da face sai da normal e da luz do estilo, não de uma escolha da peça.

A face com a marca ``lit_by_normal`` desce ou sobe um degrau da família do material dela (a cadeia do
``cast_material``: tábua clara → tábua → tábua escura) pelo Lambert da normal: de frente para a luz, um degrau acima;
de costas, um abaixo; no meio, o material como está. ``tone_up`` e ``tone_down`` são o desvio da própria peça,
somado ao da luz; o total fica em um degrau para cada lado. A troca é do material do comando, antes de qualquer passe.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import replace
from math import isqrt

from ..contracts.estilo import MaterialDef
from ..views.primitivas import DrawCommand, Ponto3

LIT = "lit_by_normal"
DESVIO = {"tone_up": 1, "tone_down": -1}
# Lambert (‰) com a luz do alto à esquerda: a face sobe um degrau de CLARO para cima e desce de ESCURO para baixo. A
# faixa do meio é larga do lado da luz porque quase toda face vista de cima recebe um pouco dela.
CLARO_PM, ESCURO_PM = 700, -200


def familias(materials: Sequence[MaterialDef]) -> tuple[dict[str, str], dict[str, str]]:
    """(degrau de cima, degrau de baixo) de cada material pela cadeia do ``cast_material``. Com dois materiais que
    descem para o mesmo, o de cima é o que tem o id do de baixo como prefixo (``tabua_clara`` sobre ``tabua``)."""
    down = {m.id: m.cast_material for m in materials if m.cast_material}
    ups: dict[str, list[str]] = {}
    for m in materials:
        if m.cast_material:
            ups.setdefault(m.cast_material, []).append(m.id)
    up: dict[str, str] = {}
    for base, cands in ups.items():
        pref = cands if len(cands) == 1 else [c for c in cands if c.startswith(base)]
        if len(pref) == 1:
            up[base] = pref[0]
    return up, down


def lambert_permille(light_dir: Sequence[int], facing: Ponto3) -> int:
    """O Lambert da face com a luz do estilo (espaço de câmera), em ‰ de [-1000, 1000]. Inteiro e sem estado."""
    lx, ly, lz = light_dir
    ln = isqrt((lx * lx + ly * ly + lz * lz) * 1_000_000) or 1
    return (facing[0] * lx + facing[1] * ly + facing[2] * lz) * 1000 // ln


def _degrau(lambert_pm: int) -> int:
    return 1 if lambert_pm >= CLARO_PM else -1 if lambert_pm <= ESCURO_PM else 0


def pela_normal(commands: list[DrawCommand], materials: Sequence[MaterialDef],
                lambert: Callable[[Ponto3], int]) -> list[DrawCommand]:
    """Os comandos com o material de cada face ``lit_by_normal`` trocado pelo degrau da luz mais o desvio."""
    up, down = familias(materials)
    out = []
    for c in commands:
        if LIT not in c.tags or c.facing is None:
            out.append(c)
            continue
        n = max(-1, min(1, _degrau(lambert(c.facing)) + sum(DESVIO.get(t, 0) for t in c.tags)))
        m = up.get(c.material, c.material) if n > 0 else down.get(c.material, c.material) if n < 0 else c.material
        out.append(c if m == c.material else replace(c, material=m))
    return out
