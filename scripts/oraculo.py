"""O oráculo de pixel (I11): o `pixel-engine` exportado por `git archive HEAD` numa pasta temporária, com um ambiente
próprio, roda a mesma entrada que a engine nova. Nada é escrito no `pixel-engine` (I7): o `git archive` só lê, e a
cópia, o ambiente e a saída ficam na pasta temporária.

Uso:
    python scripts/oraculo.py --versao     # exporta (uma vez por commit) e mostra o commit e a versão do motor antigo
"""

from __future__ import annotations

import argparse
import io
import os
import subprocess
import sys
import tarfile
import tempfile
from collections.abc import Sequence
from pathlib import Path

REPO = Path(os.environ.get("PFE_ORACULO_REPO", r"D:\gabri\Projetos\Gabriel\pixel-engine"))
CACHE = Path(tempfile.gettempdir()) / "pfe-oraculo"
# só o que instala e roda o motor antigo (o `challenge/` e o resto do treino ficam de fora da cópia)
CAMINHOS = ["src", "presets", "schemas", "pyproject.toml", "README.md", "LICENSE"]


def commit() -> str:
    return subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"], capture_output=True, text=True,
                          check=True).stdout.strip()


def python_da_copia(destino: Path) -> Path:
    return destino / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def exportar(sha: str) -> Path:
    """A cópia do `pixel-engine` no commit ``sha``, instalada num ambiente próprio (feita uma vez por commit)."""
    destino = CACHE / sha[:12]
    if (destino / ".pronto").exists():
        return destino
    tar = subprocess.run(["git", "-C", str(REPO), "archive", "--format=tar", sha, *CAMINHOS], capture_output=True,
                         check=True).stdout
    destino.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(tar)) as arquivo:
        arquivo.extractall(destino, filter="data")
    subprocess.run(["uv", "venv", "--quiet", "--python", "3.12", str(destino / ".venv")], check=True)
    subprocess.run(["uv", "pip", "install", "--quiet", "--python", str(python_da_copia(destino)), str(destino)],
                   check=True)
    (destino / ".pronto").write_text(sha, encoding="utf-8")
    return destino


def rodar(destino: Path, script: Path, entrada: bytes) -> bytes:
    """Roda ``script`` no Python da cópia, isolado (``-I``), com ``entrada`` no stdin; devolve o stdout."""
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    feito = subprocess.run([str(python_da_copia(destino)), "-I", str(script)], input=entrada, capture_output=True,
                           cwd=destino, env=env)
    if feito.returncode:
        raise RuntimeError(f"o oráculo falhou:\n{feito.stderr.decode('utf-8', 'replace')}")
    return feito.stdout


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--versao", action="store_true", help="exporta e mostra o commit e a versão do motor antigo")
    args = ap.parse_args(argv)
    sha = commit()
    destino = exportar(sha)
    if args.versao:
        sonda = destino / "versao.py"
        sonda.write_text("import importlib.metadata as m\nprint(m.version('pixel-forge-engine'))\n", encoding="utf-8")
        print(f"pixel-engine {sha[:12]} | motor {rodar(destino, sonda, b'').decode().strip()} | {destino}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
