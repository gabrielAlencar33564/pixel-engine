"""A flora de lâminas e de pontos (mudança 21): a touceira lê como lâminas e não como massa, a folha larga é mais
que um traço, a folha em pena é serrilhada, a folha lisa é chapada, o claro fica do lado da luz da tela em toda
vista, a palma nasce no alto do tronco, e o salpico cai onde a câmera vê, por dentro da figura; nas pontas, a flor
fica no alto e as flores não se amontoam; nenhuma folha larga aponta para a câmera de uma vista; a nervura corre no
eixo, e as folhas lisas vizinhas não se juntam. Os controles: a moita em massa, a lâmina fina, a folha lisa
sombreada, o lado da luz do mundo, o pé no chão, o ponto na face por fora da folhagem, o salpico sorteado na volta
toda, a escolha das pontas pela normal, a flor sem distância, a frente livre só na S, a nervura erguida e a folha
lisa no grupo do nó com o tom sorteado."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pytest

from pixel_forge.application.catalogo import de_uma_peca
from pixel_forge.application.estilo import estilo_base
from pixel_forge.application.quadros import quadro_de_repouso
from pixel_forge.contracts.carregar import validar
from pixel_forge.contracts.composicao import Composicao
from pixel_forge.design.asset import ir_da_composicao
from pixel_forge.design.escala import PPM
from pixel_forge.design.kit import pecas_ervas
from pixel_forge.design.kit.registro import PECAS
from pixel_forge.design.vistas import AZIMUTE
from pixel_forge.quality import flora
from pixel_forge.raster.estilo import estilo_render
from pixel_forge.raster.renderer import Quadro

CAPIM = PECAS["touceira"].variacoes[0][1]
FLORES = PECAS["salpico"].variacoes[0][1]


def _quadro(comp: Composicao) -> Quadro:
    return quadro_de_repouso(ir_da_composicao(comp), estilo_render(estilo_base()), "S")


def test_a_touceira_e_de_laminas() -> None:
    """A silhueta é de lâminas: enche pouco do fecho convexo dela, e cada lâmina é uma parte."""
    for nome, args in PECAS["touceira"].variacoes:
        comp = de_uma_peca("touceira", args)
        assert flora.solidez(_quadro(comp).dono != 0) < 0.8, nome
        laminas = [p for p in ir_da_composicao(comp).parts if not p.id.endswith(("_pena", "_nervura", "_miolo"))]
        assert len(laminas) == int(args["n"])


def test_controle_a_moita_em_massa_enche_o_fecho() -> None:
    moita = PECAS["copa"].variacoes[-1][1]
    assert flora.solidez(_quadro(de_uma_peca("copa", moita)).dono != 0) > 0.85


def _pixels(**args: Any) -> int:
    return int((_quadro(de_uma_peca("touceira", {**CAPIM, "altura": ["50cm", "80cm"], **args})).dono != 0).sum())


def test_a_folha_larga_e_mais_que_um_traco() -> None:
    assert _pixels(largura="20cm") >= 1.5 * _pixels()


def _borda_sobre_a_area(pena: bool) -> float:
    """Os pixels da borda da figura sobre os da figura: a folha serrilhada tem mais borda que a lisa."""
    args = {**CAPIM, "altura": ["80cm", "1.1m"], "n": "5", "abre": "0.8", "largura": "30cm", "pena": pena}
    figura = _quadro(de_uma_peca("touceira", args)).dono != 0
    dentro = figura.copy()
    dentro[1:] &= figura[:-1]
    dentro[:-1] &= figura[1:]
    dentro[:, 1:] &= figura[:, :-1]
    dentro[:, :-1] &= figura[:, 1:]
    return float((figura & ~dentro).sum()) / float(figura.sum())


def test_a_folha_em_pena_e_serrilhada() -> None:
    assert _borda_sobre_a_area(True) >= 1.15 * _borda_sobre_a_area(False)


def _pes(pe: list[str]) -> set[float]:
    """A altura de onde sai cada lâmina, com um tronco de 2 m por baixo (a touceira no ar é recusada)."""
    dado = de_uma_peca("touceira", {**CAPIM, "raio": "0", "pe": pe}).model_dump(mode="json")
    tronco = {"id": "tronco", "peca": "tronco_em_pe",
              "args": {"altura": "2m", "base": "26cm", "topo": "18cm", "casca": "casca"}}
    ir = ir_da_composicao(validar({**dado, "nos": [tronco, *dado["nos"]]}, Composicao, "teste"))
    return {p.geometry.points_q8[0][2] / 256 for p in ir.parts if p.geometry.type == "polyline"}


def test_a_touceira_nasce_no_alto_de_um_tronco() -> None:
    """Com o pé no alto (a palma), toda lâmina sai de lá."""
    assert _pes(["0", "0", "2m"]) == {round(2 * PPM * 256) / 256}


def test_controle_por_padrao_a_touceira_nasce_no_chao() -> None:
    assert _pes(["0", "0", "0"]) == {0.0}


def _do_lado_de_la(vistas: tuple[str, ...]) -> tuple[int, int]:
    """Os pontos do salpico, e deles os que caem na metade de trás da moita (longe da câmera da vista S)."""
    dado = de_uma_peca("salpico", FLORES).model_dump(mode="json")
    ir = ir_da_composicao(validar({**dado, "vistas": dict.fromkeys(vistas, {})}, Composicao, "teste"))
    pontos = [p.geometry.center_q8 for p in ir.parts if p.id.startswith("n_") and p.geometry.type == "ellipse"]
    return len(pontos), sum(1 for p in pontos if p[1] < -5 * 256)


def test_o_salpico_cai_do_lado_da_camera() -> None:
    """Na composição de vista única, nenhum ponto cai atrás da moita."""
    assert _do_lado_de_la(("S",)) == (int(FLORES["n"]), 0)


def test_controle_na_volta_toda_ha_pontos_do_lado_de_la() -> None:
    """Com as 4 vistas os pontos se espalham pela volta: cada vista mostra os dela."""
    assert _do_lado_de_la(("S", "E", "N", "W"))[1] >= 2


def _no_contorno(vistas: tuple[str, ...]) -> tuple[int, int]:
    """Das flores e dos frutos na moita (seis sementes, cada vista): os que aparecem por dentro da figura e os que
    tocam o contorno dela."""
    dentro = contorno = 0
    for _, args in PECAS["salpico"].variacoes[:2]:
        for semente in range(6):
            dado = {**de_uma_peca("salpico", args).model_dump(mode="json"), "semente": semente,
                    "vistas": dict.fromkeys(vistas, {})}
            ir = ir_da_composicao(validar(dado, Composicao, "teste"))
            for v in ir.views:
                q = quadro_de_repouso(ir, estilo_render(estilo_base()), v)
                pts = [p for p in q.part_table if p.startswith("n_")]
                contorno += sum(1 for p in pts if q.na_silhueta.get(p, 0))
                dentro += sum(1 for p in pts if q.visiveis.get(p, 0) and not q.na_silhueta.get(p, 0))
    return dentro, contorno


def test_o_salpico_cai_por_dentro_da_figura() -> None:
    """Os pontos da face da copa caem sobre a massa: na vista única, de cada 8 que aparecem por dentro, no máximo um
    toca o contorno; nas quatro vistas, no máximo um de cada 2 (a folhagem cobre o da beira de cada vista)."""
    dentro, contorno = _no_contorno(("S",))
    assert contorno <= dentro / 8
    dentro, contorno = _no_contorno(("S", "E", "N", "W"))
    assert contorno <= dentro / 2


def test_controle_o_ponto_na_face_cai_no_contorno(monkeypatch: pytest.MonkeyPatch) -> None:
    """Com o ponto na face do volume, por fora da folhagem (o jeito antigo), o da beira fica no contorno."""
    monkeypatch.setattr(pecas_ervas, "MERGULHO", 0.0)
    dentro, contorno = _no_contorno(("S",))
    assert contorno > dentro / 2


def test_controle_sorteado_na_volta_toda_o_ponto_cai_no_contorno(monkeypatch: pytest.MonkeyPatch) -> None:
    """Sem a escolha dos pontos que a câmera vê no meio da figura, os da beira e os do lado de lá entram."""
    monkeypatch.setattr(pecas_ervas, "_beiras", lambda normais, _azimutes: [0.0] * len(normais))
    dentro, contorno = _no_contorno(("S",))
    assert contorno > dentro / 8


def test_o_salpico_na_ponta_das_laminas() -> None:
    """A âncora das pontas da touceira leva a flor e a espiga."""
    comp = validar({**de_uma_peca("touceira", CAPIM).model_dump(mode="json"), "nos": [
        {"id": "pe", "peca": "touceira", "args": {**CAPIM, "n": "6"}},
        {"id": "flor", "peca": "salpico", "args": {"em": "pe.pontas", "material": "ambar", "n": "6"}}]},
        Composicao, "teste")
    q = _quadro(comp)
    assert sum(1 for p in q.part_table if p.startswith("flor_") and q.visiveis.get(p, 0)) >= 4


def _sombra_no_chao() -> int:
    """Os pixels da sombra que a touceira lança no chão."""
    style = estilo_base()
    q = _quadro(de_uma_peca("touceira", {**CAPIM, "altura": ["50cm", "80cm"]}))
    chao = next(m for m in style.materials if m.id == "sombra").ramp[0]
    return int(((q.index == chao) & (q.alpha == 255) & (q.dono == 0)).sum())


def test_a_touceira_lanca_a_sombra_dela() -> None:
    """A lâmina fina não é detalhe: a sombra dela no chão assenta a planta."""
    assert _sombra_no_chao() >= 20


def test_controle_a_lamina_de_detalhe_nao_lanca_sombra(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pecas_ervas, "FIO", ("flat", "detail", "no_outline"))
    assert _sombra_no_chao() == 0


def _raios_do_ponto(**args: str) -> tuple[int, int]:
    ir = ir_da_composicao(de_uma_peca("salpico", {**FLORES, **args}))
    raios = next(p.geometry.radii_q8 for p in ir.parts if p.id.startswith("n_") and p.geometry.type == "ellipse")
    return raios[0], raios[2]


def test_o_ponto_alongado_e_a_espiga_em_pe() -> None:
    largo, alto = _raios_do_ponto(alonga="3")
    assert abs(alto - 3 * largo) <= 2  # q8: 1/128 px de arredondamento


def test_controle_por_padrao_o_ponto_e_redondo() -> None:
    largo, alto = _raios_do_ponto()
    assert alto == largo


def _claras_de_cada_lado() -> tuple[int, int]:
    """As lâminas claras de uma touceira grande que abrem para a esquerda da tela (a luz) e para a direita."""
    ir = ir_da_composicao(de_uma_peca("touceira", {**CAPIM, "n": "40", "raio": "0"}))
    lados = [p.geometry.points_q8[-1][0] for p in ir.parts
             if p.material == "capim_claro" and p.geometry.type == "polyline"]
    return sum(1 for x in lados if x < 0), sum(1 for x in lados if x > 0)


def test_o_claro_das_laminas_fica_do_lado_da_luz() -> None:
    esquerda, direita = _claras_de_cada_lado()
    assert esquerda >= 6 and esquerda >= 3 * direita


def test_controle_so_com_o_sorteio_o_claro_cai_dos_dois_lados(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pecas_ervas, "LADO_DA_LUZ", 0.0)
    esquerda, direita = _claras_de_cada_lado()
    assert esquerda >= 3 and direita >= 3


def _claras_em_cada_vista() -> dict[str, tuple[int, int]]:
    """Na touceira grande de quatro vistas, as lâminas claras de cada vista (o material dela ali) que abrem para a
    esquerda da tela dessa vista e para a direita."""
    dado = {**de_uma_peca("touceira", {**CAPIM, "n": "40", "raio": "0"}).model_dump(mode="json"),
            "vistas": dict.fromkeys(("S", "E", "N", "W"), {})}
    ir = ir_da_composicao(validar(dado, Composicao, "teste"))
    out: dict[str, tuple[int, int]] = {}
    for v, vista in ir.views.items():
        a = math.radians(AZIMUTE[v] / 1000)
        lados = [x * math.cos(a) - y * math.sin(a) for p in ir.parts if p.geometry.type == "polyline"
                 for x, y, _ in [p.geometry.points_q8[-1]] if vista.materials.get(p.id, p.material) == "capim_claro"]
        out[v] = (sum(1 for x in lados if x < 0), sum(1 for x in lados if x > 0))
    return out


def test_o_claro_das_laminas_fica_do_lado_da_luz_em_toda_vista() -> None:
    """A luz vem da esquerda da tela em toda vista: a lâmina troca de tom com a vista (o material da vista)."""
    for v, (esquerda, direita) in _claras_em_cada_vista().items():
        assert esquerda >= 6 and esquerda >= 3 * direita, v


def test_controle_com_o_lado_da_luz_do_mundo_o_claro_vira_nas_outras_vistas(monkeypatch: pytest.MonkeyPatch) -> None:
    """Com o lado da luz tirado do mundo (o da vista S), na vista N o claro cai todo do lado da sombra."""
    monkeypatch.setattr(pecas_ervas, "_lado_da_luz", lambda az, _azimute: -math.sin(az))
    esquerda, direita = _claras_em_cada_vista()["N"]
    assert direita >= 3 * esquerda


FOLHAS = {**CAPIM, "altura": ["60cm", "90cm"], "n": "8", "abre": "0.8", "cai": "0.5", "largura": "16cm", "raio": "0"}


def _nervuras_a_mostra(largura: str, pena: bool) -> int:
    """As folhas com a nervura à mostra (a parte ``_pena`` ou ``_nervura`` com pixel)."""
    q = _quadro(de_uma_peca("touceira", {**FOLHAS, "largura": largura, "pena": pena}))
    return sum(1 for p in q.part_table if p.endswith(("_pena", "_nervura")) and q.visiveis.get(p, 0) >= 3)


@pytest.mark.parametrize("pena", [True, False])
def test_a_folha_larga_tem_a_nervura_a_mostra(pena: bool) -> None:
    """Cada folha larga, em pena ou lisa, se lê pela nervura dela, por cima do corpo."""
    assert _nervuras_a_mostra("16cm", pena) >= 6


def test_controle_a_lamina_fina_nao_tem_nervura() -> None:
    assert _nervuras_a_mostra("0", False) == 0


def _faixa_clara_na_folha_lisa() -> int:
    """Os pixels do tom claro da rampa nas folhas lisas do material comum: a peça lisa sombreada tem a faixa de luz
    de um lado e a de sombra do outro (lê como tubo); a chapada é de um tom só, o do meio."""
    comp = de_uma_peca("touceira", FOLHAS)
    comuns = {p.id for p in ir_da_composicao(comp).parts if p.material == "capim" and not p.id.endswith("_nervura")}
    claro = next(m for m in estilo_base().materials if m.id == "capim").ramp[-1]
    q = _quadro(comp)
    return sum(int(((q.dono == k + 1) & (q.index == claro)).sum()) for k, p in enumerate(q.part_table) if p in comuns)


def test_a_folha_lisa_e_chapada() -> None:
    assert _faixa_clara_na_folha_lisa() == 0


def test_controle_a_folha_lisa_sombreada_tem_a_faixa_de_tubo(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pecas_ervas, "FOLHA_LISA", ("no_inner_outline",))
    assert _faixa_clara_na_folha_lisa() >= 5


def _mais_perto_da_frente(semente: int) -> float:
    """O ângulo (graus) entre a câmera e a folha larga que mais aponta para ela."""
    dado = de_uma_peca("touceira", FOLHAS).model_dump(mode="json")
    ir = ir_da_composicao(validar({**dado, "semente": semente}, Composicao, "teste"))
    pontas = [p.geometry.points_q8[-1] for p in ir.parts if p.geometry.type == "tapered_polyline"]
    return min(abs(math.degrees(math.atan2(x, y))) for x, y, _ in pontas)


def test_nenhuma_folha_larga_aponta_para_a_camera() -> None:
    """A roseta deixa a frente livre: a folha de frente para a câmera viraria um talo em pé no meio dela."""
    assert min(_mais_perto_da_frente(s) for s in range(12)) >= 0.2 * 360 / 8 - 0.5


def test_controle_com_o_giro_solto_uma_folha_aponta_para_a_camera(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pecas_ervas, "FRENTE_LIVRE", 1.0)
    monkeypatch.setattr(pecas_ervas, "FOLGA", 0.0)
    assert min(_mais_perto_da_frente(s) for s in range(12)) < 0.2 * 360 / 8 - 0.5


def _miolo_a_mostra(largura: str) -> int:
    """Os pixels do miolo escuro no pé da touceira."""
    q = _quadro(de_uma_peca("touceira", {**FOLHAS, "largura": largura, "pena": largura != "0"}))
    return q.visiveis.get("n_miolo", 0)


def test_a_roseta_de_folhas_largas_tem_o_miolo_escuro() -> None:
    """O pé das folhas largas é o ponto mais escuro da planta: a roseta tem fundo."""
    assert _miolo_a_mostra("16cm") >= 4


def test_controle_a_touceira_de_laminas_finas_nao_tem_miolo() -> None:
    assert _miolo_a_mostra("0") == 0


# a flor nas pontas: o capim derivado pelo hábito (três portes) e o composto à mão (o do kit)
CAPINS_DE_FLOR = tuple({"planta": {"habito": "touceira", "altura": h, "largura": w}, "nos": []}
                       for h, w in (("40cm", "70cm"), ("45cm", "60cm"), ("30cm", "60cm"))) + (
    {"nos": [{"id": "folhas", "peca": "touceira", "args": CAPIM}]},)


def _com_flores(caso: dict[str, Any], semente: int, flores: tuple[str, ...] = ("5",)) -> Any:
    """A IR da touceira ``caso`` com um ``salpico`` de ``n`` flores nas pontas dela para cada ``n`` de ``flores``."""
    nos = [*caso["nos"], *({"id": f"flor{j}", "peca": "salpico",
                            "args": {"em": "folhas.pontas", "material": "olho_claro", "n": n}}
                           for j, n in enumerate(flores))]
    dado = {**de_uma_peca("touceira", CAPIM).model_dump(mode="json"), "categoria": "objeto", "semente": semente,
            **caso, "nos": nos}
    return ir_da_composicao(validar(dado, Composicao, "teste"))


def _altura_das_flores(caso: dict[str, Any]) -> float:
    """A altura média na tela da vista S das flores, em alturas da touceira (0 = o pé; 1 = o alto), em seis sementes:
    da câmera de cima a 45°, o z sobe e o y (para a câmera) desce."""
    alturas: list[float] = []
    for semente in range(6):
        ir = _com_flores(caso, semente)
        alto = max(z * math.sqrt(0.5) - y * 0.6 for p in ir.parts if p.geometry.type == "polyline"
                   for _, y, z in p.geometry.points_q8)
        alturas += [(p.geometry.center_q8[2] * math.sqrt(0.5) - p.geometry.center_q8[1] * 0.6) / alto
                    for p in ir.parts if p.geometry.type == "ellipse"]
    return sum(alturas) / len(alturas)


def _escolha_antiga(c: Any, pts: list[Any], a: dict[str, Any]) -> list[int]:
    """O jeito antigo nas pontas: o da face de um volume (as de normal virada para a câmera, que descem na tela)."""
    beiras = pecas_ervas._beiras(pecas_ervas._normais(pts), list(c.vistas.values()))
    ordem = sorted(range(len(pts)), key=lambda k: beiras[k])
    escolha = [k for j, k in enumerate(ordem) if j < a["n"] or beiras[k] <= pecas_ervas.BEIRA]
    return [escolha.pop(c.st.randint(0, len(escolha) - 1)) for _ in range(min(a["n"], len(escolha)))]


def test_a_flor_nas_pontas_fica_no_alto_da_touceira() -> None:
    """Nas pontas, o salpico vai para as mais altas na tela: a ponta que abre para a câmera desce, e a flor nela
    ficava na altura do pé."""
    for caso in CAPINS_DE_FLOR:
        assert _altura_das_flores(caso) >= 0.6, caso


def test_controle_pela_normal_a_flor_cai_embaixo(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pecas_ervas, "_nas_pontas", _escolha_antiga)
    for caso in CAPINS_DE_FLOR:
        assert _altura_das_flores(caso) < 0.5, caso


def _flores_juntas() -> int:
    """Os pares de flores a menos de dois raios e 1 px uma da outra na tela da vista S, com dois salpicos de quatro
    flores nas mesmas pontas do capim de 40 × 70 cm (a margarida e o ranúnculo), em seis sementes."""
    juntas = 0
    for semente in range(6):
        ir = _com_flores(CAPINS_DE_FLOR[0], semente, ("4", "4"))
        tela = [pecas_ervas._na_tela((x / 256, y / 256, z / 256), 0) for x, y, z in
                (p.geometry.center_q8 for p in ir.parts if p.geometry.type == "ellipse")]
        juntas += sum(1 for i, p in enumerate(tela) for o in tela[i + 1:] if math.dist(p, o) < 2 * 0.03 * PPM + 1)
    return juntas


def test_as_flores_nas_pontas_nao_se_amontoam() -> None:
    """Cada flor fica longe das outras, as do mesmo salpico e as de outro nas mesmas pontas."""
    assert _flores_juntas() == 0


def test_controle_sem_a_distancia_as_flores_caem_juntas(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pecas_ervas, "LONGE", -1e9)
    assert _flores_juntas() >= 10


def _mais_perto_de_uma_camera(vistas: tuple[str, ...]) -> float:
    """Em fatias da volta: o menor ângulo entre uma folha larga e a câmera de uma das ``vistas``, de 5 a 11 folhas e
    seis sementes."""
    menor = 1.0
    for n in range(5, 12):
        dado = de_uma_peca("touceira", {**FOLHAS, "n": str(n)}).model_dump(mode="json")
        for semente in range(6):
            ir = ir_da_composicao(validar({**dado, "semente": semente, "vistas": dict.fromkeys(vistas, {})},
                                          Composicao, "teste"))
            for x, y, _ in (p.geometry.points_q8[-1] for p in ir.parts if p.geometry.type == "tapered_polyline"):
                for v in vistas:
                    d = (math.degrees(math.atan2(x, y)) - AZIMUTE[v] / 1000 + 180) % 360 - 180
                    menor = min(menor, abs(d) / (360 / n))
    return menor


def test_nenhuma_folha_larga_aponta_para_a_camera_de_uma_vista() -> None:
    """Em toda vista declarada, a folha mais perto da câmera fica a 0,2 fatia ou mais dela (só com a S, as outras
    ficavam livres por acaso, com ``n`` múltiplo de 4)."""
    for vistas in (pecas_ervas.QUATRO, ("S", "E")):
        assert _mais_perto_de_uma_camera(vistas) >= 0.2 - 0.01, vistas


def test_controle_com_a_frente_livre_so_na_s_uma_folha_aponta_para_outra_camera(
        monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pecas_ervas, "FOLGA", 0.0)
    monkeypatch.setattr(pecas_ervas, "_vao", lambda _cameras, _n: (0.5, 1.0))
    assert _mais_perto_de_uma_camera(pecas_ervas.QUATRO) < 0.05


def _rosetas_da_vista_s() -> list[Any]:
    out = []
    for n in range(5, 12):
        dado = de_uma_peca("touceira", {**FOLHAS, "n": str(n)}).model_dump(mode="json")
        out += [ir_da_composicao(validar({**dado, "semente": s}, Composicao, "teste")).parts for s in range(6)]
    return out


def test_a_roseta_da_vista_unica_s_nao_muda(monkeypatch: pytest.MonkeyPatch) -> None:
    """Na composição de vista única S a frente já ficava livre: o empurrão das câmeras não mexe em folha nenhuma."""
    antes = _rosetas_da_vista_s()
    monkeypatch.setattr(pecas_ervas, "FOLGA", 0.0)
    assert _rosetas_da_vista_s() == antes


ESPADA = PECAS["touceira"].variacoes[3][1]
LISAS = ({**FOLHAS, "pena": False}, ESPADA)


def _lado_da_nervura() -> float:
    """Onde a nervura cai na folha lisa larga, na vista S: em cada coluna, (os px da folha abaixo dela − os acima)
    sobre a soma (0 = no meio; 1 = no alto da folha), na média de quatro sementes."""
    lados = []
    dado = de_uma_peca("touceira", {**FOLHAS, "pena": False}).model_dump(mode="json")
    for semente in range(4):
        q = _quadro(validar({**dado, "semente": semente}, Composicao, "teste"))
        for k, p in enumerate(q.part_table):
            if not p.endswith("_nervura"):
                continue
            folha = (q.dono == k + 1) | (q.dono == q.part_table.index(p.removesuffix("_nervura")) + 1)
            for y, x in zip(*(q.dono == k + 1).nonzero(), strict=True):
                cima = baixo = 0
                while y - cima > 0 and folha[y - cima - 1, x]:
                    cima += 1
                while y + baixo + 1 < folha.shape[0] and folha[y + baixo + 1, x]:
                    baixo += 1
                if cima + baixo >= 3:
                    lados.append((baixo - cima) / (cima + baixo))
    return sum(lados) / len(lados)


def test_a_nervura_corre_no_eixo_da_folha() -> None:
    """A nervura corre no eixo e vem à frente do corpo no z-buffer: na folha deitada ela fica no meio."""
    assert abs(_lado_da_nervura()) <= 0.3


def test_controle_a_nervura_erguida_corre_no_alto_da_folha(monkeypatch: pytest.MonkeyPatch) -> None:
    """O jeito antigo: a nervura erguida o raio do corpo acima do eixo (para o corpo não a cobrir)."""
    monkeypatch.setattr(pecas_ervas, "_nervura", lambda arco, largura: (
        [(x, y, z + largura / 2 * k) for (x, y, z), k in zip(arco[:-1], pecas_ervas.LARGURA_NO_ARCO, strict=False)],
        0))
    assert _lado_da_nervura() >= 0.3


def _juntas(args: dict[str, Any]) -> float:
    """Das beiras entre os corpos de duas folhas vizinhas na vista S, a fração em que as duas saem do mesmo tom (o
    tom de cada uma é o mais comum nela; a linha entre elas não conta), em seis sementes."""
    juntas = beiras = 0
    for semente in range(6):
        q = _quadro(validar({**de_uma_peca("touceira", args).model_dump(mode="json"), "semente": semente},
                            Composicao, "teste"))
        dono = q.dono.astype(np.int64)
        cheio = np.full(len(q.part_table) + 1, -1)
        for k, p in enumerate(q.part_table):
            if not p.endswith(("_nervura", "_miolo")) and (q.dono == k + 1).any():
                cheio[k + 1] = np.bincount(q.index[q.dono == k + 1]).argmax()
        corpo = q.index == cheio[dono]
        for dy, dx in ((0, 1), (1, 0)):
            h, w = dono.shape[0] - dy, dono.shape[1] - dx
            vizinhas = corpo[:h, :w] & corpo[dy:, dx:] & (dono[:h, :w] != dono[dy:, dx:])
            beiras += int(vizinhas.sum())
            juntas += int((vizinhas & (q.index[:h, :w] == q.index[dy:, dx:])).sum())
    return juntas / beiras


def test_as_folhas_lisas_vizinhas_nao_se_juntam_numa_mancha() -> None:
    """A folha lisa não repete o tom da vizinha na volta, e a larga tem o contorno dela: a beira entre duas folhas
    quase nunca é do mesmo tom dos dois lados."""
    for args in LISAS:
        assert _juntas(args) <= 0.25, args["largura"]


def test_controle_no_mesmo_grupo_e_no_tom_sorteado_as_folhas_se_juntam(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pecas_ervas, "_outro_tom", lambda _a, tom, _lado, _vizinhas: tom)
    monkeypatch.setattr(pecas_ervas, "COM_CONTORNO", 1e9)
    for args in LISAS:
        assert _juntas(args) >= 0.3, args["largura"]
