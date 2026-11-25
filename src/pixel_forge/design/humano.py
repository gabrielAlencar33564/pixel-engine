"""O humano como composição: o corpo como primeiro nó, a roupa depois, as 8 direções (quem anda vira) e o movimento
pelos clipes que o corpo faz. O que é assimétrico nunca é espelhado: cada direção é uma vista do mesmo corpo."""

from __future__ import annotations

from typing import Any

from ..contracts.composicao import Clipe, Composicao
from ..core.direcoes import DIRECOES
from ..core.recusa import Recusa
from ..core.rng import Stream
from .composicao import medidas, semente_do_no
from .construtor import AssetBuilder
from .expressao import compilar, variaveis
from .kit.humano import FRONT_VIEWS, canvas_de, landmarks, motion_params, regras
from .kit.humano import medidas as medidas_do_corpo
from .kit.peca import Ctx, ler_args
from .kit.pecas_humano import corpo_dos_args
from .kit.pilha import Pilha
from .kit.registro import PECAS
from .kit.roupa import Vista

CORPO = "corpo_humano"
CLIPES = {"idle": "parado", "walk": "andar_poses", "attack": "golpe"}  # o clipe e a receita que o gera


def clipes(comp: Composicao) -> dict[str, str]:
    """Os clipes pedidos e a receita de cada um."""
    return {m.clip if isinstance(m, Clipe) else str(m): m.receita if isinstance(m, Clipe) else CLIPES.get(str(m), "")
            for m in comp.movimento}


def _conferir_no(comp: Composicao, i: int, ids: set[str]) -> None:
    no = comp.nos[i]
    peca = PECAS.get(no.peca)
    if peca is None or peca.tipo != "humanoide":
        nomes = ", ".join(sorted(p.id for p in PECAS.values() if p.tipo == "humanoide"))
        raise Recusa("PECA", f"Nó '{no.id}': a peça '{no.peca}' não é do humanoide.", f"Peças: {nomes}.",
                     f"/nos/{i}/peca")
    if no.id in ids or no.repete is not None or no.osso != "raiz":
        raise Recusa("NO", f"Nó '{no.id}': id repetido, repetição ou osso de prop.",
                     "Cada peça do humano é um nó; ela diz os ossos do rig que usa.", f"/nos/{i}")
    sobra = sorted(set(no.args) - {a.nome for a in peca.args})
    if sobra:
        raise Recusa("ARGUMENTO", f"Peça '{no.peca}': argumento desconhecido {', '.join(sobra)}.",
                     "Veja o schema da peça em `pfe catalogo`.", f"/nos/{i}/args/{sobra[0]}")


def validar_humano(comp: Composicao) -> None:
    """As recusas além do schema: as 8 direções, o corpo como primeiro e único nó do corpo, a peça que não é do
    humano, o argumento fora do schema e o clipe que o corpo não faz."""
    if sorted(comp.vistas) != sorted(DIRECOES):
        raise Recusa("VISTA", f"Composição '{comp.id}': o humano anda e vira: as 8 direções; pediu "
                     f"{', '.join(comp.vistas)}.", "Declare as 8 direções (S, SW, W, NW, N, NE, E, SE).", "/vistas")
    if comp.nos[0].peca != CORPO or [n.peca for n in comp.nos].count(CORPO) != 1:
        raise Recusa("CORPO", f"Composição '{comp.id}': o primeiro nó é o corpo ('{CORPO}'), e só ele.",
                     "Ponha um nó corpo_humano no começo; a roupa vem depois.", "/nos/0")
    for nome, texto in comp.medidas.items():
        variaveis(compilar(texto, f"/medidas/{nome}"))
    ids: set[str] = set()
    for i, no in enumerate(comp.nos):
        _conferir_no(comp, i, ids)
        ids.add(no.id)
    for j, (clip, receita) in enumerate(clipes(comp).items()):
        if CLIPES.get(clip) != receita:
            raise Recusa("MOVIMENTO", f"Composição '{comp.id}': o clipe '{clip}' (receita '{receita}') não é do corpo.",
                         f"Clipes do humano: {', '.join(CLIPES)} (quem anda tem 'walk').", f"/movimento/{j}")


def _vistas(b: AssetBuilder, vista: Vista) -> dict[str, Any]:
    """As regras e o que some em cada uma das 8 vistas (só as regras entre peças que o corpo vestido tem)."""
    ids = {p["id"] for p in b.parts}

    def ok(rules: list[dict[str, str]]) -> list[dict[str, str]]:
        return [r for r in rules if r["front"] in ids and r["back"] in ids]

    out: dict[str, Any] = {}
    for d in DIRECOES:
        frente = d in FRONT_VIEWS
        rules = regras(d) + ok(vista.rules + (vista.front_rules if frente else vista.back_rules))
        some = vista.cobre + ([] if frente else vista.hide_back) + {"W": vista.hide_w, "E": vista.hide_e}.get(d, [])
        out[d] = {"occlusion_rules": rules, "visibility": {pid: "hidden" for pid in some if pid in ids}}
    return out


def ir_do_humano(comp: Composicao) -> dict[str, Any]:
    """A IR do humano: o corpo e a roupa pelos nós, as 8 vistas e o canvas do cânone."""
    env = medidas(comp)
    b = AssetBuilder()
    humano: dict[str, Any] = {}
    for i, no in enumerate(comp.nos):
        args = ler_args(PECAS[no.peca], no.args, env, f"/nos/{i}")
        ctx = Ctx(b, Stream(semente_do_no(comp.semente, no.id)), no.id, no.grupo or no.id, Pilha(), 0, no=no.id,
                  humano=humano)
        PECAS[no.peca].desenha(ctx, args)
    c = humano["medidas"]
    arma = any(no.peca == "espada" for no in comp.nos)
    return {"id": comp.id, "revision": comp.revision, "bones": b.bones, "parts": b.parts, "landmarks": landmarks(c),
            "canvas": canvas_de(c["estatura"], arma), "views": _vistas(b, humano["vista"]), "modelo": "humano"}


def movimento_do_humano(comp: Composicao) -> dict[str, int]:
    """Os parâmetros do movimento na escala do corpo do primeiro nó; com a saia, a barra segue a coxa com 35 %."""
    a = ler_args(PECAS[CORPO], comp.nos[0].args, medidas(comp), "/nos/0")
    mp = motion_params(medidas_do_corpo(corpo_dos_args(a)))
    if any(no.peca == "saia" for no in comp.nos):
        mp["skirt_follow_pm"] = 350
    return mp
