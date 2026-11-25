"""A crítica da flora: as medidas acusam o jeito fraco (o ovo, a copa espelhada, o tom chapado, a árvore sem tronco, a
planta igual à irmã) e deixam passar a copa do kit; o pacote da flora só sai com a crítica feita e o parecer de quem
revisou; o asset que não é planta sai como sempre."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from pixel_forge.application import critica
from pixel_forge.cli import main
from pixel_forge.contracts.carregar import ler, validar
from pixel_forge.contracts.composicao import Composicao
from pixel_forge.quality import flora

FIXTURES = Path(__file__).parent / "fixtures"
EXEMPLO = FIXTURES / "exemplos" / "arvore_folhosa.r1.json"
MOURAO = FIXTURES / "composicoes" / "mourao.r1.json"
TRONCO: dict[str, Any] = {"id": "tronco", "peca": "tronco_em_pe",
          "args": {"altura": "1.5m", "base": "30cm", "topo": "20cm", "casca": "casca_sulcada"}}


def _planta(*nos: dict[str, Any], categoria: str = "arvore_pequena") -> Composicao:
    dado = json.loads(EXEMPLO.read_text(encoding="utf-8"))
    return validar({**dado, "categoria": categoria, "nos": list(nos), "tracos": []}, Composicao, "teste")


def _codigos(comp: Composicao, gravidade: str = "defeito") -> set[str]:
    m = critica.medir(comp)[0]
    return {a["codigo"] for a in flora.achados(m, comp.categoria in critica.ARVORES, {})
            if a["gravidade"] == gravidade}


def _bola(i: int, centro: tuple[float, float, float]) -> dict[str, Any]:
    return {"id": f"bola_{i:02d}", "peca": "elipsoide", "grupo": "copa", "args": {
        "centro": [f"{v:.3f}m" for v in centro], "raios": ["63cm", "63cm", "40cm"], "material": "copa_folhosa"}}


def _copa_em_anel() -> Composicao:
    """O jeito antigo, sintético: bolas iguais em anéis em volta do eixo (o tufo de cima, um anel no meio)."""
    bolas = [_bola(0, (0.0, 0.0, 2.6))]
    bolas += [_bola(i + 1, (0.77 * math.sin(a), 0.77 * math.cos(a), 2.1))
              for i, a in enumerate(2 * math.pi * k / 8 for k in range(8))]
    return _planta(TRONCO, *bolas)


def test_a_copa_do_kit_passa_nas_medidas() -> None:
    assert _codigos(ler(EXEMPLO, Composicao)) == set()
    assert _codigos(ler(EXEMPLO, Composicao), "aviso") == set()


def test_controle_o_ovo_e_acusado() -> None:
    """A moita de um elipsoide só: lisa e espelhada."""
    ovo = {"id": "moita", "peca": "elipsoide", "args": {"centro": ["0", "0", "45cm"],
                                                        "raios": ["70cm", "55cm", "45cm"], "material": "copa_folhosa"}}
    assert _codigos(_planta(ovo, categoria="arbusto")) == {"FOLHAGEM_LISA", "FOLHAGEM_ESPELHADA"}


def test_controle_a_copa_em_anel_e_acusada() -> None:
    assert "FOLHAGEM_ESPELHADA" in _codigos(_copa_em_anel())


def test_controle_a_folhagem_chapada_e_acusada() -> None:
    """A conífera de um polígono: sem lado claro nem escuro."""
    cone = {"id": "copa", "peca": "poligono", "args": {
        "pontos": [["-90cm", "0", "50cm"], ["90cm", "0", "50cm"], ["0", "0", "3m"]], "material": "agulha"}}
    assert "LUZ_SEM_DIRECAO" in _codigos(_planta(cone))


def test_controle_a_arvore_sem_tronco_a_mostra_e_avisada() -> None:
    toco = {**TRONCO, "args": {**TRONCO["args"], "altura": "40cm"}}
    copa = {"id": "copa", "peca": "copa", "args": {"copa": ["1.4m", "1m", "1m"], "tamanho": "0.5"}}
    assert "TRONCO_SUMIDO" in _codigos(_planta(toco, copa), "aviso")


def test_as_medidas_na_mascara() -> None:
    """Cada medida no caso simples e no controle dela."""
    yy, xx = np.indices((40, 40))
    disco = (xx - 20) ** 2 + (yy - 20) ** 2 <= 15 ** 2
    cruz = (abs(xx - 20) <= 2) | (abs(yy - 20) <= 2)
    torto = disco & ~((xx > 22) & (yy < 18))
    assert flora.solidez(disco) == 1.0 and flora.solidez(cruz) < 0.5
    assert flora.simetria(disco) == 1.0 and flora.simetria(torto) < 0.9
    assert flora.ilhas(disco) == 1 and flora.ilhas(disco | (xx == 0)) == 2
    luz = np.where(xx + yy < 40, 200.0, 50.0)  # o claro em cima e à esquerda
    assert flora.luz(luz, disco) > 0.2 and flora.luz(luz[::-1, ::-1], disco) < -0.2 and flora.luz(luz * 0, disco) == 0
    grande = np.repeat(np.repeat(torto, 3, axis=0), 3, axis=1)
    alto = np.zeros((40, 40), dtype=bool)
    alto[2:38, 17:23] = True
    assert flora.semelhanca(flora.assinatura(torto), flora.assinatura(grande)) > 0.9  # a mesma forma, outro tamanho
    assert flora.semelhanca(flora.assinatura(torto), flora.assinatura(alto)) < 0.4


def pfe(capsys: pytest.CaptureFixture[str], *args: str) -> tuple[int, dict[str, Any]]:
    codigo = main([*args, "--json"])
    return codigo, json.loads(capsys.readouterr().out)


def _arquivo(pasta: Path, nome: str, **mudar: Any) -> Path:
    dado = {**json.loads(EXEMPLO.read_text(encoding="utf-8")), **mudar}
    alvo = pasta / f"{nome}.json"
    alvo.write_text(json.dumps(dado), encoding="utf-8")
    return alvo


def _parecer(pasta: Path, **ruins: str) -> Path:
    respostas = {k: {"ok": k not in ruins, "nota": ruins.get(k, "olhei o painel e a fileira das irmãs")}
                 for k in critica.PERGUNTAS}
    alvo = pasta / "parecer.json"
    alvo.write_text(json.dumps({"respostas": respostas}), encoding="utf-8")
    return alvo


def test_a_flora_so_sai_com_a_critica_que_passa(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    acervo = str(tmp_path / "acervo")
    build = pfe(capsys, "build", str(EXEMPLO), "--acervo", acervo)[1]["result"]["build"]
    codigo, r = pfe(capsys, "exportar", build)
    assert codigo == 2 and r["errors"][0]["code"] == "CRITICA_PENDENTE" and "pfe critica" in r["errors"][0]["hint"]
    feita = pfe(capsys, "critica", build)[1]["result"]
    assert feita["veredito"] == "pendente" and feita["achados"] == [] and Path(feita["prancha"]).is_file()
    assert set(feita["perguntas"]) == set(critica.PERGUNTAS) and feita["ficha"].startswith("Folhosa")
    assert pfe(capsys, "exportar", build)[1]["errors"][0]["code"] == "CRITICA_PENDENTE"
    # o parecer sem as notas, sem quem revisou, e o que manda corrigir
    vazio = tmp_path / "vazio.json"
    vazio.write_text(json.dumps({"respostas": {k: {"ok": True, "nota": "ok"} for k in critica.PERGUNTAS}}))
    assert pfe(capsys, "critica", build, "--parecer", str(vazio), "--por", "outro")[1]["errors"][0]["code"] == "PARECER"
    assert pfe(capsys, "critica", build, "--parecer", str(_parecer(tmp_path)))[1]["errors"][0]["code"] == "CRITICA"
    ruim = _parecer(tmp_path, silhueta="a copa lê como uma bola sobre um palito")
    corrigir = pfe(capsys, "critica", build, "--parecer", str(ruim), "--por", "agente revisor")[1]["result"]
    assert (corrigir["veredito"], corrigir["a_corrigir"]) == ("corrigir", ["silhueta"])
    assert pfe(capsys, "exportar", build)[1]["errors"][0]["code"] == "CRITICA_PENDENTE"
    passa = pfe(capsys, "critica", build, "--parecer", str(_parecer(tmp_path)), "--por", "agente revisor")[1]["result"]
    assert passa["veredito"] == "passa" and passa["parecer"]["por"] == "agente revisor"
    assert pfe(capsys, "exportar", build)[0] == 0
    assert pfe(capsys, "olhar", build)[1]["result"]["art_review"] == "pending"  # a crítica não aprova a arte


def test_o_defeito_medido_nao_passa_com_parecer_bom(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """A irmã do acervo com a mesma silhueta em outro tamanho: a crítica acusa, e o parecer bom não a salva."""
    acervo = str(tmp_path / "acervo")
    pfe(capsys, "build", str(EXEMPLO), "--acervo", acervo)
    maior = _arquivo(tmp_path, "arvore_maior", id="arvore_maior", tracos=[],
                     medidas={"h": "3.2m", "a": "1.49m", "copa0": "$h * 0.42", "c": "($h - $copa0) / 2",
                              "cz": "$copa0 + $c"})
    build = pfe(capsys, "build", str(maior), "--acervo", acervo)[1]["result"]["build"]
    feita = pfe(capsys, "critica", build)[1]["result"]
    assert [a["codigo"] for a in feita["achados"]] == ["PARECIDA_COM_A_IRMA"]
    assert feita["irmas"]["arvore_folhosa"] >= flora.PARECIDA
    dado = pfe(capsys, "critica", build, "--parecer", str(_parecer(tmp_path)), "--por", "agente revisor")[1]["result"]
    assert (dado["veredito"], dado["a_corrigir"]) == ("corrigir", ["PARECIDA_COM_A_IRMA"])
    assert pfe(capsys, "exportar", build)[1]["errors"][0]["code"] == "CRITICA_PENDENTE"


def test_controle_a_irma_de_outra_construcao_nao_e_acusada(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    acervo = str(tmp_path / "acervo")
    pfe(capsys, "build", str(EXEMPLO), "--acervo", acervo)
    nos = json.loads(EXEMPLO.read_text(encoding="utf-8"))["nos"]
    gota = _arquivo(tmp_path, "arvore_em_gota", id="arvore_em_gota", tracos=[], nos=[nos[0], {
        "id": "copa", "peca": "copa", "args": {"copa": ["80cm", "$c", "$cz"], "perfil": "0.9", "tufos": "11",
                                               "tamanho": "0.34"}}])
    build = pfe(capsys, "build", str(gota), "--acervo", acervo)[1]["result"]["build"]
    feita = pfe(capsys, "critica", build)[1]["result"]
    assert feita["achados"] == [] and 0 < feita["irmas"]["arvore_folhosa"] < flora.PARECIDA


def test_a_previa_ja_mede_a_flora(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    acervo = str(tmp_path / "acervo")
    r = pfe(capsys, "previa", str(EXEMPLO), "--acervo", acervo)[1]["result"]
    assert r["critica"]["achados"] == [] and r["critica"]["medidas"]["folhagem_px"] > 1000


def test_controle_o_asset_que_nao_e_planta_sai_sem_critica(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    acervo = str(tmp_path / "acervo")
    assert "critica" not in pfe(capsys, "previa", str(MOURAO), "--acervo", acervo)[1]["result"]
    build = pfe(capsys, "build", str(MOURAO), "--acervo", acervo)[1]["result"]["build"]
    assert pfe(capsys, "critica", build)[1]["errors"][0]["code"] == "CRITICA"
    assert pfe(capsys, "exportar", build)[0] == 0
