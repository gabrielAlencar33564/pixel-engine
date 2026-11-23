"""I2 e I4: nenhum treino na pasta nova e nada em ``src/`` que conheça um asset.

Os nomes de treino (as cenas, os personagens, a fauna, a flora e os props com que a engine antiga foi treinada) e os
pedidos da prova de fora não aparecem em nome de arquivo rastreado, em identificador nem em texto do código. O
acervo de trabalho (composições, builds, exports) não fica no git, salvo as fixtures de ``tests/fixtures/``."""

from __future__ import annotations

import ast
import subprocess
from pathlib import Path

from .fontes import ROOT, SRC, arquivos_py, palavras

TREINO = frozenset({
    # cenas
    "clareira", "moinho", "riacho", "sitio", "estaleiro", "cais", "uivo", "terreiro",
    # flora
    "betula", "birch", "pinheiro", "pine", "cerejeira", "blossom", "momiji", "maple", "salgueiro", "willow",
    "baoba", "baobab", "bambu", "bamboo", "taboa",
    # fauna e personagens
    "lobo", "wolf", "mossling", "raposa", "fox", "cao", "ninja", "espadachim", "swordsman", "aldeao", "villager",
    "manequim", "mannequin", "elfa", "elf", "cervo", "deer", "golem", "dragao", "dragon", "andarilha", "serpe", "xama",
    "heron", "garca", "hen", "galinha", "fisher", "pescador", "courier",
    # props
    "poco", "barril", "caixote", "feno", "cocho", "lantern", "clothesline",
    # os pedidos da prova de fora: a engine não pode conhecê-los de antemão
    "carvalho", "roble", "oak", "camponesa",
})
PASTAS_DE_ACERVO = {"builds", "exports", "acervo", "composicoes"}


def nomes_de_treino(texto: str) -> set[str]:
    return palavras(texto) & TREINO


def _docstrings(arvore: ast.AST) -> set[int]:
    out = set()
    for no in ast.walk(arvore):
        if isinstance(no, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef) and no.body:
            primeiro = no.body[0]
            if isinstance(primeiro, ast.Expr) and isinstance(primeiro.value, ast.Constant):
                out.add(id(primeiro.value))
    return out


def textos_do_codigo(fonte: str) -> list[str]:
    """Os identificadores (nomes, atributos, argumentos, definições) e os textos que não são docstring."""
    arvore = ast.parse(fonte)
    docs = _docstrings(arvore)
    out: list[str] = []
    for no in ast.walk(arvore):
        if isinstance(no, ast.Name):
            out.append(no.id)
        elif isinstance(no, ast.Attribute):
            out.append(no.attr)
        elif isinstance(no, ast.arg):
            out.append(no.arg)
        elif isinstance(no, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            out.append(no.name)
        elif isinstance(no, ast.Constant) and isinstance(no.value, str) and id(no) not in docs:
            out.append(no.value)
    return out


def asset_no_codigo(arquivos: list[Path], raiz: Path) -> list[str]:
    out = []
    for p in arquivos:
        achados = nomes_de_treino(p.relative_to(raiz).as_posix())
        for texto in textos_do_codigo(p.read_text(encoding="utf-8")):
            achados |= nomes_de_treino(texto)
        out += [f"{p.relative_to(raiz).as_posix()}: {n}" for n in sorted(achados)]
    return out


def treino_rastreado(caminhos: list[str]) -> list[str]:
    out = []
    for c in caminhos:
        partes = c.split("/")
        if nomes_de_treino(c):
            out.append(f"{c}: {sorted(nomes_de_treino(c))}")
        elif partes[:2] != ["tests", "fixtures"] and (PASTAS_DE_ACERVO & set(partes[:-1])):
            out.append(f"{c}: acervo fora de tests/fixtures")
    return out


def rastreados() -> list[str]:
    saida = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"], cwd=ROOT,
                           capture_output=True, text=True, check=True).stdout
    return [c for c in saida.splitlines() if c]


def test_nada_em_src_conhece_um_asset() -> None:
    assert asset_no_codigo(arquivos_py(SRC), SRC) == []


def test_controle_o_tom_de_especie_e_o_modulo_de_cena_sao_achados(tmp_path: Path) -> None:
    (tmp_path / "tons.py").write_text('"""Os tons da bétula."""\nTONS = ["birch_leaf", "folha"]\n', encoding="utf-8")
    (tmp_path / "clareira.py").write_text("X = 1\n", encoding="utf-8")
    (tmp_path / "ok.py").write_text('"""Fala do pinheiro só na docstring."""\nY = "folha_escura"\n',
                                    encoding="utf-8")
    assert asset_no_codigo(sorted(tmp_path.glob("*.py")), tmp_path) == ["clareira.py: clareira", "tons.py: birch"]


def test_nada_de_treino_nem_acervo_rastreado() -> None:
    assert treino_rastreado(rastreados()) == []


def test_controle_o_treino_e_o_acervo_rastreados_sao_achados() -> None:
    caminhos = ["challenge/lobo/build.json", "docs/regras.md", "acervo/builds/x.json",
                "tests/fixtures/exemplos/composicoes/arvore.r1.json", "src/pixel_forge/design/kit/pecas_betula.py"]
    assert treino_rastreado(caminhos) == [
        "challenge/lobo/build.json: ['lobo']",
        "acervo/builds/x.json: acervo fora de tests/fixtures",
        "src/pixel_forge/design/kit/pecas_betula.py: ['betula']",
    ]
