# Pixel Asset Engine

A engine de pixel art (pacote `pixel_forge`, CLI `pfe`); a visão geral está no `README.md`. As regras de trabalho e de
desenho estão em `docs/regras.md`; o estado e o próximo passo, em `docs/estado.md`; as decisões, em `docs/decisoes.md`.

- Instalação: `uv sync`. Validação antes de cada commit: `uv run python scripts/check.py` (`--fast` no ciclo rápido).
  Sem o `uv` no PATH: `.venv/Scripts/python.exe scripts/check.py` e `.venv/Scripts/pfe.exe`.
- Para criar, completar ou corrigir um asset, use a skill `.claude/skills/pixel-asset-engine/`. Depois de editá-la,
  `uv run python scripts/skill.py` refaz a tabela de porte, o espelho em `.agents/skills/` e o `docs/pedido.md`.
- Remoto: `origin` = `git@github.com:gabrielAlencar33564/pixel-engine.git`, branch `main` (é esta engine desde
  2026-11-23; o histórico do motor antigo não está nele).

## O oráculo de pixel

- A engine desenha igual ao motor antigo pixel a pixel, salvo as mudanças intencionais de `docs/decisoes.md`. Os
  testes comparam com os esperados gravados em `tests/fixtures/oraculo/`.
- Regerar os esperados pede o clone local do motor antigo (`PFE_ORACULO_REPO`, padrão
  `D:\gabri\Projetos\Gabriel\pixel-engine`): `uv run python scripts/oraculo.py <casos> --kit --composicoes --animados`.
  O script lê o clone por `git archive` numa pasta temporária e passa a câmera da engine ao motor antigo.
- O clone antigo só se lê: nunca escreva, faça commit, `pull` ou `push` nele (o histórico dele não se liga à `main`
  do `origin`, e o push de lá desfaria a troca).
- Mudança intencional de pixel: tire o caso da igualdade com o oráculo, teste a propriedade nova com um controle que
  acusa o jeito antigo, registre em `docs/decisoes.md` e mostre a prancha do antes e do depois.
