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

## N1

- A câmera é uma constante (3/4 oblíquo, 45°, profundidade 0,35): a vista da IR guarda só a direção (plano v2, seção
  3: "não há outro modo de câmera"; regra 3).
- O estilo guarda valores, não interruptores: o contorno por dentro, o sel-out, o pixel-perfect, a sombra no chão
  projetada, a sombra entre planos e a limpeza de cor isolada são o jeito da engine (o único valor que o estilo base
  usava; regra 3). O oráculo converte com esses valores.
- A limpeza de cor isolada roda no render, não só no build: a prévia e o build dão o mesmo pixel (I8).
- Só entram as geometrias que as fixtures pedem (a face em leque, a revolução, a elipse); as outras entram com as
  peças do N2 (seção 4, por demanda).
- Não entram, até uma peça vigente pedir: a máscara de pixels importada, o decalque, o traço preso a ossos, a
  superfície em malha (`shade_facing`), a chama, as emendas, o contorno por fora e o volume por máscara (regra 3).
- O núcleo do N1 entra já ligado ao `pfe` (`build` de uma IR e `exportar`), senão ficaria usado só por teste (I10);
  no N3 o `build` passa a ler a composição.
- O pacote `pfe-jogo/1` perde os campos que o leitor de referência não lê (`kind`, `schema_version`, `layout`,
  `padding_px`, `trimmed`, `tags`, `image`) (regra 3).
- O quadro cortado pelo canvas e as cores acima do limite do estilo são recusas com dica, não um relatório (I8).
- A ordem dos argumentos e o desenho por objetos (`Camadas`, `Tabelas`, `NaJanela`) vêm do teto de 5 argumentos e
  da complexidade 10: o render antigo passava 16 buffers soltos por função (I10).
