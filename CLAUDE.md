# Pixel Asset Engine

A engine de pixel art (pacote `pixel_forge`, CLI `pfe`). As regras de trabalho e de desenho estão em `docs/regras.md`;
o estado e o próximo passo, em `docs/estado.md`; as decisões, em `docs/decisoes.md`.

- Instalação: `uv sync`. Validação antes de cada commit: `uv run python scripts/check.py` (`--fast` no ciclo rápido).
- Oráculo de pixel: `uv run python scripts/oraculo.py` (lê o `pixel-engine` por `git archive`, nunca escreve nele).
- Para criar, completar ou corrigir um asset, use a skill `.claude/skills/pixel-asset-engine/`.
