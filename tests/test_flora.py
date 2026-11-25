"""A flora em volumes, para a câmera de cima (mudança 19): a copa da folhosa é uma massa só de tufos, mostra o alto,
cobre o tronco pela frente e lança a sombra dela no chão; a conífera também; os galhos abrem em volta do tronco; a
árvore desenha as 4 vistas e balança. Os controles: a copa do jeito antigo (discos chapados no plano da frente,
espalhados) é acusada em cada medida, e a engine recusa o pontilhado, o polígono plano e as peças que saíram."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from pixel_forge.application.build import instantes
from pixel_forge.application.catalogo import de_uma_peca
from pixel_forge.application.estilo import estilo_base
from pixel_forge.application.quadros import quadro_da_pose, quadro_de_repouso
from pixel_forge.contracts.carregar import ler, validar
from pixel_forge.contracts.composicao import Composicao
from pixel_forge.contracts.ir import AssetIR
from pixel_forge.core.recusa import Recusa
from pixel_forge.core.rng import Stream
from pixel_forge.design.asset import ir_da_composicao, movimento
from pixel_forge.design.escala import PPM
from pixel_forge.design.kit.pecas_copa import tufos
from pixel_forge.design.kit.registro import PECAS
from pixel_forge.design.porte import altura_m
from pixel_forge.raster.estilo import estilo_render
from pixel_forge.raster.renderer import mascaras
from pixel_forge.rig.fk import Skeleton
from pixel_forge.rig.pose import rest_pose
from pixel_forge.views.camera import ELEVACAO_MDEG, PROFUNDIDADE_PERMILLE
from pixel_forge.views.projetor import project_view

FIXTURES = Path(__file__).parent / "fixtures"
EXEMPLO = FIXTURES / "exemplos" / "arvore_folhosa.r1.json"
ARVORE = FIXTURES / "composicoes" / "arvore.r1.json"
SD, CE = PROFUNDIDADE_PERMILLE / 1000, math.cos(math.radians(ELEVACAO_MDEG / 1000))
COPA_DO_EXEMPLO = (1.4, 0.87)  # a meia largura e a meia altura da copa do exemplo (m)
Mascara = np.ndarray[Any, np.dtype[np.bool_]]


def _pedacos(m: Mascara) -> int:
    """As ilhas da máscara (vizinhança de 4)."""
    falta = m.copy()
    n = 0
    while falta.any():
        y, x = np.argwhere(falta)[0]
        pilha = [(int(y), int(x))]
        falta[y, x] = False
        n += 1
        while pilha:
            a, b = pilha.pop()
            for c, d in ((a + 1, b), (a - 1, b), (a, b + 1), (a, b - 1)):
                if 0 <= c < falta.shape[0] and 0 <= d < falta.shape[1] and falta[c, d]:
                    falta[c, d] = False
                    pilha.append((c, d))
    return n


def leitura(comp: Composicao, copa: str = "copa") -> dict[str, float]:
    """A copa na tela, na vista S: as ilhas dela, quanto enche a elipse da caixa dela, a altura sobre a largura, a
    altura da sombra no chão sobre a largura da copa, os pixels do tronco à mostra e as partes do asset."""
    style = estilo_base()
    ir, est = ir_da_composicao(comp), estilo_render(style)
    cena = project_view(ir, rest_pose(Skeleton(ir.bones)), "S")
    cheias = mascaras(cena, est, ir.canvas.width, ir.canvas.height)
    massa: Mascara = np.logical_or.reduce([m for p, m in cheias.items() if p.startswith(copa)])
    ys, xs = np.nonzero(massa)
    w, h = int(xs.max() - xs.min()) + 1, int(ys.max() - ys.min()) + 1
    yy, xx = np.indices(massa.shape)
    elipse = ((xx - (xs.max() + xs.min()) / 2) / (w / 2)) ** 2 + ((yy - (ys.max() + ys.min()) / 2) / (h / 2)) ** 2 <= 1
    q = quadro_de_repouso(ir, est, "S")
    chao = q.index == est.materials["sombra"].ramp[0]
    sombra = np.nonzero((chao & (q.alpha == 255)).any(axis=1))[0]
    return {"pedacos": _pedacos(massa), "cheia": float((massa & elipse).sum() / elipse.sum()),
            "alto_sobre_largo": h / w,
            "sombra_sobre_largo": (int(sombra.max() - sombra.min()) + 1) / w if sombra.size else 0.0,
            "tronco": q.visiveis.get("tronco", 0), "partes": len(ir.parts),
            "sombra_px": int((chao & (q.alpha == 255)).sum()), "figura_px": int(((q.alpha == 255) & ~chao).sum())}


def _exemplo(**args: Any) -> Composicao:
    dado = json.loads(EXEMPLO.read_text(encoding="utf-8"))
    dado["nos"][1]["args"] |= args
    dado["tracos"] = []
    return validar(dado, Composicao, "teste")


def _copa_de_discos() -> Composicao:
    """O jeito antigo, sintético: a mesma árvore com a copa em discos chapados no plano da frente (sem fundo),
    espalhados dentro da elipse da copa, como os cachos pontilhados eram."""
    dado = json.loads(EXEMPLO.read_text(encoding="utf-8"))
    st = Stream(5)
    nos = [dado["nos"][0]]
    for i in range(20):
        u, v = st.randint(-80, 80) / 100, st.randint(-80, 80) / 100
        nos.append({"id": f"copa_{i:02d}", "peca": "elipsoide", "grupo": "copa", "args": {
            "centro": [f"$a * {u}", "0", f"$cz + $c * {v}"], "raios": ["22cm", "1cm", "22cm"],
            "material": "copa_folhosa"}})
    return validar({**dado, "nos": nos, "tracos": []}, Composicao, "controle")


def test_a_copa_e_uma_massa_so() -> None:
    """Uma massa cheia, com poucas partes, que mostra o alto (a altura na tela soma o fundo visto de cima)."""
    m = leitura(ler(EXEMPLO, Composicao))
    a, c = COPA_DO_EXEMPLO
    de_cima = math.hypot(a * SD, c * CE) / a  # o elipsoide da copa na câmera: 0,74 (de frente, chapado: 0,44)
    assert m["pedacos"] == 1 and m["cheia"] >= 0.9 and m["partes"] <= 30
    assert abs(m["alto_sobre_largo"] - de_cima) <= 0.05


def test_a_copa_cobre_o_tronco_e_lanca_a_sombra_dela() -> None:
    """O tronco aparece só embaixo da copa, e a sombra no chão é uma mancha do fundo da copa, não uma tira."""
    m = leitura(ler(EXEMPLO, Composicao))
    so_o_tronco = leitura(_exemplo(copa=["10cm", "10cm", "$cz"]))["tronco"]
    assert 0 < m["tronco"] < 0.6 * so_o_tronco
    assert m["sombra_sobre_largo"] >= 0.35


def test_controle_a_copa_de_discos_chapados_e_acusada() -> None:
    m = leitura(_copa_de_discos())
    a, c = COPA_DO_EXEMPLO
    assert m["pedacos"] > 1 and m["cheia"] < 0.9
    assert abs(m["alto_sobre_largo"] - math.hypot(a * SD, c * CE) / a) > 0.05
    assert m["sombra_sobre_largo"] < 0.35


@pytest.mark.parametrize("semente", range(12))
def test_o_tufo_nao_passa_da_copa(semente: int) -> None:
    """O tufo encosta por dentro no elipsoide da copa: a altura e a largura do asset são as da copa pedida."""
    a = {"copa": (40.0, 30.0, 60.0), "fundo": 0.8, "tufos": 7, "tamanho": 0.45, "irregular": 0.3, "pende": 0.0}
    eixos = (40.0, 32.0, 30.0)
    for (cx, cy, cz), raios in tufos(Stream(semente), a):
        d = [abs(v) / e for v, e in zip((cx, cy, cz - 60.0), eixos, strict=True)]
        assert math.hypot(*d) + raios[0] / eixos[0] <= 1 + 1e-9


def test_a_altura_da_copa_e_a_pedida() -> None:
    args = PECAS["copa"].variacoes[0][1]
    assert args["copa"] == ["1.2m", "1m", "1.9m"]
    assert altura_m(ir_da_composicao(de_uma_peca("copa", args))) == pytest.approx(2.9, abs=1 / PPM)


def test_controle_o_tufo_que_pende_desce_da_copa() -> None:
    """Com ``pende``, os tufos de baixo descem do elipsoide (o ramo que cai) sem entrar no chão."""
    a = {"copa": (40.0, 30.0, 60.0), "fundo": 1.0, "tufos": 7, "tamanho": 0.3, "irregular": 0.0}
    reto = min(c[2] - r[2] for c, r in tufos(Stream(1), {**a, "pende": 0.0}))
    cai = min(c[2] - r[2] for c, r in tufos(Stream(1), {**a, "pende": 2.0}))
    assert 0 <= cai < reto - 5


def _conifera_chapada() -> Composicao:
    """O jeito antigo, sintético: a conífera como uma face chapada no plano da frente."""
    return de_uma_peca("poligono", {"pontos": [["-90cm", "0", "50cm"], ["90cm", "0", "50cm"], ["0", "0", "4m"]],
                                    "material": "agulha"})


def test_a_conifera_lanca_a_sombra_dela() -> None:
    """A sombra no chão da conífera é a do cone (uma mancha larga); a ponta é da altura pedida."""
    for _, args in PECAS["copa_conica"].variacoes:
        comp = de_uma_peca("copa_conica", args)
        m = leitura(comp, "n_")
        assert m["sombra_px"] >= 0.2 * m["figura_px"], args
    alta = PECAS["copa_conica"].variacoes[0][1]
    assert altura_m(ir_da_composicao(de_uma_peca("copa_conica", alta))) == pytest.approx(4.0, abs=1 / PPM)


def test_controle_a_conifera_chapada_lanca_uma_linha() -> None:
    m = leitura(_conifera_chapada(), "n")
    assert m["sombra_px"] < 0.2 * m["figura_px"]


def _pontas(fundo: str) -> list[tuple[float, float]]:
    args = {**PECAS["galhos"].variacoes[0][1], "fundo": fundo, "bifurca": "0"}
    ir = ir_da_composicao(de_uma_peca("galhos", args))
    pontas = [p.geometry.points_q8[-1] for p in ir.parts if p.geometry.type == "tapered_polyline"]
    return [(p[0] / 256, p[1] / 256) for p in pontas]


def test_os_galhos_abrem_em_volta_do_tronco() -> None:
    """Uma ponta em cada fatia da volta: há galho para a frente, para trás e para os dois lados."""
    pontas = _pontas("1")
    fatias = {int((math.degrees(math.atan2(x, y)) % 360) // (360 / len(pontas))) for x, y in pontas}
    assert len(pontas) == 5 and len(fatias) >= 4
    assert min(y for _, y in pontas) < -5 and max(y for _, y in pontas) > 5


def test_controle_os_galhos_num_plano_so_sao_acusados() -> None:
    """O leque do jeito antigo (todos no plano da frente): nenhuma ponta sai para a frente nem para trás."""
    assert all(abs(y) < 1e-6 for _, y in _pontas("0"))


def test_a_arvore_desenha_as_quatro_vistas() -> None:
    dado = json.loads(ARVORE.read_text(encoding="utf-8"))
    comp = validar({**dado, "vistas": dict.fromkeys(("S", "E", "N", "W"), {}), "movimento": ["static"],
                    "nos": [{**n, "osso": "raiz"} for n in dado["nos"]]}, Composicao, "teste")
    ir, est = ir_da_composicao(comp), estilo_render(estilo_base())
    quadros = {d: quadro_de_repouso(ir, est, d) for d in ir.views}
    assert all(q.clipping_px == 0 and q.visiveis.get("tronco", 0) > 0 for q in quadros.values())
    assert len({q.index.tobytes() for q in quadros.values()}) == 4  # cada vista é outra face da mesma árvore


def test_controle_a_peca_de_uma_vista_so_e_recusada_nas_quatro() -> None:
    dado = json.loads(ARVORE.read_text(encoding="utf-8"))
    fios = {"id": "fios", "peca": "fios", "args": {"raio": "50cm", "altura": "60cm"}}
    with pytest.raises(Recusa) as e:
        ir_da_composicao(validar({**dado, "vistas": dict.fromkeys(("S", "E", "N", "W"), {}), "movimento": ["static"],
                                  "nos": [fios]}, Composicao, "teste"))
    assert e.value.codigo == "VISTA"


def _balanco(osso: str) -> tuple[int, int]:
    """Os quadros diferentes do balanço e, deles, os diferentes nas 6 fileiras de baixo da figura (o pé do tronco)."""
    dado = json.loads(ARVORE.read_text(encoding="utf-8"))
    nos = [dado["nos"][0], *({**n, "osso": osso} for n in dado["nos"][1:])]
    comp = validar({**dado, "nos": nos}, Composicao, "teste")
    ir, est = ir_da_composicao(comp), estilo_render(estilo_base())
    pedidos, mp = movimento(comp)
    its, loop = instantes(ir, "sway", pedidos["sway"], mp)
    assert loop
    py = ir.canvas.pivot_px[1]
    quadros = [quadro_da_pose(ir, est, it.pose, "S") for it in its]
    assert all(q.clipping_px == 0 for q in quadros)
    chao = est.materials["sombra"].ramp[0]  # a sombra da copa no chão balança com ela: não é o pé do tronco
    pes = {np.where(q.index[py - 5:py + 1] == chao, 0, q.index[py - 5:py + 1]).tobytes() for q in quadros}
    return len({q.index.tobytes() for q in quadros}), len(pes)


@pytest.mark.slow
def test_o_balanco_move_a_copa_e_nao_o_pe_do_tronco() -> None:
    inteiros, pes = _balanco("cadeia")
    assert inteiros > 1 and pes == 1


@pytest.mark.slow
def test_controle_a_copa_fora_da_cadeia_nao_balanca() -> None:
    assert _balanco("tronco") == (1, 1)


def test_controle_a_ir_recusa_o_pontilhado_e_o_poligono_plano() -> None:
    """O jeito antigo não existe mais: a IR não tem as geometrias da flora chapada."""
    ir = ir_da_composicao(ler(EXEMPLO, Composicao)).model_dump(mode="json")
    plano = {"plane": "xz", "origin_q8": [0, 0, 0], "vertices_q8": [[0, 0], [256, 0], [0, 256]]}
    for geo in ({"type": "polygon", **plano},
                {"type": "stipple", **plano, "density_permille": 700, "seed": 1, "cell_px": 1}):
        with pytest.raises(Recusa):
            validar({**ir, "parts": [{**ir["parts"][0], "geometry": geo}]}, AssetIR, "controle")


@pytest.mark.parametrize(("antiga", "nova"), [("pontilhado", "'copa'"), ("galhos_em_pena", "'copa_conica'"),
                                              ("galhos_grossos", "'galhos'"), ("cortinas", "pende")])
def test_controle_a_peca_que_saiu_e_recusada_com_a_que_ficou(antiga: str, nova: str) -> None:
    dado = json.loads(EXEMPLO.read_text(encoding="utf-8"))
    dado["nos"][1]["peca"] = antiga
    with pytest.raises(Recusa) as e:
        ir_da_composicao(validar({**dado, "tracos": []}, Composicao, "teste"))
    assert e.value.codigo == "PECA" and nova in e.value.dica
