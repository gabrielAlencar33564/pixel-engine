"""A flora em volumes, para a câmera de cima (mudança 19): a copa da folhosa é uma massa só de tufos, mostra o alto,
cobre o tronco pela frente e lança a sombra dela no chão; a conífera também; os galhos abrem em volta do tronco; a
árvore desenha as 4 vistas e balança. Os controles: a copa do jeito antigo (discos chapados no plano da frente,
espalhados) é acusada em cada medida, e a engine recusa o pontilhado, o polígono plano e as peças que saíram.

A flora variada (mudança 21): a copa é uma massa de luz só, em lóbulos desencontrados que a semente muda; o perfil
faz a gota e o guarda-sol; a copa aberta deixa os galhos à mostra; a saia da conífera é recortada; os galhos saem
escalonados. O controle de cada uma é o jeito de antes (cada tufo com a sua luz, a saia lisa, a copa fechada)."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from pixel_forge.application import critica
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
from pixel_forge.design.kit import pecas_copa, pecas_tronco
from pixel_forge.design.kit.pecas_copa import ramos, tufos
from pixel_forge.design.kit.registro import PECAS
from pixel_forge.design.porte import altura_m
from pixel_forge.quality import flora
from pixel_forge.raster import montagem, sombra, tons, volume
from pixel_forge.raster.estilo import estilo_render
from pixel_forge.raster.grade import MARGIN
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
    return {"pedacos": flora.ilhas(massa), "cheia": float((massa & elipse).sum() / elipse.sum()),
            "alto_sobre_largo": h / w,
            "sombra_sobre_largo": (int(sombra.max() - sombra.min()) + 1) / w if sombra.size else 0.0,
            "tronco": q.visiveis.get("tronco", 0), "partes": len(ir.parts),
            "sombra_px": int((chao & (q.alpha == 255)).sum()), "figura_px": int(((q.alpha == 255) & ~chao).sum())}


COPA_DE_TESTE: dict[str, Any] = {"copa": (40.0, 30.0, 60.0), "fundo": 1.0, "tufos": 7, "tamanho": 0.45,
                                 "irregular": 0.14, "perfil": 0.0, "raminhos": 2, "pende": 0.0}


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
    """Uma massa só, com poucas partes, que mostra o alto (a altura na tela soma o fundo visto de cima); os lóbulos
    recuam da borda, e ela não enche mais a elipse como o ovo."""
    m = leitura(ler(EXEMPLO, Composicao))
    a, c = COPA_DO_EXEMPLO
    de_cima = math.hypot(a * SD, c * CE) / a  # o elipsoide da copa na câmera: 0,74 (de frente, chapado: 0,44)
    assert m["pedacos"] == 1 and 0.6 <= m["cheia"] < 0.9 and m["partes"] <= 40
    assert abs(m["alto_sobre_largo"] - de_cima) <= 0.1


def test_a_copa_cobre_o_tronco_e_lanca_a_sombra_dela() -> None:
    """O tronco aparece só embaixo da copa, e a sombra no chão é uma mancha do fundo da copa, não uma tira."""
    m = leitura(ler(EXEMPLO, Composicao))
    so_o_tronco = leitura(_exemplo(copa=["10cm", "10cm", "$cz"]))["tronco"]
    assert 0 < m["tronco"] < 0.8 * so_o_tronco
    assert m["sombra_sobre_largo"] >= 0.35


def test_controle_a_copa_de_discos_chapados_e_acusada() -> None:
    m = leitura(_copa_de_discos())
    a, c = COPA_DO_EXEMPLO
    assert m["pedacos"] > 1 and m["cheia"] < 0.6
    assert abs(m["alto_sobre_largo"] - math.hypot(a * SD, c * CE) / a) > 0.1
    assert m["sombra_sobre_largo"] < 0.35


@pytest.mark.parametrize("semente", range(12))
def test_o_tufo_nao_passa_da_copa(semente: int) -> None:
    """Nenhum lóbulo nem raminho passa do elipsoide da copa, com qualquer perfil, e o raminho do alto encosta
    nele: a altura do asset é a da copa pedida."""
    eixos = (40.0, 32.0, 30.0)
    for perfil in (-1.0, 0.0, 1.0):
        a = {**COPA_DE_TESTE, "fundo": 0.8, "irregular": 0.3, "perfil": perfil}
        volumes = tufos(Stream(semente), a)
        for (cx, cy, cz), raios in volumes:
            d = [abs(v) / e for v, e in zip((cx, cy, cz - 60.0), eixos, strict=True)]
            assert math.hypot(*d) + raios[0] / eixos[0] <= 1 + 1e-9
        assert max(c[2] + r[2] for c, r in volumes) == pytest.approx(90.0)


def test_a_altura_da_copa_e_a_pedida() -> None:
    args = PECAS["copa"].variacoes[0][1]
    assert args["copa"] == ["1.2m", "1m", "1.9m"]
    assert altura_m(ir_da_composicao(de_uma_peca("copa", args))) == pytest.approx(2.9, abs=1 / PPM)


def test_os_ramos_que_caem_fazem_a_cortina() -> None:
    """Com ``pende``, ramos finos caem em volta da copa (na frente, atrás e dos lados), de dentro da folhagem até
    abaixo do elipsoide, sem entrar no chão."""
    a = {**COPA_DE_TESTE, "pende": 2.5}
    lobulos = tufos(Stream(1), a)[:7]
    cortina = ramos(Stream(1), a, lobulos)
    centros = {c[2] for c, _ in sorted(lobulos, key=lambda v: v[0][2])[:5]}
    assert len(cortina) == 5 * 5 and all(alto[2] in centros for alto, _, _ in cortina)  # saem de dentro dos lóbulos
    pontas = [ponta[2] for _, ponta, _ in cortina]
    assert min(pontas) > 0 and max(pontas) - min(pontas) >= 3  # nenhum chega ao chão, e a barra é desigual
    assert min(pontas) < min(c[2] - r[2] for c, r in lobulos) - 5
    assert max(raio for _, _, raio in cortina) < min(r[0] for _, r in lobulos) / 3


def test_controle_sem_pende_nao_ha_ramo_caindo() -> None:
    assert ramos(Stream(1), COPA_DE_TESTE, tufos(Stream(1), COPA_DE_TESTE)[:7]) == []


def _duas_massas(grupos: tuple[str, str]) -> tuple[float, float]:
    """Dois nós de copa lado a lado (o ``desvio``): a luminância média do nó da esquerda e a do nó da direita."""
    nos = [{"id": f"copa_{lado}", "peca": "copa", "grupo": grupo,
            "args": {"copa": ["60cm", "50cm", "50cm"], "desvio": [desvio, "0"]}}
           for lado, grupo, desvio in (("a", grupos[0], "-70cm"), ("b", grupos[1], "70cm"))]
    comp = validar({**json.loads(EXEMPLO.read_text(encoding="utf-8")), "categoria": "arbusto", "nos": nos,
                    "tracos": []}, Composicao, "teste")
    ir, style = ir_da_composicao(comp), estilo_base()
    q = quadro_de_repouso(ir, estilo_render(style), "S")
    brilho = np.zeros(65536)
    for p in style.palette:
        brilho[p.index] = 0.299 * p.rgba[0] + 0.587 * p.rgba[1] + 0.114 * p.rgba[2]
    medias = []
    for lado in ("copa_a", "copa_b"):
        dele = np.isin(q.dono, [i + 1 for i, p in enumerate(q.part_table) if p.startswith(lado)])
        medias.append(float(brilho[q.index][dele].mean()))
    return medias[0], medias[1]


def test_os_nos_do_mesmo_grupo_sao_uma_massa_de_luz() -> None:
    """A moita de duas massas: a do lado da luz é mais clara que a outra."""
    luz, sombra = _duas_massas(("moita", "moita"))
    assert luz >= 1.1 * sombra


def test_controle_em_grupos_diferentes_cada_no_tem_a_sua_luz() -> None:
    luz, sombra = _duas_massas(("uma", "outra"))
    assert luz < 1.08 * sombra


def _beira(recortada: bool, monkeypatch: pytest.MonkeyPatch) -> float:
    """Os pixels da beira da folhagem do exemplo sobre os pixels dela."""
    if not recortada:
        monkeypatch.setattr(pecas_copa, "_na_massa", lambda c: ("volume_sphere", f"massa_{c.grupo}"))
    comp = ler(EXEMPLO, Composicao)
    q = quadro_de_repouso(ir_da_composicao(comp), estilo_render(estilo_base()), "S")
    folhas = np.isin(q.dono, [i + 1 for i, p in enumerate(q.part_table) if p.startswith("copa_")])
    dentro = folhas.copy()
    dentro[1:] &= folhas[:-1]
    dentro[:-1] &= folhas[1:]
    dentro[:, 1:] &= folhas[:, :-1]
    dentro[:, :-1] &= folhas[:, 1:]
    return float((folhas & ~dentro).sum()) / float(folhas.sum())


def test_a_beira_da_folhagem_e_recortada(monkeypatch: pytest.MonkeyPatch) -> None:
    """A borda de cada volume sai em folhas: a folhagem tem bem mais beira que a dos volumes lisos (o controle)."""
    assert _beira(True, monkeypatch) >= 1.25 * _beira(False, monkeypatch)


def _copa_alta_e_estreita() -> int:
    """Os pixels que a copa alta e estreita põe fora do canvas (a sombra dela no chão desce mais que o fundo)."""
    ir = ir_da_composicao(de_uma_peca("copa", {"copa": ["60cm", "3m", "3.2m"], "perfil": "0.55"}))
    return quadro_de_repouso(ir, estilo_render(estilo_base()), "S").clipping_px


def test_a_copa_alta_e_estreita_cabe_no_quadro() -> None:
    assert _copa_alta_e_estreita() == 0


def test_controle_a_sombra_da_elipse_na_tela_sai_do_canvas(monkeypatch: pytest.MonkeyPatch) -> None:
    """O jeito de antes: o volume de folhagem se lançava como a elipse dele na tela, com metade da altura dele, e a
    do volume alto e estreito descia no chão mais que o fundo dele (o canvas pedia uma folga para isso)."""
    monkeypatch.setattr(sombra, "FOLHAGEM", frozenset())
    assert _copa_alta_e_estreita() > 0


def _sombra_da_copa_alta(semente: int) -> Mascara:
    """A sombra no chão inteira (sem a figura por cima) da árvore de copa alta e estreita, na vista S."""
    dado = json.loads(EXEMPLO.read_text(encoding="utf-8"))
    del dado["medidas"]
    comp = validar({**dado, "categoria": "arvore_grande", "semente": semente, "nos": [], "tracos": [],
                    "planta": {"habito": "excurrente", "altura": "10m", "largura": "2m"}}, Composicao, "teste")
    ir = ir_da_composicao(comp)
    cena = project_view(ir, rest_pose(Skeleton(ir.bones)), "S")
    return sombra._ground_projection(cena, estilo_render(estilo_base()).light, ir.canvas.width + 2 * MARGIN,
                                     ir.canvas.height + 2 * MARGIN)


def test_a_copa_alta_lanca_uma_sombra_so() -> None:
    """Cada volume da copa se lança inteiro pela luz (o alto vai mais longe): a sombra da copa alta é uma mancha só,
    junto com a do tronco, como a copa."""
    assert [flora.ilhas(_sombra_da_copa_alta(s)) for s in (1, 2, 3)] == [1, 1, 1]


def test_controle_a_elipse_na_tela_lanca_a_copa_alta_em_manchas(monkeypatch: pytest.MonkeyPatch) -> None:
    """O jeito de antes: cada volume no chão como a elipse dele na tela, curta, no centro lançado; os do alto da
    copa alta caem longe dos de baixo, e a sombra sai em manchas."""
    monkeypatch.setattr(sombra, "FOLHAGEM", frozenset())
    assert all(flora.ilhas(_sombra_da_copa_alta(s)) > 1 for s in (1, 2, 3))


def _conifera_chapada() -> Composicao:
    """O jeito antigo, sintético: a conífera como uma face chapada no plano da frente."""
    return de_uma_peca("poligono", {"pontos": [["-90cm", "0", "50cm"], ["90cm", "0", "50cm"], ["0", "0", "4m"]],
                                    "material": "agulha"})


def test_a_conifera_lanca_a_sombra_dela() -> None:
    """A sombra no chão da conífera é a do cone (uma mancha larga); a ponta é da altura pedida."""
    for _, args in PECAS["copa_conica"].variacoes:
        comp = de_uma_peca("copa_conica", args)
        m = leitura(comp, "n_")
        assert m["sombra_px"] >= 0.1 * m["figura_px"], args
    alta = PECAS["copa_conica"].variacoes[0][1]
    assert altura_m(ir_da_composicao(de_uma_peca("copa_conica", alta))) == pytest.approx(4.0, abs=1 / PPM)


def test_controle_a_conifera_chapada_lanca_uma_linha() -> None:
    m = leitura(_conifera_chapada(), "n")
    assert m["sombra_px"] < 0.1 * m["figura_px"]


def _pontas(fundo: str, fase: str = "0.5") -> list[tuple[float, float]]:
    args = {**PECAS["galhos"].variacoes[0][1], "fundo": fundo, "bifurca": "0", "fase": fase}
    ir = ir_da_composicao(de_uma_peca("galhos", args))
    pontas = [p.geometry.points_q8[-1] for p in ir.parts if p.geometry.type == "tapered_polyline"]
    return [(p[0] / 256, p[1] / 256) for p in pontas]


def test_os_galhos_abrem_em_volta_do_tronco() -> None:
    """Uma ponta em cada fatia da volta: há galho para a frente, para trás e para os dois lados."""
    pontas = _pontas("1")
    fatias = {int((math.degrees(math.atan2(x, y)) % 360) // (360 / len(pontas))) for x, y in pontas}
    assert len(pontas) == 5 and len(fatias) >= 4
    assert min(y for _, y in pontas) < -5 and max(y for _, y in pontas) > 5


def _para_a_camera(pontas: list[tuple[float, float]]) -> int:
    """As pontas a menos de 20° da frente (o galho que desce na tela por cima do tronco, como uma escora)."""
    return sum(1 for x, y in pontas if abs(math.degrees(math.atan2(x, y))) < 20)


def test_nenhum_galho_aponta_para_a_camera() -> None:
    assert _para_a_camera(_pontas("1")) == 0


def test_controle_com_a_fase_zero_um_galho_aponta_para_a_camera() -> None:
    assert _para_a_camera(_pontas("1", "0")) == 1


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


# --- a flora variada (mudança 21): o controle de cada propriedade é o jeito de antes

ABERTA = PECAS["copa_aberta"].variacoes[0][1]


def _lados_da_folhagem(comp: Composicao) -> tuple[float, float]:
    """A luminância média da folhagem no terço do lado da luz (a esquerda) e no terço do lado da sombra."""
    ir, style = ir_da_composicao(comp), estilo_base()
    q = quadro_de_repouso(ir, estilo_render(style), "S")
    brilho = {p.index: 0.299 * p.rgba[0] + 0.587 * p.rgba[1] + 0.114 * p.rgba[2] for p in style.palette}
    folhas = [i + 1 for i, p in enumerate(q.part_table) if p.startswith("n_")]
    ys, xs = np.nonzero(np.isin(q.dono, folhas))
    v = np.array([brilho[int(i)] for i in q.index[ys, xs]])
    terco = (xs.max() - xs.min() + 1) / 3
    return float(v[xs < xs.min() + terco].mean()), float(v[xs > xs.max() - terco].mean())


def test_a_folhagem_tem_a_luz_de_uma_massa() -> None:
    """As nuvens da copa aberta são uma massa de luz só: a do lado da luz é clara e a do lado da sombra, escura."""
    luz, sombra = _lados_da_folhagem(de_uma_peca("copa_aberta", ABERTA))
    assert luz >= 1.15 * sombra


def test_controle_cada_tufo_com_a_sua_luz_nao_tem_lado(monkeypatch: pytest.MonkeyPatch) -> None:
    """O jeito de antes: cada volume sombreado sozinho, como uma bola (o brócolis)."""
    monkeypatch.setattr(pecas_copa, "_na_massa", lambda _c: ("volume_sphere",))
    luz, sombra = _lados_da_folhagem(de_uma_peca("copa_aberta", ABERTA))
    assert luz < 1.08 * sombra


def _com_a_semente(semente: int) -> flora.Leitura:
    dado = json.loads(EXEMPLO.read_text(encoding="utf-8"))
    return critica.medir(validar({**dado, "semente": semente, "tracos": []}, Composicao, "teste"))[0]


def test_outra_semente_da_outra_copa_da_mesma_especie() -> None:
    """A semente muda os lóbulos: as silhuetas diferem, sem deixar de ser a mesma árvore."""
    lidas = [_com_a_semente(s) for s in range(77, 83)]
    pares = [flora.semelhanca(a.assinatura, b.assinatura) for i, a in enumerate(lidas) for b in lidas[:i]]
    assert max(pares) < flora.PARECIDA and min(pares) > 0.5
    assert all(m.simetria < flora.ESPELHADA and m.solidez < flora.LISA for m in lidas)


def test_controle_a_mesma_semente_da_a_mesma_copa() -> None:
    assert flora.semelhanca(_com_a_semente(77).assinatura, _com_a_semente(77).assinatura) == 1.0


def _larguras_da_copa(perfil: float) -> tuple[float, float, float]:
    """Dos lóbulos (sem os raminhos): o alcance para os lados no terço de cima e no de baixo, e o ponto mais baixo."""
    a = {**COPA_DE_TESTE, "tufos": 12, "tamanho": 0.3, "irregular": 0.0, "raminhos": 0, "perfil": perfil}
    lobulos = tufos(Stream(3), a)

    def alcance(de: float, ate: float) -> float:
        return max((math.hypot(c[0], c[1]) + r[0] for c, r in lobulos if de <= c[2] - 60.0 < ate), default=0.0)

    return alcance(8.0, 31.0), alcance(-31.0, -8.0), min(c[2] - r[2] for c, r in lobulos)


def test_o_perfil_faz_a_gota_e_o_guarda_sol() -> None:
    em_cima, embaixo, _ = _larguras_da_copa(1.0)
    assert em_cima < 0.75 * embaixo  # a gota: fina no alto
    _, embaixo, fundo = _larguras_da_copa(-1.0)
    assert embaixo == 0.0 and fundo > 45.0  # o guarda-sol: nada abaixo do meio da copa


def test_controle_a_copa_redonda_nao_afina_nem_perde_a_metade_de_baixo() -> None:
    em_cima, embaixo, fundo = _larguras_da_copa(0.0)
    assert em_cima >= 0.75 * embaixo > 0 and fundo < 45.0


def _aberta_e_fechada() -> tuple[int, int]:
    """Os pixels dos galhos à mostra sob a copa aberta e, nos mesmos galhos, sob a copa em massa."""
    out = []
    for nome, args in (("copa_aberta", ABERTA), ("copa", {"copa": ["1.3m", "70cm", "2.3m"]})):
        comp = de_uma_peca(nome, args)
        if nome == "copa":
            dado = de_uma_peca("copa_aberta", ABERTA).model_dump(mode="json")
            comp = validar({**dado, "nos": [*dado["nos"][:-1], {"id": "n", "peca": nome, "args": args}]}, Composicao,
                           "controle")
        q = quadro_de_repouso(ir_da_composicao(comp), estilo_render(estilo_base()), "S")
        out.append(sum(n for p, n in q.visiveis.items() if p.startswith("galhos_")))
    return out[0], out[1]


def test_a_copa_aberta_deixa_os_galhos_a_mostra() -> None:
    aberta, _ = _aberta_e_fechada()
    m = critica.medir(de_uma_peca("copa_aberta", ABERTA))[0]
    assert aberta >= 60 and m.solidez < 0.8


def test_controle_a_copa_em_massa_cobre_os_galhos() -> None:
    aberta, fechada = _aberta_e_fechada()
    assert fechada < 0.5 * aberta


def _pontas_da_nuvem(material: str, semente: int) -> int:
    """As pontas da silhueta de uma nuvem só da copa aberta (num galho só), na vista S: no perfil polar em volta do
    centro dela (72 setores), os máximos que passam 1,5 px dos vales dos dois lados."""
    dado = de_uma_peca("copa_aberta", {**ABERTA, "material": material}).model_dump(mode="json")
    for no in dado["nos"]:
        if no["peca"] == "galhos":
            no["args"]["n"] = "1"
    ir = ir_da_composicao(validar({**dado, "semente": semente}, Composicao, "teste"))
    cheias = mascaras(project_view(ir, rest_pose(Skeleton(ir.bones)), "S"), estilo_render(estilo_base()),
                      ir.canvas.width, ir.canvas.height)
    ys, xs = np.nonzero(np.logical_or.reduce([m for p, m in cheias.items() if p.startswith("n_")]))
    setor = ((np.arctan2(ys - ys.mean(), xs - xs.mean()) + np.pi) / (2 * np.pi) * 72).astype(int) % 72
    r = np.zeros(72)
    np.maximum.at(r, setor, np.hypot(ys - ys.mean(), xs - xs.mean()))
    vales = [(min(r[(i - k) % 72] for k in range(1, 6)), min(r[(i + k) % 72] for k in range(1, 6))) for i in range(72)]
    return sum(1 for i in range(72) if r[i] >= r[(i + 1) % 72] and r[i] > r[i - 1] and r[i] - max(vales[i]) >= 1.5)


def test_a_nuvem_de_agulha_tem_a_beira_em_pontas() -> None:
    """A copa aberta de agulha (o pinheiro de galhos à mostra): cada nuvem é um tufo chato de leques, e a silhueta
    dela tem muitas pontas finas, como a conífera; a de folha larga segue em lóbulos (poucas)."""
    assert all(_pontas_da_nuvem("copa_agulha", s) >= 10 for s in range(2, 7))
    assert all(_pontas_da_nuvem("copa_folhosa", s) <= 8 for s in range(2, 7))


def test_controle_a_nuvem_de_agulha_em_lobulos_le_como_folha(monkeypatch: pytest.MonkeyPatch) -> None:
    """O jeito de antes: a nuvem de agulha era a de folha em outra cor, em lóbulos redondos."""
    monkeypatch.setattr(pecas_copa, "AGULHA", "<nenhum>")
    assert all(_pontas_da_nuvem("copa_agulha", s) <= 8 for s in range(2, 7))


def _solidez_da_conifera(**args: str) -> float:
    alta = PECAS["copa_conica"].variacoes[0][1]
    return critica.medir(de_uma_peca("copa_conica", {**alta, **args}))[0].solidez


def test_a_saia_da_conifera_e_recortada() -> None:
    """As pontas recortam a silhueta: a conífera enche pouco do fecho convexo dela."""
    assert _solidez_da_conifera() < 0.78


def test_controle_a_saia_lisa_e_um_cone() -> None:
    assert _solidez_da_conifera(recorte="0", cai="0", irregular="0") > 0.84


def _saidas(sobe: str) -> list[float]:
    """A altura de onde sai cada galho (px)."""
    args = {**PECAS["galhos"].variacoes[0][1], "bifurca": "0", "sobe": sobe}
    ir = ir_da_composicao(de_uma_peca("galhos", args))
    return sorted(p.geometry.points_q8[0][2] / 256 for p in ir.parts if p.geometry.type == "tapered_polyline")


def test_os_galhos_saem_escalonados() -> None:
    saidas = _saidas("90cm")
    assert saidas[-1] - saidas[0] == pytest.approx(0.9 * PPM, abs=1) and len(set(saidas)) == len(saidas)


def test_controle_sem_sobe_os_galhos_saem_do_mesmo_ponto() -> None:
    assert len(set(_saidas("0"))) == 1


# --- o tronco com forma de tronco (mudança 20): o controle é o tronco liso, o cone do `pixel-engine`

CILINDRO = {"altura": "2m", "base": "60cm", "topo": "60cm", "casca": "casca"}
LISO = {"pe": "0", "irregular": "0"}


def _fileiras(args: dict[str, Any], parte: str = "n") -> list[tuple[int, int]]:
    """A primeira e a última coluna do tronco em cada fileira da tela, de cima para baixo (a máscara inteira)."""
    ir, est = ir_da_composicao(de_uma_peca("tronco_em_pe", args)), estilo_render(estilo_base())
    m = mascaras(project_view(ir, rest_pose(Skeleton(ir.bones)), "S"), est, ir.canvas.width, ir.canvas.height)[parte]
    return [(int(c[0]), int(c[-1])) for c in (np.flatnonzero(f) for f in m) if c.size]


def _larguras(args: dict[str, Any], de: float, ate: float) -> list[int]:
    """As larguras das fileiras entre as frações ``de`` e ``ate`` da altura na tela (0 = o alto)."""
    f = _fileiras(args)
    return [b - a + 1 for a, b in f[round(de * len(f)):round(ate * len(f))]]


def _pe_sobre_o_fuste(args: dict[str, Any]) -> float:
    return max(_larguras(args, 0.85, 1.0)) / float(np.median(_larguras(args, 0.4, 0.6)))


def test_o_pe_do_tronco_abre() -> None:
    """Por padrão o tronco tem pé: no chão ele é mais largo que o fuste."""
    assert _pe_sobre_o_fuste({**CILINDRO, "irregular": "0"}) >= 1.2


def test_controle_o_tronco_liso_nao_tem_pe() -> None:
    assert _pe_sobre_o_fuste({**CILINDRO, **LISO}) <= 1.1


def _folga_do_fuste(irregular: str) -> int:
    fuste = _larguras({**CILINDRO, "pe": "0", "irregular": irregular}, 0.2, 0.8)
    return max(fuste) - min(fuste)


def test_o_fuste_engrossa_e_afina() -> None:
    assert _folga_do_fuste("0.2") >= 3


def test_controle_o_fuste_liso_e_reto() -> None:
    assert _folga_do_fuste("0") <= 1


def _eixo(curva: str) -> tuple[float, float, float]:
    """O meio do tronco na tela a 3/4, a 1/4 e no alto da altura, a partir do meio do pé (px)."""
    f = _fileiras({**CILINDRO, **LISO, "curva": curva})
    meio = [(a + b) / 2 for a, b in f]
    pe = meio[-6]
    return meio[round(0.3 * len(f))] - pe, meio[round(0.72 * len(f))] - pe, meio[3] - pe


def test_o_tronco_ondula_e_volta_ao_prumo() -> None:
    """Com ``curva``, o eixo vai para um lado embaixo e para o outro em cima, e o alto fica sobre o pé."""
    em_cima, embaixo, alto = _eixo("15cm")
    assert em_cima <= -3 and embaixo >= 3 and abs(alto) <= 1.5


def test_controle_o_tronco_sem_curva_fica_no_prumo() -> None:
    assert all(abs(v) <= 1 for v in _eixo("0"))


def _velho(**args: str) -> tuple[dict[str, int], int]:
    """Os pixels à mostra de cada raiz e nó, e quanto a figura passa da largura do tronco no chão."""
    velho = {**PECAS["tronco_em_pe"].variacoes[2][1], **args}
    ir, est = ir_da_composicao(de_uma_peca("tronco_em_pe", velho)), estilo_render(estilo_base())
    q = quadro_de_repouso(ir, est, "S")
    figura = np.flatnonzero(((q.alpha == 255) & (q.index != est.materials["sombra"].ramp[0])).any(axis=0))
    tronco = _fileiras(velho)
    passa = int(figura[-1] - figura[0] + 1) - max(b - a + 1 for a, b in tronco)
    return {p: n for p, n in q.visiveis.items() if "_raiz_" in p or "_no_" in p}, passa


def test_as_raizes_e_os_nos_aparecem() -> None:
    partes, passa = _velho()
    raizes = [p for p in partes if "_raiz_" in p]
    assert len(raizes) >= 4 and sum(1 for p in partes if "_no_" in p) == 2 and passa >= 8


def test_controle_sem_raizes_nem_nos_o_tronco_e_so_o_fuste() -> None:
    assert _velho(raizes="0", nos="0") == ({}, 0)


def _veio(casca: str, lisa: str) -> tuple[int, int]:
    """Os sulcos da casca (os pixels que diferem da casca lisa no mesmo tronco): os pares de sulco um sobre o outro
    e os pares lado a lado."""
    quadros = []
    for material in (casca, lisa):
        ir = ir_da_composicao(de_uma_peca("tronco_em_pe", {**CILINDRO, **LISO, "casca": material}))
        quadros.append(quadro_de_repouso(ir, estilo_render(estilo_base()), "S").index)
    sulco = quadros[0] != quadros[1]
    return int((sulco[1:] & sulco[:-1]).sum()), int((sulco[:, 1:] & sulco[:, :-1]).sum())


def test_a_casca_sulcada_tem_o_veio_em_pe_e_a_anelada_deitado() -> None:
    """Cada casca é o controle da outra: os sulcos de uma correm ao longo da altura, os da outra em volta."""
    em_pe, deitado = _veio("casca_sulcada", "casca")
    assert em_pe >= 40 and em_pe >= 3 * deitado
    em_pe, deitado = _veio("casca_anelada", "casca_clara")
    assert deitado >= 12 and deitado >= 3 * em_pe


def test_o_tronco_velho_desenha_as_quatro_vistas() -> None:
    comp = de_uma_peca("tronco_em_pe", PECAS["tronco_em_pe"].variacoes[2][1])
    quatro = validar({**comp.model_dump(mode="json"), "vistas": dict.fromkeys(("S", "E", "N", "W"), {})}, Composicao,
                     "teste")
    ir, est = ir_da_composicao(quatro), estilo_render(estilo_base())
    assert all(quadro_de_repouso(ir, est, d).clipping_px == 0 for d in ir.views)


def _viradas_das_raizes() -> list[float]:
    """Quanto cada raiz do tronco velho vira do pé à ponta, vista de cima (graus)."""
    ir = ir_da_composicao(de_uma_peca("tronco_em_pe", PECAS["tronco_em_pe"].variacoes[2][1]))
    out = []
    for p in ir.parts:
        if "_raiz_" in p.id and p.geometry.type == "tapered_polyline":
            pts = p.geometry.points_q8
            pe, ponta = math.atan2(pts[1][0], pts[1][1]), math.atan2(pts[-1][0], pts[-1][1])
            out.append(abs(math.degrees(math.atan2(math.sin(ponta - pe), math.cos(ponta - pe)))))
    return out


def test_a_raiz_deita_em_curva() -> None:
    """A raiz vira para um lado até a ponta: não é uma lâmina reta saindo do pé."""
    viradas = _viradas_das_raizes()
    assert len(viradas) == 5 and min(viradas) >= 15


def test_controle_a_raiz_sem_torcer_e_uma_lamina_reta(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pecas_tronco, "RAIZ_TORCE", (0, 0))
    assert max(_viradas_das_raizes()) < 1


def _tom_mais_claro(ganho: float | None, monkeypatch: pytest.MonkeyPatch) -> float:
    """A parte da folhagem do exemplo no tom mais claro da rampa dela."""
    if ganho is not None:
        monkeypatch.setattr(volume, "GANHO", ganho)
    style = estilo_base()
    q = quadro_de_repouso(ir_da_composicao(ler(EXEMPLO, Composicao)), estilo_render(style), "S")
    folhas = np.isin(q.dono, [i + 1 for i, p in enumerate(q.part_table) if p.startswith("copa_")])
    claro = next(m for m in style.materials if m.id == "copa_folhosa").ramp[-1]
    return float((q.index[folhas] == claro).mean())


def test_o_relevo_da_massa_chega_ao_tom_mais_claro(monkeypatch: pytest.MonkeyPatch) -> None:
    """O alto dos lóbulos do lado da luz usa o tom mais claro: a massa não é uma mancha de dois tons."""
    com = _tom_mais_claro(None, monkeypatch)
    sem = _tom_mais_claro(1.0, monkeypatch)  # o controle: sem o ganho, o claro é só o pixel solto da textura
    assert com >= 0.04 and com >= 2 * sem


def _folhagem_da_moita_pequena(folha_grande: int | None, monkeypatch: pytest.MonkeyPatch) -> int:
    """Os pixels de folhagem de uma moita de 60 cm (lóbulos de menos de 150 px)."""
    if folha_grande is not None:
        monkeypatch.setattr(montagem, "FOLHA_GRANDE", folha_grande)
    comp = de_uma_peca("copa", {"copa": ["30cm", "22cm", "22cm"], "tufos": "6", "tamanho": "0.45"})
    q = quadro_de_repouso(ir_da_composicao(comp), estilo_render(estilo_base()), "S")
    return int(np.isin(q.dono, [i + 1 for i, p in enumerate(q.part_table) if p != "n_miolo"]).sum())


def test_a_folha_da_moita_pequena_e_de_um_pixel(monkeypatch: pytest.MonkeyPatch) -> None:
    """A beira recortada vai na medida da peça: com a folha de 2 px (o controle) a moita pequena perde a forma."""
    fina = _folhagem_da_moita_pequena(None, monkeypatch)
    grossa = _folhagem_da_moita_pequena(0, monkeypatch)
    assert fina >= 1.08 * grossa


def test_a_massa_larga_escurece_de_um_lado_ao_outro(monkeypatch: pytest.MonkeyPatch) -> None:
    """A luz da massa vem mais de lado que a de uma bola: na moita de dois tufos o da luz é bem mais claro que o
    outro. O controle é a luz da bola (o brilho se repetia em cada tufo)."""
    luz, sombra = _duas_massas(("moita", "moita"))
    monkeypatch.setattr(tons, "LUZ_DA_MASSA", volume.SPH_LIGHT)
    luz_da_bola, sombra_da_bola = _duas_massas(("moita", "moita"))
    assert luz / sombra >= 1.2 and luz / sombra >= luz_da_bola / sombra_da_bola + 0.05
