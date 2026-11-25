"""O catálogo em dois níveis: o resumo (as famílias e as peças) e um arquivo por família com a peça inteira. Quem
faz uma planta lê o resumo e a flora, não o kit inteiro; a lista de partes numeradas vira faixa. Os controles: o
catálogo sem pedido grava todas as famílias, a família que não existe é recusada, e dois ids seguidos não viram
faixa."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from pixel_forge.application.catalogo import catalogo, em_faixas
from pixel_forge.cli import main
from pixel_forge.core.recusa import Recusa
from pixel_forge.design.kit.registro import FAMILIAS, PECAS

EXEMPLO = Path(__file__).parent / "fixtures" / "exemplos" / "arvore_folhosa.r1.json"


def _ler(caminho: str) -> Any:
    return json.loads(Path(caminho).read_text(encoding="utf-8"))


def test_o_resumo_tem_toda_peca_numa_familia(tmp_path: Path) -> None:
    feito = catalogo(tmp_path)
    resumo = _ler(feito["index"])
    por_familia = {f["familia"]: list(f["pecas"]) for f in resumo["familias"]}
    assert por_familia == {f: list(ids) for f, ids in FAMILIAS.items()}
    assert sorted(p for ids in por_familia.values() for p in ids) == sorted(PECAS)  # cada peça numa família só
    assert resumo["materiais"] and all("args" not in f for f in resumo["familias"])
    for familia, arquivo in feito["familias"].items():
        pecas = _ler(arquivo)
        assert [p["id"] for p in pecas] == list(FAMILIAS[familia])
        assert all(p["args"] and p["variacoes"] and (tmp_path / p["prancha"]).is_file() for p in pecas)


def test_quem_faz_planta_le_so_a_flora(tmp_path: Path) -> None:
    """Com a família pedida, o catálogo grava só ela, e o que se lê é uma fração do kit inteiro (o controle)."""
    feito = catalogo(tmp_path / "flora", ["flora"])
    assert list(feito["familias"]) == ["flora"]
    assert sorted(p.stem for p in (tmp_path / "flora").glob("*.png")) == sorted(FAMILIAS["flora"])
    lido = sum(Path(a).stat().st_size for a in (feito["index"], *feito["familias"].values()))
    tudo = catalogo(tmp_path / "tudo")
    inteiro = sum(Path(a).stat().st_size for a in (tudo["index"], *tudo["familias"].values()))
    assert len(tudo["familias"]) == len(FAMILIAS) and lido <= 0.4 * inteiro


def test_controle_a_familia_que_nao_existe_e_recusada(tmp_path: Path) -> None:
    with pytest.raises(Recusa) as e:
        catalogo(tmp_path, ["plantas"])
    assert e.value.codigo == "FAMILIA" and "flora" in e.value.dica


def test_as_partes_numeradas_viram_faixa() -> None:
    ids = ["t", "c_miolo", "c_00", "c_01", "c_02", "c_03", "r_0", "r_1", "x_9", "x_10", "x_11", "y_01", "y_03"]
    # dois seguidos e os que pulam um número ficam como estão
    assert em_faixas(ids) == ["t", "c_miolo", "c_00..c_03", "r_0", "r_1", "x_9..x_11", "y_01", "y_03"]


def test_a_previa_diz_as_partes_em_faixas(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["previa", str(EXEMPLO), "--acervo", str(tmp_path), "--json"]) == 0
    partes = json.loads(capsys.readouterr().out)["result"]["partes"]
    assert partes[:2] == ["tronco", "copa_miolo"] and partes[2].startswith("copa_00..copa_") and len(partes) == 3
