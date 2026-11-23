"""A validação completa num comando: ruff, mypy estrito e a suíte (as travas, o código morto e o oráculo gravado).

Uso:
    python scripts/check.py            # tudo (o que vale antes do commit)
    python scripts/check.py --fast     # a suíte sem os testes marcados `slow` (ciclo rápido; não vale para commit)
    python scripts/check.py tests/x    # só esses testes (ciclo rápido)

Roda com o Python que o chamou (`uv run python scripts/check.py` ou `.venv/Scripts/python.exe scripts/check.py`).
Executa todas as etapas mesmo que uma falhe e sai com 1 se alguma falhou.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from collections.abc import Sequence
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATHS = ["src", "tests", "scripts"]


def etapas(fast: bool, testes: Sequence[str]) -> list[tuple[str, list[str]]]:
    py = sys.executable
    pytest = [py, "-m", "pytest", "-n", "auto", "--dist", "loadscope", *testes]
    if fast and not testes:
        pytest += ["-m", "not slow"]
    return [
        ("ruff", [py, "-m", "ruff", "check", *PATHS]),
        ("mypy", [py, "-m", "mypy"]),
        ("pytest", pytest),
    ]


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fast", action="store_true", help='pytest -m "not slow"')
    ap.add_argument("testes", nargs="*", help="arquivos ou pastas de teste (no lugar da suíte)")
    args = ap.parse_args(argv)
    t0 = time.perf_counter()
    falhas = []
    for nome, cmd in etapas(args.fast, args.testes):
        t = time.perf_counter()
        codigo = subprocess.run(cmd, cwd=ROOT).returncode
        print(f"== {nome}: {'ok' if codigo == 0 else 'FALHOU'} em {time.perf_counter() - t:.1f}s", flush=True)
        if codigo:
            falhas.append(nome)
    print(f"resumo: {'ok' if not falhas else 'FALHOU: ' + ', '.join(falhas)} | total {time.perf_counter() - t0:.0f}s")
    if args.fast or args.testes:
        print("aviso: suíte parcial; antes do commit rode `python scripts/check.py` sem argumentos.")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
