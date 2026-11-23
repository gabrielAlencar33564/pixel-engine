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

## N2

- O formato único é o da v2 (as mesmas chaves), sem `kind` nem versão (não há versão a migrar, I5) e sem o campo
  de rig (o tipo decide o rig); ganha a `categoria`, que o porte confere (seção 5).
- A peça é uma função sobre os argumentos já lidos; as funções intermediárias das gramáticas antigas não vêm
  (regra 3). Os auxiliares de desenho são métodos do contexto da peça (o teto de 5 argumentos não conta o `self`).
- A regra dos dois usos do plano v2 não vale: a peça que não foi substituída é vigente (o bocal, o aro, a parede de
  tábuas, o telhado de tabuinhas, o cercado, os fios) (objetivo; seção 5 lista as peças vigentes).
- O oráculo do kit roda o `pixel-engine` com o estilo base novo nos nomes antigos: confere o porte na mesma entrada,
  e a troca de paleta fica na prancha (I11).
- Os materiais de cena (céu, lua, água, pena, crista, chama) saem do estilo; com eles muda a tinta de contorno que a
  limpeza de cor isolada poupa (o índice 21 deixa de ser tinta). É parte da troca de paleta (seção 5).
- Os ids fixos do bocal e do cercado ficam (no empate, a ordem de desenho depende do id); duas peças de id fixo na
  mesma composição são recusadas com dica (I11; I8).
- O catálogo e o build já leem a composição (antecipam o N3) para nada ficar usado só por teste (I10).
- O teto da peça (12 argumentos, 250 linhas, 3 variações) é conferido pelo registro ao carregar, não só pelo teste
  (mecanismo 2: a correção vira recusa).
- A sombra de contato das vistas E, N e W sai reescalada para o oblíquo como a da S (no antigo só a S era): ela fica
  3:1 na tela em toda vista. Mudança intencional, com prancha (objetivo).
- O tronco em pé só tem o modo sólido de revolução: o chapado e o de volume por máscara eram o jeito substituído
  (I3: pedir `solido`, `sombra` ou `marca` é argumento desconhecido, recusado com a lista do que a peça aceita).
- A folhagem de copa é o `pontilhado`; a peça `pacotes` não existe no kit (seção 5; I3).
