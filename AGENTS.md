# Pixel Asset Engine (para agentes)

Leia `docs/regras.md` antes de trabalhar: é a fonte única das regras. O estado está em `docs/estado.md`.

- Instalação: `uv sync`. Validação antes de cada commit: `uv run python scripts/check.py`.
- Para criar, completar ou corrigir um asset, siga a skill `.agents/skills/pixel-asset-engine/SKILL.md` (gerada da
  `.claude/skills/` por `scripts/skill.py`). O agente do jogo pede pelo formulário `docs/pedido.md`.
