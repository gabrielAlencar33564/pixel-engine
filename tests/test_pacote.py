"""O build e o pacote do jogo pelo `pfe`: o export relido pelo leitor do jogo dá os mesmos quadros do build, e a
recusa traz código e dica."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from pixel_forge.cli import main
from pixel_forge.export.imagem import ler_rgba, salvar_png

from .oraculo import CASOS, caso


def _build(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> Path:
    ir = tmp_path / "bloco.ir.json"
    ir.write_text(json.dumps(caso("bloco")["ir"]), encoding="utf-8")
    assert main(["build", str(ir), "--estilo", str(CASOS / "estilo.json"), "--acervo", str(tmp_path / "acervo"),
                 "--json"]) == 0
    res = json.loads(capsys.readouterr().out)["result"]
    assert res["quadros"] == 2
    return Path(res["build"])


def test_o_pacote_relido_da_os_quadros_do_build(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    build = _build(tmp_path, capsys)
    assert main(["exportar", str(build), "--json"]) == 0
    atlas = Path(json.loads(capsys.readouterr().out)["result"]["atlas"])
    doc = json.loads(atlas.read_text(encoding="utf-8"))
    assert doc["contract"] == "pfe-jogo/1" and doc["directions"] == ["S", "SE"]
    assert doc["status"] == "preview" and doc["art_review"] == "pending"
    assert main(["exportar", str(build), "--verificar", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["result"] == {"verificado": True}


def test_controle_o_pixel_trocado_no_atlas_e_achado(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    build = _build(tmp_path, capsys)
    main(["exportar", str(build), "--json"])
    atlas = Path(json.loads(capsys.readouterr().out)["result"]["atlas"]).with_name("atlas.png")
    rgba = ler_rgba(atlas)
    ys, xs = np.nonzero(rgba[..., 3] == 255)
    rgba[ys[0], xs[0], :3] ^= 0xFF
    salvar_png(atlas, rgba)
    assert main(["exportar", str(build), "--verificar", "--json"]) == 2
    erro = json.loads(capsys.readouterr().out)["errors"][0]
    assert erro["code"] == "EXPORT_DIVERGE" and "pixels divergem" in erro["message"] and erro["hint"]


def test_controle_o_contrato_desconhecido_e_recusado(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    build = _build(tmp_path, capsys)
    main(["exportar", str(build), "--json"])
    atlas = Path(json.loads(capsys.readouterr().out)["result"]["atlas"])
    doc = json.loads(atlas.read_text(encoding="utf-8"))
    atlas.write_text(json.dumps({**doc, "contract": "pfe-jogo/0"}), encoding="utf-8")
    assert main(["exportar", str(build), "--verificar", "--json"]) == 2
    erro = json.loads(capsys.readouterr().out)["errors"][0]
    assert erro["code"] == "PACOTE_CONTRATO" and erro["hint"]


def test_o_desenho_cortado_pelo_canvas_e_recusado_com_dica(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    dado = caso("bloco")["ir"]
    dado["canvas"]["pivot_px"] = [4, 32]
    ir = tmp_path / "cortado.json"
    ir.write_text(json.dumps(dado), encoding="utf-8")
    assert main(["build", str(ir), "--estilo", str(CASOS / "estilo.json"), "--acervo", str(tmp_path), "--json"]) == 2
    erro = json.loads(capsys.readouterr().out)["errors"][0]
    assert erro["code"] == "QUADRO_CORTADO" and "canvas" in erro["hint"]
