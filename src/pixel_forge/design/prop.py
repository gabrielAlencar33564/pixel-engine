"""O prop como composição: só peças do kit, na raiz (ou na cadeia do balanço, ou no osso do giro), com a sombra de
contato, os pontos do jogo, as vistas declaradas (1, 2 ou 4) e o canvas do tamanho dele."""

from __future__ import annotations

from typing import Any

from ..contracts.composicao import Balanco, Composicao, Giro
from ..core.recusa import Recusa
from ..core.rng import Stream
from .canvas import canvas_do_prop
from .composicao import conferir_medidas, conferir_nos, medidas, repeticoes, semente_do_no
from .construtor import AssetBuilder, Junta, Parte, ellipse, q, qv
from .expressao import compilar, valor, variaveis
from .kit.movimento import Elo, sway_chain
from .kit.peca import Ctx, ler_args
from .kit.pilha import Pilha
from .kit.registro import PECAS
from .vistas import (
    AZIMUTE,
    N_VISTAS,
    SEN45,
    VISTAS,
    no_mundo,
    regras_da_vista,
    reparentar,
    sombra_da_vista,
    sombra_no_obliquo,
)

PRECISA = {"tronco": "balanco", "cadeia": "balanco", "giro": "giro"}


def _receita[R: (Balanco, Giro)](comp: Composicao, tipo: type[R]) -> R | None:
    return next((m for m in comp.movimento if isinstance(m, tipo)), None)


