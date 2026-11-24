"""O caminho curto de um asset pelo `pfe`, no acervo e sem projeto: prévia, checar, build, exportar, verificar, olhar,
revisar e publicar; a prévia recusa o que o build recusa (I8); a identidade é imutável e a mudança é a revisão seguinte;
o mesmo id de build é sempre o mesmo desenho; o estático sai em menos de 1 min de máquina."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import pytest

from pixel_forge.cli import main
from pixel_forge.views import camera

from .oraculo import CASOS

ARVORE = CASOS / "composicoes" / "arvore.r1.json"
MOURAO = Path(__file__).parent / "fixtures" / "composicoes" / "mourao.r1.json"


def pfe(capsys: pytest.CaptureFixture[str], *args: str) -> tuple[int, dict[str, Any]]:
    codigo = main([*args, "--json"])
    return codigo, json.loads(capsys.readouterr().out)


def _copia(tmp_path: Path, origem: Path, **mudar: Any) -> Path:
    dado = {**json.loads(origem.read_text(encoding="utf-8")), **mudar}
    alvo = tmp_path / origem.name
    alvo.write_text(json.dumps(dado), encoding="utf-8")
    return alvo


def test_o_caminho_curto_do_estatico_em_menos_de_1_min(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    acervo = str(tmp_path / "acervo")
    t0 = time.process_time()
    assert pfe(capsys, "previa", str(ARVORE), "--acervo", acervo)[0] == 0
    _, b = pfe(capsys, "build", str(ARVORE), "--acervo", acervo)
    build = b["result"]["build"]
    assert pfe(capsys, "exportar", build)[0] == 0
    assert pfe(capsys, "exportar", build, "--verificar")[1]["result"] == {"verificado": True}
    assert time.process_time() - t0 < 60
    _, o = pfe(capsys, "olhar", build)
    assert Path(o["result"]["prancha"]).is_file() and o["result"]["art_review"] == "pending"
    assert Path(b["result"]["composicao"]) == Path(acervo) / "composicoes" / "arvore.r1.json"


def test_so_sai_publicado_com_a_revisao_do_dono(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    build = pfe(capsys, "build", str(MOURAO), "--acervo", str(tmp_path))[1]["result"]["build"]
    codigo, r = pfe(capsys, "exportar", build, "--publicar")
    assert codigo == 2 and r["errors"][0]["code"] == "REVISAO_PENDENTE" and "pfe revisar" in r["errors"][0]["hint"]
    assert pfe(capsys, "revisar", build, "--veredito", "aprovado")[1]["errors"][0]["code"] == "REVISAO"
    pfe(capsys, "revisar", build, "--veredito", "aprovado", "--nota", "a silhueta lê", "--por", "dono do teste")
    atlas = Path(pfe(capsys, "exportar", build, "--publicar")[1]["result"]["atlas"])
    doc = json.loads(atlas.read_text(encoding="utf-8"))
    assert (doc["status"], doc["art_review"]) == ("release_candidate", "approved")


@pytest.mark.parametrize("comando", ["previa", "checar", "build"])
def test_a_previa_recusa_o_que_o_build_recusa(tmp_path: Path, capsys: pytest.CaptureFixture[str], comando: str) -> None:
    comp = _copia(tmp_path, MOURAO, categoria="arvore_grande")
    codigo, r = pfe(capsys, comando, str(comp), *(["--acervo", str(tmp_path)] if comando != "checar" else []))
    assert codigo == 2 and r["errors"][0]["code"] == "PORTE" and "~2,5×" in r["errors"][0]["hint"]


def test_a_identidade_e_imutavel_e_a_mudanca_e_a_revisao_seguinte(tmp_path: Path,
                                                                   capsys: pytest.CaptureFixture[str]) -> None:
    acervo = str(tmp_path / "acervo")
    assert pfe(capsys, "build", str(MOURAO), "--acervo", acervo)[0] == 0
    mudada = _copia(tmp_path, MOURAO, semente=8)
    codigo, r = pfe(capsys, "build", str(mudada), "--acervo", acervo)
    assert codigo == 2 and r["errors"][0]["code"] == "IDENTIDADE" and "pfe atualizar" in r["errors"][0]["hint"]
    _, a = pfe(capsys, "atualizar", str(mudada), "--acervo", acervo)
    assert Path(a["result"]["composicao"]).name == "mourao.r2.json"
    assert pfe(capsys, "atualizar", str(mudada), "--acervo", acervo)[1]["errors"][0]["code"] == "SEM_MUDANCA"


def test_o_mesmo_id_de_build_e_sempre_o_mesmo_desenho(tmp_path: Path, capsys: pytest.CaptureFixture[str],
                                                      monkeypatch: pytest.MonkeyPatch) -> None:
    acervo = str(tmp_path / "acervo")
    antes = pfe(capsys, "build", str(MOURAO), "--acervo", acervo)[1]["result"]["build"]
    assert pfe(capsys, "build", str(MOURAO), "--acervo", acervo)[1]["result"]["build"] == antes
    monkeypatch.setattr(camera, "PROFUNDIDADE_PERMILLE", 350)  # o motor desenha diferente sem mudar de versão
    depois = pfe(capsys, "build", str(MOURAO), "--acervo", acervo)[1]["result"]["build"]
    assert depois != antes and Path(antes).is_dir() and Path(depois).is_dir()


def test_o_conjunto_poe_a_regua_e_as_alturas(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _, r = pfe(capsys, "conjunto", str(ARVORE), str(MOURAO), "--acervo", str(tmp_path))
    assert Path(r["result"]["prancha"]).is_file() and set(r["result"]["alturas"]) == {"arvore", "mourao"}


def test_o_checar_confere_todos_os_quadros_do_humano(capsys: pytest.CaptureFixture[str]) -> None:
    _, r = pfe(capsys, "checar", str(CASOS / "humanos" / "vestido.r1.json"))
    assert r["result"]["quadros"] == 176 and r["result"]["clipes"] == ["idle", "walk"]
