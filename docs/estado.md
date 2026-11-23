# Estado da engine corrigida

Plano: `docs/plano.md` (cópia do plano de 2026-11-23). Decisões: `docs/decisoes.md`. Regras: `docs/regras.md`.
Oráculo: o `pixel-engine` em 3df5fe42 (motor 2.3.0), só leitura (I7: `git status` limpo no início e agora).

## Feito

**N0 — o esqueleto com as travas.** Repositório novo (`main`, sem remoto), `uv`, ruff (F, ARG, ERA, C901, PLR0912/0913/
0915, sem lista de exceções), mypy estrito em `src`, `tests` e `scripts`, e `scripts/check.py`. As travas, verdes no
repositório vazio e cada uma com controle negativo (`tests/travas/`):
- código limpo (I10): código morto por referência, nenhuma marca de silêncio, a config sem exceção;
- camadas: render, rig e export não importam desenho nem movimento; núcleo e contratos não importam nada acima;
- nada de asset em `src/` (I4) e nada de treino nem acervo rastreado (I2);
- teto de 400 linhas por módulo e de 1 500 linhas em `docs/`;
- uma fonte de regras (I6): `CLAUDE.md`, `AGENTS.md` e a skill citam `docs/regras.md`, sem repetir; o espelho da skill.
O oráculo (`scripts/oraculo.py`): `git archive` do `pixel-engine` numa pasta temporária, com ambiente próprio.

## Números

| Medida | N0 |
|---|---|
| Linhas em `src/` | 1 |
| Arquivos rastreados | 21 |
| `check.py` completo | 9 s, 18 testes |

## Próximo passo

**N1 — o núcleo por demanda:** portar o mínimo para renderizar e exportar, igual ao oráculo, três fixtures sintéticas
(um bloco com sombra projetada, um tronco sólido de revolução, uma face com a luz pela normal). Ler antes a seção 4
do plano (o que nunca se porta).