def _conferir_movimento(comp: Composicao, conhecidas: set[str]) -> None:
    estranho = [m for m in comp.movimento if not isinstance(m, Balanco | Giro) and m != "static"]
    receitas = [m for m in comp.movimento if isinstance(m, Balanco | Giro)]
    if estranho or comp.movimento.count("static") > 1 or len({type(m) for m in receitas}) != len(receitas):
        raise Recusa("MOVIMENTO", f"Composição '{comp.id}': o prop tem 'static' e no máximo um balanço e um giro.",
                     "Os clipes de andar e de ação são de quem anda (humanoide, quadrúpede).", "/movimento")
    for j, m in enumerate(receitas):
        textos = [m.tronco, m.base, m.topo] if isinstance(m, Balanco) else list(m.centro)
        falta = set().union(*(variaveis(compilar(t)) for t in textos)) - conhecidas
        if falta:
            raise Recusa("EXPRESSAO", f"A receita '{m.receita}' usa {', '.join(sorted(falta))}.",
                         "Declare em 'medidas'.", f"/movimento/{j}")
    giro = _receita(comp, Giro)
    if giro is not None and (giro.periodo_ms % giro.quadros or 360_000 * giro.voltas // giro.quadros >= 180_000):
        raise Recusa("GIRO", f"O giro de {giro.voltas} volta(s) em {giro.quadros} quadros e {giro.periodo_ms} ms: o "
                     "período tem de ser múltiplo dos quadros e o passo menor que 180° (senão o sentido fica ambíguo).",
                     f"Use quadros que dividam o período e mais de {2 * giro.voltas} quadros.", "/movimento")
    tem = {m.receita for m in receitas}
    for i, no in enumerate(comp.nos):
        if no.osso in PRECISA and PRECISA[no.osso] not in tem:
            raise Recusa("MOVIMENTO", f"Nó '{no.id}': o osso '{no.osso}' pede a receita '{PRECISA[no.osso]}' em "
                         "'movimento'.", "Declare a receita ou use 'raiz'.", f"/nos/{i}/osso")


def movimento_do_prop(comp: Composicao) -> tuple[dict[str, str], dict[str, int]]:
    """Os clipes do prop (o estático, o balanço ``sway`` e o giro ``spin``) e os parâmetros das receitas."""
    clipes: dict[str, str] = {"static": ""} if "static" in comp.movimento else {}
    mp: dict[str, int] = {}
    if (m := _receita(comp, Balanco)) is not None:
        clipes["sway"] = "balanco"
        mp |= {"sway_period_ms": m.periodo_ms, "sway_shift_px": m.desloca_px, "sway_wave_px": m.onda_px,
               "sway_lag_mdeg": m.atraso_mdeg, "sway_sample_ms": m.amostra_ms}
    if (g := _receita(comp, Giro)) is not None:
        clipes["spin"] = "giro"
        mp |= {"spin_period_ms": g.periodo_ms, "spin_frames": g.quadros, "spin_turns": g.voltas,
               "spin_dir": g.sentido}
    return clipes, mp


def validar_prop(comp: Composicao) -> None:
    """As recusas do prop além do schema, sem montar."""
    vistas = list(comp.vistas)
    if sorted(set(vistas) - set(VISTAS)) or "S" not in vistas or len(vistas) not in N_VISTAS:
        raise Recusa("VISTA", f"Composição '{comp.id}': o prop parado tem 1 vista (a do jogo), ou 2 ou 4 cardinais "
                     f"({', '.join(VISTAS)}) se o pedido disser, sempre com a S; pediu {', '.join(vistas)}.",
                     "Declare só a S (o padrão); as 8 direções são de quem anda ou vira.", "/vistas")
    conhecidas = conferir_medidas(comp)
    _conferir_movimento(comp, conhecidas)
    conferir_nos(comp, conhecidas)


def _sombra(b: AssetBuilder, comp: Composicao, env: dict[str, float]) -> None:
    """A sombra de contato com a proporção (≈ 3:1) na tela da câmera física de 45° do kit (a do canvas), deslocada
    para o lado da sombra; :func:`sombra_no_obliquo` a leva ao 3/4 oblíquo depois do canvas."""
    sh = comp.sombra
    if sh is None:
        return
    meia = valor(sh.meia_largura, env)
    g = ellipse(qv(valor(sh.dx, env), valor(sh.dy, env), 0), qv(meia, meia / (sh.proporcao_pm / 1000) / SEN45, 0.3))
    b.part("ground_shadow", "sombra", g, Parte(tags=("ground_shadow",), priority=-100))


def _ossos(b: AssetBuilder, comp: Composicao, env: dict[str, float]) -> tuple[list[Elo], tuple[float, ...] | None]:
    """A raiz, o tronco e a cadeia do balanço e o osso do giro; devolve a cadeia e o centro do giro."""
    b.bone("root", None, [0, 0, 0], Junta("z"))
    cadeia: list[Elo] = []
    if (bal := _receita(comp, Balanco)) is not None:
        base = valor(bal.base, env)
        b.bone("trunk", "root", qv(0, 0, 0), Junta("z", q(valor(bal.tronco, env))))
        cadeia = sway_chain(b, "trunk", base, valor(bal.topo, env) - base, bal.elos)
    if (giro := _receita(comp, Giro)) is None:
        return cadeia, None
    centro = tuple(valor(t, env) for t in giro.centro)
    b.bone("spin", "root", qv(*centro), Junta(giro.eixo, q(1)))
    return cadeia, centro


def _nos(b: AssetBuilder, comp: Composicao, env: dict[str, float], ossos: tuple[list[Elo], Any]
         ) -> tuple[list[Any], dict[str, dict[str, Any]]]:
    """Os nós na ordem do arquivo, cada repetição com a semente dela, no osso do nó; devolve as regras das pilhas e o
    que as peças mudam por vista."""
    cadeia, centro_giro = ossos
    pilhas: dict[str, Pilha] = {}
    regras: list[dict[str, Any]] = []
    ancoras: dict[str, list[Any]] = {}
    por_vista: dict[str, dict[str, Any]] = {}
    vistas: dict[str, int] = {v: AZIMUTE[v] for v in comp.vistas}
    for i, no in enumerate(comp.nos):
        peca = PECAS[no.peca]
        for pid, rv in repeticoes(no):
            args = ler_args(peca, no.args, {**env, **rv}, f"/nos/{i}")
            ctx = Ctx(b, Stream(semente_do_no(comp.semente, pid)), pid, no.grupo or no.id,
                      pilhas.setdefault(no.pilha, Pilha()), no.camada, regras, vistas, cadeia, no.osso, ancoras,
                      por_vista, no.id)
            n0 = len(b.parts)
            peca.desenha(ctx, args)
            reparentar(b.parts[n0:], no.osso, cadeia, centro_giro)
    return regras + [r for s in pilhas.values() for r in s.rules()], por_vista


def _vistas(comp: Composicao, b: AssetBuilder, regras: list[Any], por_vista: dict[str, dict[str, Any]]
            ) -> dict[str, Any]:
    out: dict[str, Any] = {}
    sombra = next((p for p in b.parts if p["id"] == "ground_shadow"), None)
    for d, vista in comp.vistas.items():
        az = AZIMUTE[d]
        v: dict[str, Any] = {"occlusion_rules": regras_da_vista(b.parts, regras, az),
                             "visibility": dict.fromkeys(vista.ocultas, "hidden"),
                             "depth_bias": por_vista.get(d, {}).get("depth_bias", {})}
        if sombra is not None and az:
            v["geometria"] = {"ground_shadow": sombra_da_vista(sombra["geometry"], az)}
        out[d] = v
    return out


def ir_do_prop(comp: Composicao) -> dict[str, Any]:
    """A IR do prop, com o canvas do tamanho dele em todas as vistas."""
    env = medidas(comp)
    b = AssetBuilder()
    ossos = _ossos(b, comp, env)
    _sombra(b, comp, env)
    regras, por_vista = _nos(b, comp, env, ossos)
    ids = [p["id"] for p in b.parts]
    repetidos = sorted({x for x in ids if ids.count(x) > 1})
    if repetidos:
        raise Recusa("NO", f"Composição '{comp.id}': partes com o mesmo id ({', '.join(repetidos[:4])}).",
                     "Duas peças de id fixo (o bocal, o cercado) não cabem na mesma composição.", "/nos")
    bal = _receita(comp, Balanco)
    folga = 3 + (bal.desloca_px if bal else 0)
    lms = [{"id": nome, "bone_id": "root", "point_q8": qv(*(valor(t, env) for t in ponto))}
           for nome, ponto in comp.landmarks.items()]
    canvas = canvas_do_prop(no_mundo(b.parts, b.bones), folga, tuple(AZIMUTE[v] for v in comp.vistas))
    sombra_no_obliquo(b.parts)
    return {"id": comp.id, "revision": comp.revision, "bones": b.bones, "parts": b.parts, "landmarks": lms,
            "canvas": canvas, "views": _vistas(comp, b, regras, por_vista)}
