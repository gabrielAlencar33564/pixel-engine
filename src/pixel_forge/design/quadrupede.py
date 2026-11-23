"""O quadrúpede como composição: um nó ``corpo_canino`` (o corpo, as marcas e as orelhas são argumentos dele), as 8
direções (quem anda vira) e o movimento: o parado e o passo em sequência lateral. O canvas sai do tamanho do bicho em
qualquer azimute, com a folga da passada."""

from __future__ import annotations

import math
from typing import Any

from ..contracts.composicao import Clipe, Composicao
from ..core.direcoes import DIRECOES
from ..core.recusa import Recusa
from ..core.rng import Stream
from ..views.camera import SOMBRA_POR_ALTURA
from .composicao import medidas, semente_do_no
from .construtor import AssetBuilder
from .kit.peca import Ctx, ler_args
from .kit.pecas_quadrupede import CERNELHA, COMPRIMENTO
from .kit.pilha import Pilha
from .kit.registro import PECAS
from .vistas import no_mundo

CORPO = "corpo_canino"
CLIPES = {"idle": "quadrupede_parado", "walk": "quadrupede_passo"}  # o clipe e a receita que o gera
FOLGA_PX = 5  # a passada: a pata vai à frente e atrás do repouso


def clipes(comp: Composicao) -> dict[str, str]:
    return {m.clip if isinstance(m, Clipe) else str(m): m.receita if isinstance(m, Clipe) else CLIPES.get(str(m), "")
            for m in comp.movimento}


def validar_quadrupede(comp: Composicao) -> None:
    """As recusas além do schema: as 8 direções, o corpo como o único nó, o argumento fora do schema e o clipe que o
    quadrúpede não faz."""
    nome = f"Composição '{comp.id}'"
    if sorted(comp.vistas) != sorted(DIRECOES):
        raise Recusa("VISTA", f"{nome}: o quadrúpede anda e vira: as 8 direções; pediu {', '.join(comp.vistas)}.",
                     "Declare as 8 direções (S, SW, W, NW, N, NE, E, SE).", "/vistas")
    if [n.peca for n in comp.nos] != [CORPO]:
        raise Recusa("CORPO", f"{nome}: o quadrúpede é um nó '{CORPO}'.",
                     "O corpo, as marcas e as orelhas são argumentos da peça (veja `pfe catalogo`).", "/nos")
    sobra = sorted(set(comp.nos[0].args) - {a.nome for a in PECAS[CORPO].args})
    if sobra:
        raise Recusa("ARGUMENTO", f"Peça '{CORPO}': argumento desconhecido {', '.join(sobra)}.",
                     "Veja o schema da peça em `pfe catalogo`.", f"/nos/0/args/{sobra[0]}")
    for j, (clip, receita) in enumerate(clipes(comp).items()):
        if CLIPES.get(clip) != receita:
            raise Recusa("MOVIMENTO", f"{nome}: o clipe '{clip}' (receita '{receita}') não é do quadrúpede.",
                         f"Clipes do quadrúpede: {', '.join(CLIPES)} (quem anda tem 'walk').", f"/movimento/{j}")


def _canvas(parts: list[dict[str, Any]]) -> dict[str, Any]:
    """O raio no chão e a altura, na câmera de 45°, mais a folga da passada; à direita, a sombra no chão da cabeça e
    do dorso (pela luz da câmera)."""
    s = c = math.sqrt(0.5)
    raio, topo = 0.0, 0.0
    for p in parts:
        g = p["geometry"]
        pts = g.get("points_q8") or [g["center_q8"]]
        r = max(g.get("radii_q8", [g.get("thickness_px", 1) * 128])) / 256
        for x, y, z in ((v / 256 for v in pt) for pt in pts):
            raio, topo = max(raio, math.hypot(x, y) + r), max(topo, z + r)
    esquerda, direita = math.ceil(raio + FOLGA_PX), math.ceil(raio + SOMBRA_POR_ALTURA * topo + FOLGA_PX)
    acima, abaixo = math.ceil(raio * s + topo * c + FOLGA_PX), math.ceil(raio * s + FOLGA_PX)
    return {"width": esquerda + direita, "height": acima + abaixo, "pivot_px": [esquerda, acima]}


def ir_do_quadrupede(comp: Composicao) -> dict[str, Any]:
    no = comp.nos[0]
    b = AssetBuilder()
    corpo: dict[str, Any] = {}
    ctx = Ctx(b, Stream(semente_do_no(comp.semente, no.id)), no.id, no.id, Pilha(), 0, no=no.id, humano=corpo)
    PECAS[CORPO].desenha(ctx, ler_args(PECAS[CORPO], no.args, medidas(comp), "/nos/0"))
    canvas = _canvas(no_mundo(b.parts, b.bones))
    return {"id": comp.id, "revision": comp.revision, "bones": b.bones, "parts": b.parts, "landmarks": [],
            "canvas": canvas, "views": corpo["vistas"], "modelo": "canino"}


def movimento_do_quadrupede(comp: Composicao) -> dict[str, int]:
    """A passada na escala do bicho: a da régua (passada de 2,5 px, elevação de 1,2 px, o sobe-e-desce de 0,2 px, o
    apoio de 65 % do ciclo) vezes o tamanho dele sobre a régua."""
    a = ler_args(PECAS[CORPO], comp.nos[0].args, medidas(comp), "/nos/0")
    kz, ky = a["altura"] / CERNELHA, a["comprimento"] / COMPRIMENTO
    return {"stride_q8": round(640 * ky), "lift_q8": round(307 * kz), "bob_q8": round(51 * kz),
            "idle_bob_q8": round(358 * kz), "duty_permille": 650}
