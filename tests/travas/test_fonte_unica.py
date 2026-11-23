"""I6: uma fonte de regras. O ``docs/regras.md`` (até 120 linhas) é citado pelo ``CLAUDE.md``, pelo ``AGENTS.md`` e
pela skill única, e nenhum deles repete uma regra dele. A skill tem o espelho em ``.agents/skills/``, igual."""

from __future__ import annotations

import re
from pathlib import Path

from .fontes import ROOT

REGRAS = "docs/regras.md"
TETO_REGRAS = 120


def regras(texto: str) -> list[str]:
    """As regras do ``regras.md``: o texto de cada item de lista, sem o marcador."""
    return [re.sub(r"\s+", " ", linha[2:]).strip() for linha in texto.splitlines() if linha.startswith("- ")]


def problemas(raiz: Path) -> list[str]:
    fonte = raiz / REGRAS
    if not fonte.exists():
        return [f"falta {REGRAS}"]
    texto = fonte.read_text(encoding="utf-8")
    out = [f"{REGRAS} tem {len(texto.splitlines())} linhas"] if len(texto.splitlines()) > TETO_REGRAS else []
    skills = sorted((raiz / ".claude" / "skills").glob("*/SKILL.md"))
    if len(skills) != 1:
        out.append(f"esperava uma skill, achou {len(skills)}")
    for doc in [raiz / "CLAUDE.md", raiz / "AGENTS.md", *skills]:
        if not doc.exists():
            out.append(f"falta {doc.name}")
            continue
        corpo = re.sub(r"\s+", " ", doc.read_text(encoding="utf-8"))
        if REGRAS not in corpo:
            out.append(f"{doc.relative_to(raiz).as_posix()} não cita {REGRAS}")
        out += [f"{doc.relative_to(raiz).as_posix()} repete: {r[:40]}" for r in regras(texto) if r in corpo]
    for skill in skills:
        espelho = raiz / ".agents" / skill.relative_to(raiz / ".claude")
        if not espelho.exists() or espelho.read_bytes() != skill.read_bytes():
            out.append(f"o espelho de {skill.parent.name} em .agents/skills/ difere")
    return out


def test_uma_fonte_de_regras() -> None:
    assert problemas(ROOT) == []


def test_controle_a_regra_repetida_e_o_espelho_velho_sao_achados(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / REGRAS).write_text("# Regras\n\n- Quem anda tem as 8 direções.\n", encoding="utf-8")
    (tmp_path / "CLAUDE.md").write_text(f"Leia {REGRAS}.\n", encoding="utf-8")
    (tmp_path / "AGENTS.md").write_text("Quem anda tem as 8 direções.\n", encoding="utf-8")
    skill = tmp_path / ".claude" / "skills" / "engine" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text(f"Siga {REGRAS}.\n", encoding="utf-8")
    espelho = tmp_path / ".agents" / "skills" / "engine" / "SKILL.md"
    espelho.parent.mkdir(parents=True)
    espelho.write_text("velho\n", encoding="utf-8")
    assert problemas(tmp_path) == [
        f"AGENTS.md não cita {REGRAS}",
        "AGENTS.md repete: Quem anda tem as 8 direções.",
        "o espelho de engine em .agents/skills/ difere",
    ]
