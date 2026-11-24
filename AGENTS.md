# Pixel Asset Engine (para agentes)

Leia `docs/regras.md` antes de trabalhar: é a fonte única das regras. O estado está em `docs/estado.md`, e a visão
geral, no `README.md`.

- Instalação: `uv sync`. Validação antes de cada commit: `uv run python scripts/check.py` (sem o `uv` no PATH,
  `.venv/Scripts/python.exe scripts/check.py`).
- Para criar, completar ou corrigir um asset, siga a skill `.agents/skills/pixel-asset-engine/SKILL.md` (gerada da
  `.claude/skills/` por `scripts/skill.py`). O agente do jogo pede pelo formulário `docs/pedido.md`.
- Remoto: `origin` = `git@github.com:gabrielAlencar33564/pixel-engine.git`, branch `main`.
- O oráculo de pixel (`scripts/oraculo.py`) lê um clone local do motor antigo (`PFE_ORACULO_REPO`); esse clone só se
  lê, sem commit, `pull` nem `push`. Os testes usam os esperados gravados em `tests/fixtures/oraculo/`.
