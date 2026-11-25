"""O hábito: a planta descrita pelos traços dela (``planta``), com os nós derivados pela engine. Cada hábito dá a
construção dele; as medidas saem de regras gerais (a esbeltez, o fuste, o lóbulo do tamanho da folhagem, o galho mais
fino que o tronco); o que se deriva nunca fica no ar, em qualquer tamanho; e a composição pelos traços é uma fração
da escrita peça por peça. Os controles: o traço fora da faixa, a planta num humano, a composição sem nada."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from pixel_forge.application import critica
from pixel_forge.application.build import construir, hash_canonico, renderizar
from pixel_forge.application.estilo import estilo_base
from pixel_forge.cli import main
from pixel_forge.contracts.carregar import ler, validar
from pixel_forge.contracts.composicao import Composicao
from pixel_forge.core.recusa import Recusa
from pixel_forge.design import habito
from pixel_forge.design.asset import ir_da_composicao
from pixel_forge.design.escala import PPM
from pixel_forge.design.habito import expandida
from pixel_forge.quality import flora

FIXTURES = Path(__file__).parent / "fixtures"
EXEMPLO = FIXTURES / "exemplos" / "arvore_folhosa.r1.json"
MOURAO = FIXTURES / "composicoes" / "mourao.r1.json"
PECAS_DO_HABITO = {
    "decurrente": ["tronco_em_pe", "copa"], "pendente": ["tronco_em_pe", "copa"],
    "guarda_sol": ["tronco_em_pe", "copa"], "excurrente": ["tronco_em_pe", "copa"],
    "aberto": ["tronco_em_pe", "galhos", "copa_aberta"], "seco": ["tronco_em_pe", "galhos"],
    "moita": ["copa", "copa", "copa"], "touceira": ["touceira"],
}


def _comp(categoria: str = "arvore_grande", nos: list[dict[str, Any]] | None = None, **planta: Any) -> Composicao:
    dado = json.loads(EXEMPLO.read_text(encoding="utf-8"))
    del dado["medidas"]
    return validar({**dado, "categoria": categoria, "nos": nos or [], "tracos": [],
                    "planta": {"altura": "4.5m", "largura": "3.6m", **planta}}, Composicao, "teste")


def _args(comp: Composicao, no: str) -> dict[str, Any]:
    return next(n.args for n in expandida(comp).nos if n.id == no)


def _px(texto: Any) -> float:
    return float(str(texto).removesuffix("px"))


@pytest.mark.parametrize("habito", sorted(PECAS_DO_HABITO))
def test_cada_habito_da_a_construcao_dele(habito: str) -> None:
    """Os nós derivados são os da construção do hábito, passam por todas as recusas do build e pela crítica."""
    moita = habito in ("moita", "touceira")
    medidas_da_moita: dict[str, Any] = {"altura": "70cm", "largura": "2.2m"} if moita else {}
    comp = _comp("arbusto" if moita else "arvore_grande", habito=habito, **medidas_da_moita)
    assert [n.peca for n in expandida(comp).nos] == PECAS_DO_HABITO[habito]
    assert all(s.quadros for s in renderizar(comp).sequencias)
    medidas = critica.medir(comp)[0]
    assert not [a for a in flora.achados(medidas, False, {}) if a["gravidade"] == "defeito"]


def test_o_excurrente_de_agulha_e_a_conifera_em_andares() -> None:
    nos = expandida(_comp(habito="excurrente", folha="agulha")).nos
    assert [n.peca for n in nos] == ["tronco_em_pe", "copa_conica"]


def test_os_habitos_dao_silhuetas_diferentes() -> None:
    """Com a mesma altura e a mesma largura, cada hábito é outra planta."""
    arvores = [h for h in PECAS_DO_HABITO if h not in ("moita", "touceira")]
    lidas = {h: critica.medir(_comp(habito=h))[0].assinatura for h in arvores}
    lidas["conifera"] = critica.medir(_comp(habito="excurrente", folha="agulha"))[0].assinatura
    nomes = sorted(lidas)
    pares = {(a, b): flora.semelhanca(lidas[a], lidas[b]) for i, a in enumerate(nomes) for b in nomes[:i]}
    assert max(pares.values()) < flora.PARECIDA, max(pares, key=lambda k: pares[k])


@pytest.mark.parametrize("habito", sorted(PECAS_DO_HABITO))
def test_o_que_se_deriva_nunca_fica_no_ar(habito: str) -> None:
    """Em qualquer tamanho, idade e vento: o tronco entra na copa, e o galho nasce do tronco e é mais fino que ele."""
    for altura, largura in (("2.2m", "1.2m"), ("4m", "4.4m"), ("6.5m", "2m"), ("6m", "6m")):
        for idade in ("jovem", "adulta", "velha"):
            for vento in ("0", "0.8", "-1"):
                ir_da_composicao(_comp(habito=habito, altura=altura, largura=largura, idade=idade, vento=vento))


def test_a_esbeltez_da_a_grossura_do_tronco() -> None:
    """O diâmetro do pé é a altura sobre a esbeltez: a árvore nova é esguia e a velha engrossa."""
    base = {i: _px(_args(_comp(habito="decurrente", idade=i), "tronco")["base"]) for i in ("jovem", "adulta", "velha")}
    assert base["adulta"] == pytest.approx(4.5 * PPM / 10, abs=0.1)
    assert base["jovem"] < 0.8 * base["adulta"] and base["velha"] > 1.25 * base["adulta"]
    dito = _px(_args(_comp(habito="decurrente", esbeltez="20"), "tronco")["base"])
    assert dito == pytest.approx(4.5 * PPM / 20, abs=0.1)  # o traço que a composição diz vale mais que o do hábito


def _fundo_dos_lobulos(fuste: str) -> float:
    """A altura (px) do ponto mais baixo dos volumes da copa derivada (sem o miolo)."""
    ir = ir_da_composicao(_comp(habito="decurrente", fuste=fuste))
    return min((p.geometry.center_q8[2] - p.geometry.radii_q8[2]) / 256 for p in ir.parts
               if p.id.startswith("copa_") and p.id != "copa_miolo" and p.geometry.type == "ellipse")


def test_o_fuste_diz_onde_a_copa_comeca() -> None:
    """A folhagem começa no fuste pedido: os lóbulos recuam da borda, e o elipsoide desce para compensar."""
    for fuste in (0.25, 0.5):
        assert _fundo_dos_lobulos(str(fuste)) == pytest.approx(fuste * 4.5 * PPM, abs=0.04 * 4.5 * PPM)


def test_controle_sem_descer_o_elipsoide_a_copa_comeca_acima_do_fuste(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(habito, "FUNDO_DA_MASSA", 1.0)  # o elipsoide do fuste ao alto, como se os lóbulos o enchessem
    assert _fundo_dos_lobulos("0.25") > (0.25 + 0.06) * 4.5 * PPM


def test_a_copa_pequena_tem_poucos_lobulos_grandes() -> None:
    """O lóbulo tem o tamanho da folhagem, não o da copa: com muitos e pequenos, na copa pequena o relevo some."""
    pequena = _args(_comp("arvore_pequena", habito="decurrente", altura="2.4m", largura="1.2m"), "copa")
    grande = _args(_comp(habito="decurrente", altura="6m", largura="5.5m"), "copa")
    assert int(pequena["tufos"]) == 5 and int(grande["tufos"]) == 12
    assert float(pequena["tamanho"]) >= 0.45 > float(grande["tamanho"])


def test_a_moita_larga_tem_tres_massas_no_mesmo_grupo() -> None:
    """O número de massas vem da proporção: a moita alta é uma só, a baixa e larga são três encostadas."""
    alta = expandida(_comp("arbusto", habito="moita", altura="1.4m", largura="1.7m")).nos
    larga = expandida(_comp("arbusto", habito="moita", altura="70cm", largura="2.2m"))
    assert [n.id for n in alta] == ["copa"] and [n.id for n in larga.nos] == ["copa", "copa_b", "copa_c"]
    assert {n.grupo for n in larga.nos} == {"copa"}  # uma massa de luz só
    assert critica.medir(larga)[0].ilhas == 1  # e uma moita só: as massas se sobrepõem


def test_a_touceira_fina_e_a_de_folha_larga() -> None:
    fina = _args(_comp("arbusto", habito="touceira", altura="1.2m", largura="50cm"), "folhas")
    larga = _args(_comp("arbusto", habito="touceira", altura="55cm", largura="1.4m", folha="larga"), "folhas")
    assert "largura" not in fina and float(fina["cai"]) < 0.1  # sem `folha`: as lâminas finas em pé (o junco)
    assert larga["pena"] is True and _px(larga["largura"]) >= 3 and float(larga["abre"]) > 0.7  # a samambaia


def _pes_do_capim() -> float:
    """O vão (px) entre o pé mais à esquerda e o mais à direita das lâminas de um capim derivado de 60 cm."""
    ir = ir_da_composicao(_comp("objeto", habito="touceira", altura="45cm", largura="60cm"))
    pes = sorted(p.geometry.points_q8[0][0] / 256 for p in ir.parts if p.geometry.type == "polyline")
    return pes[-1] - pes[0]


def test_as_laminas_do_capim_nascem_cada_uma_no_seu_pe() -> None:
    """A touceira fina derivada espalha os pés pela largura dela: as lâminas ficam separadas, como no capim, e a
    crítica não as acusa (o que se liga é a estrutura da árvore, na geometria; o pixel não se junta)."""
    assert _pes_do_capim() >= 0.3 * 0.6 * PPM
    medidas = critica.medir(_comp("objeto", habito="touceira", altura="45cm", largura="60cm"))[0]
    assert flora.achados(medidas, False, {}) == []


def test_controle_com_o_pe_num_ponto_as_laminas_se_fundem(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(habito, "PE_DA_TOUCEIRA", 0.15)  # o pé antigo: as lâminas nasciam quase de um ponto só
    assert _pes_do_capim() < 0.3 * 0.6 * PPM


def test_a_conifera_derivada_passa_na_critica_em_qualquer_tamanho() -> None:
    """A luz da conífera tem direção (o abeto dos traços saía com defeito)."""
    for altura, largura in (("6m", "3m"), ("4m", "2.2m"), ("6.5m", "2m")):
        for semente in (77, 5, 41):
            dado = _comp(habito="excurrente", folha="agulha", altura=altura, largura=largura).model_dump(mode="json")
            medidas = critica.medir(validar({**dado, "semente": semente}, Composicao, "teste"))[0]
            assert flora.achados(medidas, True, {}) in ([], [a for a in flora.achados(medidas, True, {})
                                                             if a["codigo"] == "TRONCO_SUMIDO"])


def test_no_habito_aberto_a_copa_vai_com_o_tronco_inclinado() -> None:
    """As pontas dos galhos abrem em volta do alto do tronco: com o vento, a folhagem desloca com ele."""
    def meio(vento: str) -> float:
        ir = ir_da_composicao(_comp(habito="aberto", vento=vento))
        xs = [p.geometry.center_q8[0] / 256 for p in ir.parts if p.id.startswith("copa_")
              and p.geometry.type == "ellipse"]
        return sum(xs) / len(xs)

    assert meio("0.8") - meio("0") >= 0.1 * 4.5 * PPM and abs(meio("0")) < 0.05 * 4.5 * PPM


def test_os_nos_da_composicao_citam_as_ancoras_dos_derivados() -> None:
    frutos = {"id": "frutos", "peca": "salpico", "args": {"em": "copa.superficie", "material": "pano_vermelho"}}
    ir = ir_da_composicao(_comp("arbusto", [frutos], habito="moita", altura="70cm", largura="1m"))
    assert sum(1 for p in ir.parts if p.id.startswith("frutos_")) == 8


def test_a_composicao_pelos_tracos_e_uma_fracao_da_escrita_peca_por_peca() -> None:
    comp = _comp(habito="aberto", idade="velha", vento="0.5")
    assert comp.planta is not None
    tracos = len(json.dumps(comp.planta.model_dump(exclude_defaults=True)))
    nos = len(json.dumps([n.model_dump(exclude_defaults=True) for n in expandida(comp).nos]))
    assert tracos <= 0.25 * nos


def test_a_previa_devolve_os_nos_derivados(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    arquivo = tmp_path / "planta.r1.json"
    dado = _comp(habito="pendente").model_dump(mode="json", exclude_none=True)
    arquivo.write_text(json.dumps(dado), encoding="utf-8")
    assert main(["previa", str(arquivo), "--acervo", str(tmp_path / "acervo"), "--json"]) == 0
    r = json.loads(capsys.readouterr().out)["result"]
    assert [n["peca"] for n in r["nos"]] == ["tronco_em_pe", "copa"] and r["critica"]["achados"] == []
    assert "copa_miolo" not in r["escondidas"].get("S", [])  # o de dentro da copa fica sempre escondido: não se lista


def test_controle_o_traco_fora_da_faixa_e_recusado() -> None:
    tracos: list[dict[str, Any]] = [{"fuste": "0.95"}, {"esbeltez": "2"}, {"vento": "3"}, {"altura": "0"}]
    for traco in tracos:
        with pytest.raises(Recusa) as e:
            ir_da_composicao(_comp(habito="decurrente", **traco))
        assert e.value.codigo == "PLANTA"


def test_controle_a_planta_e_do_prop() -> None:
    dado = _comp(habito="decurrente").model_dump(mode="json")
    with pytest.raises(Recusa) as e:
        ir_da_composicao(validar({**dado, "tipo": "humanoide", "categoria": "humano"}, Composicao, "controle"))
    assert e.value.codigo == "PLANTA"


def test_controle_a_composicao_sem_nos_nem_planta_e_recusada() -> None:
    dado = json.loads(EXEMPLO.read_text(encoding="utf-8"))
    with pytest.raises(Recusa) as e:
        ir_da_composicao(validar({**dado, "nos": [], "tracos": []}, Composicao, "controle"))
    assert e.value.codigo == "NO"


def test_controle_a_composicao_sem_planta_tem_o_id_que_sempre_teve(tmp_path: Path) -> None:
    """O campo novo não entra no id do build de quem não o usa."""
    comp = ler(MOURAO, Composicao)
    build = construir(comp, tmp_path)
    dado = comp.model_dump(mode="json")
    del dado["planta"]
    style = estilo_base().model_dump(mode="json")
    pixels = [f["rgba_sha256"] for c in build.manifesto["clips"] for f in c["frames"]]
    assert build.build_id == hash_canonico({"engine": build.manifesto["engine"], "composicao": dado, "style": style,
                                            "pixels": pixels})
