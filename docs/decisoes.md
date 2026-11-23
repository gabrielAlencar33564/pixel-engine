# Decisões

Uma linha por decisão que o plano (`docs/plano.md`) não fixa: a escolha e a regra que a justifica (seção 4 do plano:
1 o objetivo, 2 as invariantes, 3 o menor que funciona, 4 o que o `pixel-engine` fazia, se não for treino nem jeito
substituído). O porquê longo vai no commit.

## N0

- Linha de 120 colunas no ruff, sem ignorar o E501: o limite de formato vale para tudo (I10; regra 3).
- Os tetos de complexidade e argumentos são os padrões do ruff (C901 10, PLR0912 12, PLR0913 5, PLR0915 50): o teto
  não é escolhido para caber no código, o código é desenhado para caber nele (I10).
- O código morto conta funções, classes, métodos e constantes de módulo, citados fora da própria definição em `src/` ou
  `scripts/`; os campos de modelo (o formato do arquivo) não entram, e a citação em teste não conta (I10; regra 3).
- O oráculo instala a cópia do `pixel-engine` (só `src`, `presets`, `schemas` e o `pyproject`) num ambiente próprio na
  pasta temporária e roda isolado (`-I`): nada é escrito no `pixel-engine` (I7) e o treino nem é copiado (I2).
- A skill se chama `pixel-asset-engine`, como a pasta, para não se confundir com a skill antiga `pixel-forge` (I6).
- Sem dependência de runtime no N0: cada uma entra com o primeiro código que a usa (seção 6, N0; regra 3).
