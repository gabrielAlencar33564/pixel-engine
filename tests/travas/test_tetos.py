"""Os tetos sem lista de exceções: 400 linhas por módulo de ``src/`` e 1 500 linhas em ``docs/``."""

from __future__ import annotations

from pathlib import Path

from .fontes import ROOT, SRC, arquivos_py

TETO_MODULO = 400
TETO_DOCS = 1500


def linhas(p: Path) -> int:
    return len(p.read_text(encoding="utf-8").splitlines())


def modulos_acima(arquivos: list[Path]) -> list[str]:
    return [f"{p.name}: {linhas(p)}" for p in arquivos if linhas(p) > TETO_MODULO]


def linhas_de_docs(pasta: Path) -> int:
    return sum(linhas(p) for p in pasta.rglob("*") if p.is_file())


def test_nenhum_modulo_acima_do_teto() -> None:
    assert modulos_acima(arquivos_py(SRC)) == []


def test_controle_o_modulo_de_401_linhas_e_achado(tmp_path: Path) -> None:
    (tmp_path / "grande.py").write_text("x = 1\n" * (TETO_MODULO + 1), encoding="utf-8")
    (tmp_path / "justo.py").write_text("x = 1\n" * TETO_MODULO, encoding="utf-8")
    assert modulos_acima(sorted(tmp_path.glob("*.py"))) == [f"grande.py: {TETO_MODULO + 1}"]


def test_docs_dentro_do_teto() -> None:
    assert linhas_de_docs(ROOT / "docs") <= TETO_DOCS


def test_controle_docs_acima_do_teto_e_medido(tmp_path: Path) -> None:
    (tmp_path / "a.md").write_text("linha\n" * 1000, encoding="utf-8")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "b.md").write_text("linha\n" * 501, encoding="utf-8")
    assert linhas_de_docs(tmp_path) == TETO_DOCS + 1
