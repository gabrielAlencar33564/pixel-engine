"""I10: só fica o que é usado, sem silenciar o linter nem o mypy, e com as regras de código limpo ligadas."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from .codigo_morto import mortos
from .fontes import ROOT, SRC, arquivos_py

# montadas por partes, para este arquivo não conter a marca que ele procura
MARCAS = ("no" + "qa", "type: " + "ignore", "pragma: " + "no cover", "pylint: " + "disable", "mypy: " + "ignore")
REGRAS = {"F", "ARG", "ERA", "C901", "PLR0912", "PLR0913", "PLR0915"}
CHAVES_DE_EXCECAO = {"ignore", "extend-ignore", "per-file-ignores", "extend-per-file-ignores", "exclude",
                     "extend-exclude", "unfixable"}


def marcas_de_silencio(arquivos: list[Path]) -> list[str]:
    return [f"{p.name}:{i}" for p in arquivos
            for i, linha in enumerate(p.read_text(encoding="utf-8").splitlines(), 1)
            if any(m in linha for m in MARCAS)]


def problemas_da_config(cfg: dict[str, Any]) -> list[str]:
    ruff = cfg.get("tool", {}).get("ruff", {})
    lint = ruff.get("lint", {})
    mypy = cfg.get("tool", {}).get("mypy", {})
    out = [f"ruff: '{k}'" for k in CHAVES_DE_EXCECAO if k in ruff or k in lint]
    falta = REGRAS - set(lint.get("select", []))
    if falta:
        out.append(f"ruff: faltam as regras {sorted(falta)}")
    if mypy.get("strict") is not True:
        out.append("mypy: sem strict")
    out += [f"mypy: '{k}'" for k in ("overrides", "ignore_errors", "disable_error_code", "exclude") if k in mypy]
    return out


def test_nada_morto_em_src_nem_nos_scripts() -> None:
    achados = mortos([SRC, ROOT / "scripts"], ROOT / "pyproject.toml")
    assert not achados, "\n".join(f"{m.arquivo.relative_to(ROOT)}:{m.linha} {m.nome}" for m in achados)


def test_controle_o_detector_acha_o_morto_e_o_usado_so_por_teste(tmp_path: Path) -> None:
    src = tmp_path / "src" / "pacote"
    src.mkdir(parents=True)
    (src / "a.py").write_text("def usada() -> int:\n    return 1\n\n\ndef morta() -> int:\n    return 2\n\n\n"
                              "def recursiva(n: int) -> int:\n    return recursiva(n - 1)\n\n\nX = usada()\n",
                              encoding="utf-8")
    testes = tmp_path / "tests"
    testes.mkdir()
    (testes / "test_a.py").write_text("from pacote.a import morta\n\nmorta()\n", encoding="utf-8")
    achados = {m.nome for m in mortos([tmp_path / "src"], tmp_path / "pyproject.toml")}
    assert achados == {"morta", "recursiva", "X"}


def test_nenhuma_marca_de_silencio() -> None:
    achados = marcas_de_silencio(arquivos_py(SRC, ROOT / "tests", ROOT / "scripts"))
    assert not achados, achados


def test_controle_a_marca_de_silencio_e_achada(tmp_path: Path) -> None:
    f = tmp_path / "x.py"
    f.write_text("import os  # " + MARCAS[0] + ": F401\n", encoding="utf-8")
    assert marcas_de_silencio([f]) == ["x.py:1"]


def test_a_config_liga_as_regras_sem_excecao() -> None:
    cfg = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert problemas_da_config(cfg) == []


def test_controle_a_excecao_na_config_e_achada() -> None:
    cfg = {"tool": {"ruff": {"lint": {"select": ["F"], "per-file-ignores": {"x.py": ["F401"]}}},
                    "mypy": {"strict": True, "overrides": []}}}
    achados = problemas_da_config(cfg)
    assert "ruff: 'per-file-ignores'" in achados
    assert any("faltam as regras" in a for a in achados)
    assert "mypy: 'overrides'" in achados
