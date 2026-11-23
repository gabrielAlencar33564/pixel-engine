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
- O humano usa o rig `humano` (o `humanoid_v2` sem os ossos da cambalhota, do giro da coxa e do dedo do pé): o v3 e a
  cambalhota eram treino de combate (seção 4). O rig declara os papéis; a peça pede o papel, não o nome do osso.
- O andar é só a passada por poses-chave com IK (`andar_poses`); o andar de pêndulo era o jeito substituído (I3).
- A saia e o lenço são peças gerais novas, a lição da moleira: a barra da saia segue a coxa (35 %, 90 ms de atraso).
  Ficam provadas por teste sintético e o controle sem saia (mecanismo 1).
- O capuz com máscara, a ombreira e as molas de cabelo não vêm: eram treino de personagem e de combate (seção 4).
- O porte é a altura no mundo (o ponto mais alto no repouso, sem a sombra) contra a faixa da categoria, em humanos de
  1,65 m; o build recusa com o porte típico na dica. O catálogo de peças não confere: a peça sozinha não tem categoria.
- O quadrúpede é o corpo canino como peça (`corpo_canino`) no rig `canino` de pernas em Z; o modelo de rig declara a
  cadeia de IK de N segmentos de cada perna (o triângulo até o jarrete, os distais orientados no mundo). Vêm o parado
  e o passo lateral; a corrida, o galope e a bateria canina (sentar, deitar, latir, uivar) não vêm (treino de cena).
- A elipse orientada (girada com o osso) entra no núcleo: o ombro e a anca do quadrúpede a usam (I1, pelo oráculo).
- A luz é da câmera, como ela (`views.camera.LUZ`, de cima e da esquerda), e sai do estilo: um grau de liberdade a
  menos, e o canvas pode medir a sombra no chão sem ler o estilo (objetivo; I10).
- O canvas inclui a sombra que o asset projeta no chão: no antigo ela passava do canvas e era cortada calada (o abrigo,
  o marco e o quadrúpede sairiam recusados por `QUADRO_CORTADO`). O canvas só cresce à direita e para baixo; o pivô
  fica; o oráculo compara o recorte do tamanho antigo e confere que fora dele só há sombra (mudança intencional).
- A sombra de contato do quadrúpede é a pegada dele (não é reescalada para o oblíquo): ela gira com o corpo, e a
  reescalada ficava 2× mais longa que ele de lado. A do humano fica como estava (arte aprovada, cabe no canvas).
- O oráculo grava também o hash sem a sombra no chão; o kit do quadrúpede compara esse, e o movimento dele compara o
  quadro inteiro com o antigo animando a mesma IR nova (o passo antigo pede `gait` 1, o único que a engine faz).
- As receitas são dados do motor conferidos por teste: o `exige` do passo (o `gait`) e a recusa do balanço curto não
  vêm (nenhum pedido muda a receita).

## N3

- O asset vive no acervo como `composicoes/<id>.r<n>.json`; o `build` o registra. A mesma revisão com outro desenho é
  recusada (`IDENTIDADE`) e o `atualizar` grava a seguinte: é a identidade imutável sem `identity/` nem candidatos
  (a composição não sorteia; I5, "o menor que funciona").
- O `checar` e o `build` passam pelo mesmo percurso (`renderizar`, com o porte, o quadro cortado e as cores); a
  `previa` aplica as mesmas recusas ao repouso de cada vista e grava a prancha (I8).
- O `revisar` guarda o veredito do dono por build (`aprovado` ou `ajustar`, a nota e quem); o `exportar --publicar`
  só sai com o aprovado (`release_candidate`, `approved`). Nenhum comando aprova sozinho (I9).
- O `olhar` lê o pacote como o jogo lê; o `conjunto` põe os assets pelo chão, com o humano de 1,65 m de régua.
- O canvas só mede a sombra no chão das partes que o render projeta (faces, traços e elipses alinhadas): a copa
  pontilhada não projeta, e a árvore voltava 50 px mais larga sem isso.
- O balanço por deslocamento e o giro do prop vêm junto (o contrato os declara: aceitar e não gerar seria mentir, I8);
  o balanço da árvore sintética é igual ao antigo quadro a quadro; a recusa do giro mora na validação (a prévia a vê).

## N4

- A skill é a fonte do caminho; `scripts/skill.py` gera dela a tabela de porte (dos dados do motor), o espelho em
  `.agents/skills/` e o formulário `docs/pedido.md`, e o teste confere que estão em dia (I6, sem texto em dobro).
- Os quatro exemplos são assets do padrão vigente sem relação com os pedidos da prova (um banco, uma folhosa, um
  viajante, um canino) e passam pelo mesmo `renderizar` do build.

## N5, rodada 1 → motor

- A recusa de formato diz a regra, o campo e o valor recebido; a IR que sai inválida é `MOTOR` (defeito da engine),
  nunca um erro do pedido com o caminho da IR.
- O sprite vai até 512 px de lado (a árvore grande de 6 m com a sombra no chão passava de 256); passar disso é
  `TAMANHO`, com a medida e a escala na dica. O galho grosso tem até 32 linhas: nunca passa dos 64 vértices.
- O traço que cita parte inexistente é recusado com as parecidas; a prévia lista os ids das partes. O nó que não
  desenha nada é recusado (`NO_VAZIO`).
- A camada do nó separa os nós (`camada × 100`): as faces internas de uma peça (o miolo do bocal) não sobem mais por
  cima do nó de camada seguinte.
- O catálogo traz os argumentos de cada variação; as descrições ambíguas (o achatado, a cota da parede) dizem a
  unidade. A `reference` (a ficha) vai até 2000 caracteres.
- A largura da saia mede a barra pelo quadril (100 % reta, 160 % em A, 220 % rodada): pela coxa, dobrar a largura
  abria 2 px. O `olhar` amplia pelo tamanho do quadro (o humano saía a 1×).
