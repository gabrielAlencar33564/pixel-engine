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

## N5, rodada 2

- A prova passou. A dica do `TRACO` passou a listar as partes do asset (mandava rodar a prévia, que recusava o mesmo
  traço), e o catálogo diz as partes de cada peça: depois da prova, sem rodada nova (a correção não muda pixel).

## Depois da prova: a câmera mais de cima (pedido do dono, 2026-11-23)

- A profundidade da câmera sobe de 0,35 para 0,6 (o dono escolheu entre 0,35, 0,5 e 0,6 numa prancha da prova); a
  altura continua a cos 45°. O oráculo passa a câmera ao `pixel-engine`, que aceitava a profundidade por asset (ADR
  0149): o núcleo segue igual a ele pixel a pixel, os dois a 0,6. A versão do motor sobe para 0.2.0.
- O id do build leva os pixels: com a câmera nova e a versão velha, o build regravou a prova de 0,35 com o mesmo id
  (dois desenhos, um nome). Os builds de 0,35 foram restaurados nos ids deles; os de 0,6 têm ids novos.
- As faces de uma peça vão nos degraus da camada do nó (`Ctx.empilha` soma a camada; degrau de 0 a 99, fora disso
  é erro do kit). Os telhados, a porta, a janela, o bocal e o barril empilhavam em camadas absolutas: a palha do nó na
  camada 10 caía na 0, e a câmera de 0,6 mostrou as pedras da parede por cima da beira do telhado do abrigo. Muda o
  pixel do abrigo e do poço (a água da frente cobre os quadris; os aros do balde ficam por cima do bocal); o kit, o
  marco, o carvalho e a camponesa ficam iguais. A versão não sobe: o id do build já leva os pixels.

## O CLI depois da análise (2026-11-24)

- O `build` confere a identidade, constrói e só então registra a composição: a que ele recusava (o porte, o quadro
  cortado) ficava no acervo, e a correção na mesma revisão saía recusada por `IDENTIDADE` (I8; I5).
- A saída do `pfe` é UTF-8 também redirecionada: no Windows ela caía no cp1252, o JSON chegava quebrado a quem o lê e
  a recusa com um caractere de fora dele (`→`) morria num erro de codificação, sem código nem dica (I8).

## O humano: o braço no repouso e no andar (pedido do dono, 2026-11-24)

- O braço abre 6° no repouso (eram os 15° do `pixel-engine`): a câmera achata a altura, os 15° liam ~21° e as mãos
  caíam a 1,9× a largura dos ombros uma da outra; a 6° ficam a 1,4×. É uma constante do corpo (`ABRE_BRACO_MDEG`), não
  um argumento: o jeito antigo não existe mais na engine (regra 3). Mudança intencional, com prancha.
- O oráculo do humano (o vestido e as peças do kit) compara na abertura do antigo: o teste põe a constante em 15°, e o
  corpo, o rig, o movimento e o render seguem iguais a ele pixel a pixel. A abertura nova é provada pela medida das
  mãos, com o controle a 15°. Os esperados não foram regerados (I11).
- No andar, o ombro balança 16° e o cotovelo dobra até 16° a mais (eram 23° e 26°): a câmera achata a altura, os 23°
  liam ~31°, e de perfil o braço da frente esticava como quem aponta. Os 16° são os 23° vistos pela câmera
  (tan 23° × cos 45°). As mãos no andar de perfil caem de 55 % para 40 % da altura do corpo. Mudança intencional, com
  prancha; o oráculo do andar compara com a amplitude do antigo posta na receita, como o braço do repouso.
- No parado os pés ficam desencontrados (`avanco_m` na receita: o esquerdo 5 cm à frente, o direito 5 cm atrás, o
  lado da frente do primeiro quadro do andar): de perfil um pé cobria o outro, e agora ficam a 3 px. É da receita do
  parado, não do repouso do rig: o andar parte do repouso e sairia torto. O braço desencontrado (±6°) foi medido e
  não veio: a mão de lá continua atrás do tronco. Mudança intencional, com prancha; o oráculo tira o avanço.

## A conferência do que se vê (pedido do dono, 2026-11-24)

- O quadro guarda os pixels de que cada parte é dona, já com a oclusão, e quantos deles tocam a borda da figura. A
  prévia diz, por vista, as partes que a vista desenha e nenhum pixel mostra (`escondidas`) e os pixels de cada traço
  (`tracos`): a análise do asset deixa de depender só de olhar a prancha (I8).
- O traço `observable` sem pixel em nenhuma vista é recusado (`TRACO_ESCONDIDO`), e o de `reads_in_silhouette` que
  nunca toca a borda também (`TRACO_SEM_SILHUETA`), na prévia e no build pelo mesmo caminho. Os dois campos existiam
  no formato e nenhum código os lia: o traço só conferia se a parte existia (I8: aceitar e não conferir é mentir).

- A radiografia (`pfe radiografia`) amplia o asset pela geometria (a IR com toda medida até 4× maior, não o pixel) e
  o mostra em elevação, sem a câmera do jogo, e na câmera do jogo. A lente da elevação é só de diagnóstico: a câmera
  do asset segue uma constante, e nenhum quadro do build passa pela lente (a sombra no chão não sai nela).
- As medidas do corpo humano saem da máscara inteira de cada parte na radiografia, cada uma com a faixa de um corpo
  real. As faixas são do cânone de desenho e da antropometria, com folga, postas por quem escreveu a medida e não
  conferidas numa fonte: o dono as ajusta. A régua é provada num corpo sintético de proporções reais, com um
  controle por defeito.
- As medidas do corpo do kit fora da faixa são uma lista fixa no teste (`DEFEITOS_DO_MODELO`): a correção do
  modelo tira o item da lista, e nenhuma medida nova sai da faixa sem aparecer ali. A medida não vira recusa do
  build enquanto o modelo não é corrigido: recusaria todo humano.

## O humano: o tronco e os ombros (escolha do dono, 2026-11-24)

- A junta do ombro fica 3,5 % da estatura abaixo da base do pescoço (`OMBRO_CAI`). Ficava na mesma altura, e o alto
  da esfera do ombro batia no queixo; agora fica 3 % da estatura abaixo dele.
- O corpo ganhou a linha do ombro (`trap_l`, `trap_r`): um fuso da base do pescoço à junta, que fecha o vão de 4 % da
  estatura entre o tronco e a esfera. Fica no grupo de contorno do braço e sem linha interna, com a ponta a 0,96 do
  raio da esfera: no grupo do peito, ou com o mesmo raio, as duas peças disputavam o pixel do canto, e o contorno da
  peça fina (que vai para fora) punha espinhos na silhueta do ombro.
- O peito e a cintura entram um no outro (`PEITO`, `CINTURA`): o tronco afinava a 0,51 da largura do peito entre
  as duas bolas, e agora a 0,76. A medida nova `cintura_sobre_o_peito` (de 0,70 a 1,0) entra na radiografia.
- O pescoço tem 6,6 % da estatura de largura (eram 4,8 %).
- O braço e o antebraço têm 0,90 do tamanho real (0,167 e 0,131 da estatura). A cabeça de 1/6 tira altura do que
  fica entre o queixo e o quadril (0,30 da estatura, contra 0,34 no corpo real: 0,89), e com o ombro mais baixo o
  braço do tamanho real punha a mão 1,4 px abaixo, no meio da coxa. A 0,90 a mão fica na altura de antes. A mão não
  encolheu.
- A jaqueta segue o tronco: a ombreira (`jacket_yoke_l`, `jacket_yoke_r`) é a linha do ombro com 0,3 px de folga, no
  grupo da manga; a manga começa na junta (começava 5 % acima e fazia um gomo sobre o ombro); o peito e a cintura
  dela entram um no outro. Sem manga, a ombreira é a alça (70 % da linha) e o ombro fica nu.
- O oráculo do humano compara no tronco do antigo: o teste põe as constantes de volta e tira as partes da
  linha do ombro, e o rig, a roupa, o movimento e o render seguem iguais a ele pixel a pixel. A forma nova é provada
  pelas medidas da radiografia; o controle é o tronco do antigo, que sai da faixa nas quatro medidas. A lista
  `DEFEITOS_DO_MODELO` ficou com as quatro da cabeça. Os esperados não foram regerados (I11).
- O que mudou de visibilidade, conferido nas `escondidas` do viajante e do vestido, antes e depois: de perfil a
  manga de lá fica inteira atrás do corpo (o gomo dela aparecia acima do ombro de cá); a aba de cima da gola passa
  a tocar a borda de perfil; no vestido a cintura da jaqueta some sob o peito e a faixa fora da vista S. Olho,
  chapéu e cabelo não mudaram.

## O humano: o peito em cunha (pedido do dono, 2026-11-24)

O dono viu o busto como uma bola: o personagem masculino parecia ter seios.

- Eram três causas. O peito era um elipsoide (uma bola de 10 px), com o seu próprio grupo de contorno e a sua
  própria sombra: a engine riscava a linha de contorno sob ele, na cintura, e escurecia a borda de baixo dele. Na
  jaqueta não havia a linha, mas o peito e a cintura dela sombreavam cada um por si.
- O peito é uma cunha (`peito`, em `kit/humano.py`): um fuso de cada lado, do alto do peito (0,78 do tronco) à
  cintura (0,43), fechado em cima e embaixo. A seção é um estádio, e a frente, as costas e os lados são retas. A
  largura e a profundidade são as de antes (a profundidade, 0,95 e 0,80 do fundo do peito).
- O peito e a cintura são uma massa só: o mesmo grupo de contorno (`torso`) e a marca `shade_group`, no corpo e
  na jaqueta. Não há linha nem sombra entre os dois, e a luz e a sombra caem no tronco inteiro.
- A cunha acaba a 0,43 do tronco: mais baixa, a da jaqueta cobria a faixa. Pôr a faixa por cima do peito por regra
  foi tentado e descartado: a regra vale na máscara inteira da faixa, e a metade de trás dela aparecia sobre a
  jaqueta nas diagonais.
- A gola da jaqueta assenta na frente da cunha (`frente_do_peito`); o `_surface_y` da bola saiu.
- A medida nova `peito_na_caixa` (a área do peito sobre a da caixa dele, de 0,83 a 1,0) entra na radiografia: a
  bola dava 0,79 e a cunha dá 0,87. A faixa é uma aproximação, como as outras. `cintura_sobre_o_peito` foi de
  0,76 a 0,81.
- O oráculo segue ancorado no tronco do antigo: o teste repõe a bola (a do corpo e a da jaqueta), a frente dela
  para a gola e cada massa no seu grupo, sem `shade_group`. O teste novo conta, no passe de contorno da engine, os
  pixels de linha entre o peito e a cintura (0) e confere que os dois sombreiam como um volume; o controle é o
  tronco do antigo (7 pixels de linha, dois volumes). Os esperados não foram regerados (I11).
- O que mudou de visibilidade, nas `escondidas` de nove composições, antes e depois: de perfil a aba de baixo da
  gola passa a aparecer (1 px, na borda) e a de cima fica por dentro; no vestido a cintura da jaqueta aparece nas
  diagonais e a ombreira de lá some de perfil; sem manga, o braço de lá fica atrás do peito na vista SW. Olho,
  chapéu e cabelo não mudaram.

## O humano: a cabeça e os olhos (pedido do dono, 2026-11-24)

O dono viu os olhos estranhos, o perfil com cabelo como o de um alienígena e, na primeira tentativa (rejeitada), os
olhos atravessando o chapéu.

- O olho não é detalhe. A tentativa rejeitada o marcava como `detail`, que vence a peça até 2 px à frente dele: por
  isso atravessava a aba. Agora ele só perde o contorno em volta (`no_inner_outline`: num rosto de 6 px o contorno
  de cada olho virava uma máscara escura) e a limpeza de cor isolada o poupa (`eye`). O chapéu, o cabelo e o lenço
  o cobrem pela profundidade, sem regra.
- O olho tem 1 px de largura e fica a 58 % da altura da cabeça (`OLHO_Z`), não a 50 % como no corpo real: a câmera
  a 45° mostra o alto da cabeça e comprime a face, e a 50 % o olho caía a 74 % da cabeça na tela, colado ao
  queixo. A 58 % cai a ~62 %. Estava a 82 % (na testa, onde a aba e o cabelo assentam). É estilização, como a
  cabeça de 1/6.
- A cabeça (`CRANIO`, `FACE`, `QUEIXO`, `NARIZ`, em `kit/humano.py`): o crânio com o alto no alto da cabeça; a
  face com 0,62 da cabeça de largura (eram 0,52: lia como lâmpada) e rente à testa (a mandíbula avançava como um
  focinho); o nariz, parte nova (`nose`), é a ponta do perfil a 40 % da altura. As quatro são uma massa só
  (`shade_group`), como o tronco.
- O cabelo preso e o lenço são cascas sobre o crânio (`CABELO`, `LENCO`): o centro recua e sobe, os raios crescem
  um pouco, e a face sai pela frente de baixo, pela profundidade. Antes o cabelo recuava 20 % da cabeça (o perfil
  alongado) e, de frente, uma regra punha o crânio inteiro por cima dele e do lenço: sobrava um aro, e o nó do
  lenço ia parar na testa. As regras saíram. Sem linha de contorno na testa; no cabelo, também sem a sombra
  projetada (lia como aba de chapéu).
- O chapéu não mudou; segue o crânio novo. Com a aba de 150 % da cabeça (o viajante) os olhos aparecem sob ela; a
  partir de ~160 % a aba os cobre, pela geometria. O catálogo diz isso no argumento da aba.
- O olho recuado para dentro do crânio (para sair da borda no perfil) foi medido e não veio: de frente ele subia
  para a linha do cabelo.
- As quatro medidas da cabeça entram na faixa (rosto 0,63 → 0,85; olhos 0,82 → 0,55; ponta do perfil 0,25 → 0,38;
  cabelo 1,25 → 1,11), e o corpo do kit não tem mais medida fora da faixa. As faixas seguem aproximações minhas.
- O oráculo compara na cabeça do antigo: o teste repõe as três massas (sem o nariz, cada uma sombreada sozinha),
  os olhos e o cabelo dele. Os controles: a cabeça do antigo sai da faixa nas quatro medidas e tem o contorno em
  volta dos olhos. O lenço não tem oráculo (peça nova): o teste confere o rosto à mostra e o nó só de costas. Os
  esperados não foram regerados (I11).

## O humano: o formato da cabeça e o cabelo (pedido do dono, 2026-11-24)

Depois da mudança 12 o dono ainda viu o cabelo como um gorro e a cabeça sem formato de cabeça.

- A radiografia (a elevação) não via o defeito: as medidas estavam na faixa. Ele está na câmera do jogo. A 45° o
  crânio é uma bola de 7 px e a face, com 0,62 da cabeça, saía com 5 px sob ela, como um apêndice. A face passa a
  0,68 da cabeça (`FACE`): na tela tem a largura do crânio, e a cabeça é um bloco arredondado só.
- O queixo fica rente à testa (`QUEIXO`; recuava 1 px no perfil). O nariz desce a 33 % da altura (`NARIZ`): a
  40 % caía na fileira do olho, como um bico. O centro dele fica à frente da face: rente a ela, de perfil ele
  sumia por arredondamento em algumas estaturas (1,64 e 1,68 m).
- O cabelo preso ganha uma mecha em cada têmpora (`hair_side_l`, `hair_side_r`, `MECHA`). A casca sozinha acaba
  numa linha reta acima da testa (o gorro) e, por ser um elipsoide, não desce pelos lados sem cobrir a testa. Com
  as mechas a testa fica entre o cabelo. O lenço as cobre.
- Os testes novos medem na câmera do jogo, não na elevação: a fileira mais larga da face igual à do crânio, o
  nariz descendo abaixo do olho no perfil, o nariz com pixel de perfil de 1,20 a 1,96 m e a testa com cabelo dos
  dois lados. Os controles: a face de 0,62, o nariz a 42 %, o nariz rente à face e o cabelo sem as mechas.
- O que mudou de visibilidade: de perfil a mecha de lá fica escondida, e o queixo passa a aparecer. Olho e chapéu
  não mudaram.
- O que sobra: a ponta do perfil fica a 0,32 da cabeça, perto do piso da faixa (0,30); abaixo de 1,50 m e em
  algumas estaturas acima (1,64 e 1,74 m, entre as medidas) o nariz ainda acaba na fileira do olho, por
  arredondamento; no corpo de 1,68 m e 105 % de largura o pescoço mede 0,059 (a faixa começa em 0,060), e já
  media antes desta mudança.

## O humano: a abertura das pernas (pedido do dono, 2026-11-25)

O dono pediu a análise do quadril, das pernas e dos pés, e escolheu começar pela abertura.

- O tornozelo fica sob a junta do quadril (`TORNOZELO_X` 0,050 da estatura; eram 0,080). A perna desce reta. Antes
  os tornozelos ficavam a 26 cm um do outro, com as juntas do quadril a 17 cm: de frente as canelas passavam da
  largura do tronco (os pés a 8,6 px um do outro, no corpo de 1,65 m), e de perfil a câmera a 45° punha o pé de
  lá 5,2 px acima do de cá, no meio da canela. Agora são 5,4 px e 3,2 px. O andar usa a mesma abertura e muda
  junto.
- A medida nova `pes_sobre_o_quadril` (a distância entre os tornozelos sobre a das juntas do quadril, de 0,6 a
  1,15) entra na radiografia: dava 1,56 e dá 1,0. O teste na câmera do jogo confere os pés de frente e de perfil;
  o controle é a abertura do antigo, que o oráculo repõe (`abertura_do_antigo`). Os esperados não foram regerados
  (I11).
- O que mudou de visibilidade (corpo nu, calça presa, calça solta e saia curta): de costas as pontas dos pés ficam
  atrás dos calcanhares e somem. Nada mais.
- O resto da análise ficou para depois, na ordem em que pesa: a esfera saliente no joelho e no tornozelo (0,075
  contra 0,057 da canela; 0,048 contra 0,039); a canela em cone, sem panturrilha (0,053 a 30 %, contra ~0,07); o
  pé alto (0,066, contra ~0,045) e apontando reto; a cintura fina para o quadril (0,145 e 0,197); a barra da calça
  solta e o fundo da saia, que fecham arredondados. As referências do corpo real são de memória, não conferidas
  em fonte.

## O humano: a cabeça é um ovo (decisão do dono, 2026-11-25)

O dono mudou o critério: o humano é uma figura para a câmera de cima, pixelada, e não precisa da forma real. A
cabeça pode ser só um ovo. O crânio real dificulta a IA prever o pixel, e o detalhe (o nariz) nem se vê no jogo.
A regra entrou em `docs/regras.md`.

- A cabeça é uma parte só (`skull`), um elipsoide (`CRANIO`): 0,70 da cabeça de largura, 0,76 de fundo e 1,0 de
  altura (mais alto que fundo, para de perfil não ler deitado). A face, o queixo e o nariz das mudanças 12 e 13
  saíram, com os testes deles (a largura da face, o nariz sob o olho e por estatura).
- O olho fica a 0,38 da cabeça no osso dela (`OLHO_Z`; 63 % da altura): na tela cai entre 56 % e 69 % do ovo, de
  cima para baixo (um pouco abaixo do meio), de 1,20 a 1,96 m. Perde também o contorno de fora (`no_outline`): de perfil, por ser uma peça fina, o contorno dele
  saía da borda da cabeça, como um ressalto. Encostar o olho por dentro da superfície foi medido e não veio: não
  mudava o perfil e escondia o olho sob a aba.
- O cabelo, as mechas, o coque e o lenço foram reafinados sobre o ovo (`CABELO`, `MECHA`, `COQUE`, `LENCO`).
- O chapéu assenta um pouco para trás (`CHAPEU`): centrado no ovo, na câmera de cima a aba cobre os olhos em
  qualquer largura acima de ~110 %. Assim os olhos aparecem de frente até ~150 % de aba (1,72 m) e em alguma vista
  até ~200 %; de ~210 % em diante a aba os cobre em todas (medido em 1,60, 1,72 e 1,85 m). O catálogo diz isso.
- A régua: `olhos_na_cabeca` aceita até 0,70 (a figura para a câmera de cima põe o olho acima do real). As outras
  medidas da cabeça seguem na faixa. A cabeça do antigo continua saindo dela nas quatro.
- Os testes: a cabeça é uma parte só e oval na tela, de frente e de perfil (o controle é a cabeça de três massas
  do antigo); o olho não sai da borda de perfil (o controle é o olho com contorno: 24 px, somando as estaturas).
  O oráculo repõe a cabeça do antigo inteira (as três massas, as regras, os olhos, o cabelo e o chapéu no crânio
  dele). Os esperados não foram regerados (I11).
- O que sobra: o alto do ovo sai com 1 px de ponta em algumas estaturas e vistas (o polo do elipsoide na grade).

## O humano: os membros em formas simples (decisão do dono, 2026-11-25)

O dono pediu o resto do corpo pela regra da cabeça em ovo: formas simples, para a câmera de cima.

- A esfera de cada junta tem o raio do membro (`R_JUNTAS`; o cotovelo tinha 1,15, o joelho e o tornozelo 1,1), e o
  antebraço e a canela começam com o raio da junta (`DEPOIS_DA_JUNTA`): não há mais a bola no meio do membro. No
  boneco de madeira as esferas do cotovelo e do joelho deixam de aparecer; o catálogo diz.
- A perna é um tubo que afina pouco: a coxa 0,045 e o tornozelo 0,025 da estatura de raio (eram 0,047 e 0,021: a
  canela virava um palito de 2 px).
- O pé tem 0,12 da estatura (`PE`; o real, 0,152) e é mais baixo (`PE_ALTO`): comprido, de frente apontava para
  baixo como um bloco maior que a mão, e de perfil lia como sapato de palhaço. O calçado segue o pé.
- A mão é uma forma curta da largura do punho (`MAO_FORMA`): era um elipsoide de 0,6 do punho de largura, um risco
  de 1 px na tela. A mão do raio do punho vezes 1,15 foi medida e não veio: lia como luva.
- Cada membro sombreia como uma massa só (`MASSA_DO_MEMBRO`), como o tronco.
- A régua ganha quatro medidas de leitura (`juntas_sobre_os_membros`, `tornozelo_sobre_a_coxa`,
  `pe_sobre_a_estatura`, `mao_sobre_o_punho`); os membros do antigo saem da faixa nas quatro. O oráculo os repõe
  (`membros_do_antigo`): as formas viraram constantes do kit antes de mudar de valor, com os pixels conferidos
  iguais. Os esperados não foram regerados (I11).
- O que mudou de visibilidade (seis composições): as esferas do cotovelo e do joelho somem em todas as vistas; de
  costas, com a saia, as mãos (mais curtas) ficam atrás do quadril.

## O humano: o tronco é um bloco, com o quadril (decisão do dono, 2026-11-25)

A mesma regra das formas simples, no tronco.

- O quadril (`pelvis_block`) é do tronco: o mesmo grupo de contorno e a mesma massa de sombra (`QUADRIL`). À parte,
  a linha em volta dele lia como sunga no corpo nu (9 px de linha entre a cintura e o quadril, de frente; agora 0).
- A cintura e o quadril têm quase a largura do peito (`CINTURA_X` 0,082 e `QUADRIL_LARG_X` 0,088; eram 0,075 e
  0,095, as do corpo real): o tronco afinava e abria como uma ampulheta. `cintura_sobre_o_peito` foi de 0,81 a
  0,85. O corpo não tem argumento de sexo: a forma é a mesma para todos, e a roupa (a saia, a faixa) é que marca.
- A jaqueta e a faixa seguem a cintura e ficam ~0,4 px mais largas. Com os dois lados da cunha do peito mais
  afastados, abriu-se um sulco no meio dela, e a sombra da cabeça caía dentro (um risco nas costas da jaqueta): a
  cunha ganhou um fuso no meio.
- O teste do tronco numa massa cobre o quadril; o controle é o tronco do antigo, que o oráculo repõe com as três
  constantes. Os esperados não foram regerados (I11).
- O catálogo dizia que as juntas do punho apareciam: as que aparecem são as do ombro e do quadril (medido).
- A mão cresce um pouco (a meia altura de 0,34 para 0,38 do comprimento dela): com 0,34, de costas ela sumia
  atrás do quadril no corpo vestido.

## A sombra no chão é só a projetada (decisão do dono, 2026-11-25)

A mancha redonda e cheia embaixo do asset (a sombra de contato) saiu: a sombra no chão é a que o asset projeta pela
luz, em xadrez, que já nasce no pé (o ponto no chão se lança sobre si mesmo). Prancha: `18_so_a_sombra_projetada`.

- A composição não tem mais o campo `sombra`; pedir é recusa (`DOC_INVALIDO` em `/sombra`) com a dica. O corpo do
  humano e o do canino não desenham mais a elipse; a vista não troca mais a geometria de uma parte (só a sombra
  girada usava). Ficam sem objeto as decisões da sombra de contato reescalada nas vistas e da pegada do quadrúpede.
- A sombra no chão sai do material `sombra` do estilo, em todo asset (antes só quem tinha a de contato a ganhava;
  o estilo sem o material não pinta chão).
- O tronco (a revolução) se lança como o tubo do eixo, e o cacho pontilhado como a almofada redonda que desenha (no
  chão, com a profundidade da largura): o cacho é um plano virado para a câmera, a luz o pega de lado, e a sombra
  dele era uma linha. Sem isso, a árvore ficava sem sombra nenhuma. O canvas mede as duas.
- A limpeza de cor isolada trata a sombra no chão como vazio: o pixel da borda de baixo da figura não fica "dentro da
  massa" por causa do chão (a de contato fazia o antigo limpar pixels da borda).
- A composição guardada no acervo com a `sombra` não se lê mais e conta como outro desenho: o build da mesma revisão
  é recusado (`IDENTIDADE`) e `pfe atualizar` faz a seguinte sem ela.
- O oráculo roda o antigo sem a sombra de contato (`oraculo_antigo.py` tira as partes) e compara o quadro sem a sombra
  no chão (`sem_chao_sha256`): a do antigo só existia com a de contato. Os esperados foram regerados.
- O teste (`tests/test_sombra.py`): no banco, na árvore, no humano e no canino a sombra no chão está toda na fase do
  xadrez e encosta na base do asset; o controle pinta a elipse do jeito antigo e é acusado.

## A flora em volumes (pedido do dono, 2026-11-25)

O dono pediu a análise do modelo de árvore e de vegetação e a refatoração dele. Pranchas: `19`, `19b` e `19c`.

- O que a análise mediu no modelo antigo (a árvore de exemplo; o carvalho da prova entre parênteses): a copa era
  um desenho em elevação, discos pontilhados no plano da frente. Na câmera de cima saía com 0,44 da largura em
  altura, quando o volume pedido dá 0,74; enchia 57 % (73 %) da elipse dela, em 24 (45) pedaços soltos; 11 % (10 %)
  dos pixels eram pontos isolados; a sombra no chão era uma tira de 112 × 13 px; a árvore tinha 102 (190) partes.
  A conífera e os galhos eram polígonos chapados: de lado para a luz, a conífera lançava uma linha pontilhada e os
  galhos, nada. Toda peça de flora só desenhava a vista S. O tom de cada cacho era sorteado pela posição, não
  tirado da luz.
- A copa é feita de volumes, pela regra das formas simples para a câmera de cima. A peça `copa` (a folhosa) põe
  tufos elipsoides em quatro anéis em volta do centro, mais um miolo escuro. O tufo de tamanho `f` fica a `1 − f`
  do centro, na direção dele: encosta por dentro no elipsoide da copa, e a altura e a largura do asset são as
  pedidas. Cada tufo é sombreado como um volume, e todos ficam no grupo de contorno do nó. No chão e sem tronco,
  a copa é a moita; com `pende`, os tufos de baixo afinam e descem (o ramo que cai).
- A peça `copa_conica` (a conífera) empilha saias cônicas, sólidos de revolução, cada uma no seu grupo de
  contorno: a linha e a sombra sob a saia separam os andares.
- A peça `galhos` põe galhos roliços em volta do tronco, um a cada fatia da volta, e deixa as pontas em (x, y, z)
  para a copa pôr um tufo em cada uma (o argumento `pontas`). A copa cobre quase todos; sozinhos, são a árvore
  seca. O galho fica no osso da altura de onde sai (abaixo da cadeia do balanço, no tronco).
- O primeiro galho cai onde a `fase` manda, em fatias da volta a partir da frente (0,5: a frente livre). A fase
  era sorteada, e no carvalho um galho saiu para a câmera: descia na tela por cima do tronco, como uma escora.
  O teste conta as pontas a menos de 20° da frente (0); o controle é a fase 0 (1).
- Os materiais `copa_folhosa`, `copa_folha` e `copa_agulha` têm rampa de 4 tons e a textura de traços curtos,
  que quebra a fronteira entre os tons (a folha). Os materiais chapados de folha ficam no estilo.
- As quatro peças de flora desenham as 4 vistas (o `tronco_em_pe` também: o pixel dele na S não mudou).
- O jeito antigo não existe mais: saíram as peças `pontilhado`, `galhos_em_pena`, `cortinas`, `galhos_grossos` e
  `galhos_finos` (a recusa `PECA` diz a que ficou no lugar), o módulo da folhagem e, do núcleo, o pontilhado e o
  polígono plano (a geometria da IR, a projeção, o raster, a sombra e o canvas deles) e o viés de profundidade
  que a peça do prop punha por vista. O kit tem 35 peças.
- O oráculo: os 15 casos das cinco peças saíram do `kit.esperado.json`, e a árvore (o repouso e o balanço), do
  `composicoes.esperado.json`. Os esperados não foram regerados (I11). A fixture da árvore foi para
  `tests/fixtures/composicoes/`, no modelo novo. As peças novas não têm oráculo.
- Os testes (`tests/test_flora.py`) medem na câmera do jogo: a copa numa massa só (1 pedaço, 95 % da elipse),
  com a altura de 0,73 da largura, cobrindo o tronco, com a sombra de 0,48 da largura em altura e 20 partes (os
  pontos isolados caíram a 0,3 % dos pixels da copa); a sombra da conífera; os galhos em volta; as 4 vistas; o
  balanço. O controle é a copa do jeito antigo, sintética (discos chapados no plano da frente): 5 pedaços, 54 %,
  0,49 e 0,11. A IR recusa as duas geometrias.
- O que mudou de visibilidade: o tronco aparece só embaixo da copa (20 px no exemplo), e os galhos somem sob ela.
  A skill dá a conta do que sobra do tronco na tela. A sombra da copa entra no canvas (o exemplo foi de 158 × 84
  para 157 × 130).
- O carvalho da prova foi refeito no modelo novo (`carvalho_roble.r3.3c42542d9f2a`, export verificado, 37 partes
  contra 190). Os braços saem a 90 cm e sobem rentes ao tronco para dentro da copa: leem como o tronco que se
  abre no alto (149 px), não como braços à mostra. O braço baixo e aberto da ficha foi medido e não veio: sob a
  copa, na câmera de cima, ele sai como uma vara fina para fora dela ou desce na tela como escora.
- O que sobra: a borda do tufo e a da saia são lisas (a copa lê como massa, não como folha solta, e a conífera
  perdeu a silhueta em pontas); a copa pendente é um domo com ramos caindo, não os fios de antes; a sombra no
  chão do elipsoide segue a aproximação de antes (a elipse com metade da altura dele na tela), e com `pende` ela
  sai com furos; a linha reta de pasto continua sem peça. A versão do motor não subiu (o id do build leva os
  pixels), mas a composição que usa as peças que saíram não se lê mais.

## O tronco com forma de tronco (pedido do dono, 2026-11-25)

O dono pediu variações de tronco, para ele não ser simples e só cilíndrico. Pranchas: `20` e `20b`.

- O tronco era um cone: 21 estações de raio linear, com a inclinação e uma casca lisa. Na tela, um retângulo.
- O `tronco_em_pe` ganhou cinco argumentos. `pe` (0,35 por padrão): o pé abre no chão além da `base` e some à
  altura de uma largura do tronco, com estações a mais onde ele abre. `irregular` (0,12): o fuste engrossa e afina
  em duas ondas ao longo da altura, nulas na base e no topo (as duas larguras são as pedidas). `curva`: o eixo
  ondula em S e volta ao prumo no alto (a copa segue sobre o pé). `raizes`: raízes roliças em volta do pé, a
  primeira para a frente. `nos`: calombos na casca, do lado da câmera. Tudo no grupo de contorno do tronco.
- A textura do material ganhou o `grain`: no sólido de revolução, os sulcos deitados em volta dele (`across`, o
  que havia) ou em pé (`along`, o veio da casca). Vieram dois materiais: `casca_sulcada` (o veio em pé) e
  `casca_anelada` (clara, com os anéis deitados). As cascas lisas ficam.
- O oráculo: o tronco liso (`pe` e `irregular` em zero) é o cone do `pixel-engine` e segue igual a ele pixel a
  pixel nas três variações que a peça tinha (`VARIACOES_DO_ANTIGO`, em `scripts/oraculo.py`). O `--kit` foi
  rodado de novo e deu os mesmos 90 esperados (o estilo vai ao antigo sem o `grain`); o arquivo não mudou.
- Os testes (`tests/test_flora.py`), no cilindro de 60 cm, com o tronco liso como controle: o pé tem 1,29 da
  largura do fuste (o liso, 1,0); o fuste varia 6 px com `irregular` 0,2 (o liso, 0); com `curva` de 15 cm o eixo
  vai 5 px para cada lado e o alto fica sobre o pé; as raízes e os nós têm pixels à mostra e a figura passa 22 px
  da largura do tronco; a casca sulcada tem 79 pares de sulco em pé contra 11 deitados, e a anelada 20 contra 2.
- O que mudou de visibilidade: nada some; o pé da árvore de exemplo fica 2 px mais largo de cada lado.
- O que sobra: o `irregular` só se lê em tronco de 40 cm ou mais (abaixo disso a variação é menor que 1 px); a
  curva e a inclinação são só em x (de lado, na vista S); as raízes são retas; o lado da sombra não mostra o
  veio (a rampa não tem tom abaixo); não há forquilha nem toco cortado (a tampa leva o material da casca).
- O carvalho do acervo foi refeito com o tronco novo (`carvalho_roble.r4.89fc47c82e08`, export verificado): o
  fuste de 63 cm com o pé de 0,5 (os 95 cm da ficha no chão), 5 raízes, um nó e a casca sulcada. Na `20b`, a
  `r3` em cima e a `r4` embaixo. O build da `r3` é do tronco antigo e segue valendo para ele.

## O remoto (pedido do dono, 2026-11-23)

- O GitHub `gabrielAlencar33564/pixel-engine` passa a ser esta engine: a `main` de lá foi substituída pelo histórico
  daqui (force push com lease em 4a23b14), e o histórico antigo saiu dela por pedido do dono. O antigo fica no clone
  local `pixel-engine` (com os 81 commits que nunca subiram) e na branch `manequim` do GitHub, que não foi tocada. O
  oráculo segue lendo o clone local; o push daquele clone para a `main` sobrescreveria esta.

## O golpe de espada (pedido do jogo Aldeia da Orla, 2026-11-25)

- O humano ganhou a peça `espada` (na mão direita: a lâmina para a frente e 35° para baixo, a guarda e o cabo) e o
  clipe `attack` (a receita `golpe`: 480 ms, 8 quadros juntos no corte, sem laço, a marca `hit` aos 200 ms). A
  receita é do tipo `parado` (os pés plantados por IK); o `parado` passou a ler as curvas por chaves sobre o ciclo e o
  `laco` da receita. Quem tem a espada ganha 16 px em cima e de cada lado no canvas: a lâmina no alto do golpe saía
  do quadro. Nada muda no pixel de quem não tem a espada (o oráculo segue igual). A lâmina clara usa `casca_clara`
  (a rampa ardósia, pedra clara e osso), para não mudar o estilo: o `metal` lia como um risco escuro.

## O penedo (pedido do dono, 2026-11-25)

- A pedra solta ganhou a peça `penedo`: as pedras do jogo eram elipsoides e liam como ovos. É o fecho convexo de
  anéis de pontos sorteados pela semente (base, cintura, ombro e um topo chato que fecha em ponta com `agudo`), com
  as faces quase no mesmo plano (13°) fundidas numa só. Só as faces de frente para a câmera S se desenham (as do
  convexo não se cobrem) e só as que têm 3 px² ou mais na tela; o tom vem da luz pela normal na família do material
  (`alvenaria` ou `palha`), um degrau abaixo nas de costas para a luz. O musgo vai nas faces mais deitadas, com o
  tom calculado na peça (o verde não tem família de degraus). O teste mede o ovo: a pedra cobre até 90 % do ovo
  inscrito na caixa dela, e o elipsoide, 93 % ou mais (o controle).

- O canvas do prop conta o raio do traço roliço no que ele passa da margem (o tronco grosso deitado, de 18 cm de
  raio, saía cortado: o canvas contava só a meia espessura do traço fino). O que já cabia na margem fica igual (o
  oráculo não muda); o controle em tests/test_canvas_rolico.py recusa o tronco do jeito antigo.

## A flora variada e a crítica (pedido do dono, 2026-11-25)

O dono pediu a correção do motor da flora, construções variadas (sem um padrão só) e um jeito de os agentes
revisarem o que entregam. Pranchas: `21`, `21b` e `21c`.

- O que a análise achou nas 37 plantas que os agentes fizeram no acervo: toda folhosa era `tronco_em_pe` + `copa` e
  toda conífera, `tronco_em_pe` + `copa_conica`. A `copa` punha os tufos em 4 anéis fixos, cada um com a luz de uma
  bola (lia como brócolis; a pendente, como pinha); a saia da conífera era torneada (lia como funil); a flora baixa
  era improvisada com `fios`, `traco` e `elipsoide` (a flor lia como dente). Nada media a entrega nem a comparava
  com as outras plantas do cenário.
- A `copa` põe os lóbulos numa espiral em volta do eixo (o passo é o ângulo áureo, o giro é da semente), cada um
  com o tamanho, o lugar e o recuo sorteados, e raminhos na borda. Tudo fica por dentro do elipsoide da copa, e o
  raminho do alto encosta nele (a altura é a pedida). `tufos` passou a ser o total de lóbulos (era o do anel do
  meio). `perfil` faz a gota (1) e o guarda-sol (−1); `pende` faz a cortina: três ramos finos por lóbulo em volta
  da copa, de dentro da folhagem até `pende` meias alturas abaixo do meio dela, sem contorno (os tufos não esticam
  mais). A peça deixa a âncora `superficie` (os pontos de face que nenhum outro volume cobre).
- A folhagem de um nó é uma massa de luz: a parte com a marca `massa_<nó>` toma 45 % da luz da união das partes da
  marca (com 0,18 de penumbra) e 55 % da luz dela (`raster/tons.py`, `raster/volume.py`). Vale entre grupos de
  contorno: na conífera cada saia tem a linha dela e a árvore inteira tem um lado claro.
- A `copa_aberta` põe uma copa pequena e chata em cada ponta de uma âncora; os `galhos` ganharam `sobe` (saem
  escalonados do tronco: o de baixo vai mais longe). É a construção de galhos à mostra.
- A `copa_conica` faz cada andar como um leque pregueado (uma parte por saia): as pontas caem abaixo da barra e a
  saia entra entre elas (`pontas`, `recorte`, `cai`). O argumento `saia` saiu. Na dobra do leque o z-buffer fica
  com o triângulo da frente (o de mais de meio passo à frente); o plano que se repete não troca, e o oráculo não muda.
- A `touceira` (lâminas em arco a partir de um pé: finas; com `largura`, roliças; com `pena`, serrilhadas dos dois
  lados da nervura) e o `salpico` (pontos de cor numa âncora; na composição de vista única, só na metade mais
  virada para a câmera) fazem a flora baixa, a palma, a flor e o fruto.
- A crítica (`pfe critica`, `quality/flora.py`, `application/critica.py`): mede no quadro da vista S a solidez da
  folhagem (os pixels dela sobre os do fecho convexo), a simetria (contra o espelho), a luz (o claro do lado da
  luz), o lenho à mostra, as ilhas e a assinatura (a silhueta na grade de 32, do pé para cima), e compara a
  assinatura com a das outras plantas do acervo da mesma categoria. O papel de cada parte vem da peça (`Peca.flora`)
  ou, na peça genérica, do material. Os limites: lisa 0,985, espelhada 0,95, sem direção 0,05, parecida 0,88; nas
  copas do kit as medidas dão 0,92 a 0,97, 0,77 a 0,92, 0,17 a 0,37, e entre sementes da mesma árvore 0,66 a 0,84.
- O pacote da planta só sai com a crítica que passa neste build: sem defeito medido e com o parecer de quem revisou
  (as seis perguntas, cada uma com nota). O registro fica em `criticas/` do acervo. Vale só para a planta (a
  categoria de árvore ou arbusto, ou uma peça de folhagem); a crítica não aprova a arte, que segue com o dono.
- A prévia já devolve as medidas e os achados (sem as irmãs), e as `escondidas` não listam os volumes de uma massa.
- O que a medida não vê: o brócolis. As bolas soltas com a luz de cada uma dão a mesma medida de luz da massa (o
  conjunto ainda clareia para o alto); isso fica na pergunta `massa_de_luz`, e no motor o jeito não existe mais.
- Os testes (`tests/test_flora.py`, `test_ervas.py`, `test_critica.py`), com o jeito de antes como controle: a
  nuvem do lado da luz tem 1,23 da luminância da do lado da sombra (1,04 com cada tufo sombreado sozinho); a
  conífera enche 0,72 do fecho dela (a saia lisa, 0,90); os galhos aparecem 123 px sob a copa aberta; o ovo, a copa
  em anel e o polígono são acusados; a mesma árvore em outro tamanho é acusada como irmã (a de outra construção,
  não); o export da planta é recusado sem o parecer.
- A prova de fora (um agente sem contexto, dez plantas de uma cena pela skill, em `~/.pixel-forge/acervo-prova-flora`;
  na `21c`): as dez saíram de construções diferentes e sem defeito medido, em 65 chamadas. O que ela achou e foi
  corrigido na causa: o canvas cortava a copa alta e estreita (a sombra do elipsoide no chão tem metade da altura
  dele na tela, e o canvas a contava só até o fundo: `ALTURA_NA_SOMBRA`); os lóbulos paravam no meio da metade de
  baixo da copa (`BAIXO` foi de −0,45 a −0,8: o choupo lia como pirulito); os ramos do chorão eram presas grossas
  (viraram a cortina); a samambaia lia como aranha (a folha em pena); a dica da folhagem lisa mandava usar a peça
  que já se usava. A skill ganhou o que faltava (o tronco até o centro da copa, o `pende`, a flor na lâmina reta,
  a erva em `objeto`, o que a crítica compara).
- A revisão de fora (outro agente, só com as pranchas da crítica e as fichas): passou 2 das 10 plantas e mandou
  corrigir 8; os pareceres estão registrados. O defeito que mais se repetiu era do motor: a folhagem era sempre um
  volume liso e arredondado com contorno (lia como brócolis, pedra, picolé). O que foi corrigido na causa:
  - a beira de cada volume de folhagem sai recortada (a marca `borda_de_folha`, em `raster/montagem.py`: da faixa de
    2 px da borda saem 42 % das células de 2 px, contadas do canto da máscara), e o miolo escuro aparece nos vãos;
  - a massa de luz é do grupo de contorno, não do nó (as bolas da moita de vários nós tinham cada uma a sua luz);
  - a `copa` ganhou o `desvio` (sai do eixo: a moita de duas massas, a copa de um lado só);
  - os ramos que caem saem de dentro dos lóbulos de baixo e param a alturas desiguais, sem chegar ao chão (eram
    barras iguais até o chão, e duas despontavam por cima da copa);
  - a lâmina fina deixou de ser detalhe e lança a sombra dela (as ervas flutuavam); a pena tem um dente a cada
    2,5 px (a de 1,5 px virava mancha chapada); o `salpico` ganhou o `alonga` (a espiga em pé).
- A segunda rodada da revisão (outro agente, com a régua do jogador que a skill passou a dizer): passou 4 das 10 e
  mandou corrigir 6. O defeito que mais se repetiu: o que é linear e orgânico saía como barra reta. Corrigido na
  causa: a raiz à mostra deita em curva, grossa junto do tronco (era uma lâmina reta: a mudança 20 lia como pião
  com aletas); a cortina tem cinco ramos por lóbulo dos dois terços de baixo, cada um um pouco fora do prumo; a
  folha em pena tem o corpo roliço e as penas passando dele (o zigue-zague sozinho lia como rabisco); o claro das
  lâminas fica do lado da luz da vista S (era sorteado, e caía contra a luz); o lóbulo recua no máximo 0,28 (o
  que recuava mais abria a copa e mostrava o miolo chapado).
- A terceira rodada (outro agente) passou 7 das 10: o carvalho, o abeto, o pinheiro torto, o chorão, a roseira, a
  tabua e o capim florido saíram em pacote, exportados e verificados (prévia, arte pendente). Três ficaram em
  `corrigir`, e o export delas é recusado: a samambaia (com poucas folhas largas, o claro pelo lado parte a planta
  em duas manchas, e a folha em pena de 15 a 25 px não se lê uma a uma: pede outro desenho da fronde pequena), o
  arbusto baixo e claro (a `copa` baixa e larga lê como almofada lisa com o claro no meio) e o choupo (a casca
  clara é lisa e lê como cano; a sombra da copa alta sai em duas manchas). A ficha da roseira e a do arbusto não
  foram reescritas quando a construção mudou: o revisor foi avisado.
- As três que ficaram (pedido do dono, 2026-11-25), cada defeito corrigido na causa:
  - a samambaia: a folha em pena passou a ser o corpo roliço com a beira serrilhada dente a dente (a marca
    `borda_serrilhada`) e a nervura no tom escuro por cima (o zigue-zague saiu); a roseta de folhas largas deixa a
    frente livre (a folha de frente para a câmera virava um talo em pé) e abre por igual; o corpo nunca é do tom
    escuro, e o lado da luz pesa 0,45 no tom (com 0,6, poucas folhas largas viravam duas manchas);
  - a moita pequena: a beira em folhas vai na medida da peça (a máscara de menos de 150 px tem a folha de 1 px; a
    de 2 px comia o lóbulo pequeno), e a luz do relevo sobe 14 % (`GANHO`): o alto de cada lóbulo do lado da luz
    chega ao tom mais claro da rampa (a massa ficava em dois tons, com o claro liso no meio);
  - o choupo: o estilo ganhou a `casca_cinzenta`, com o veio da sulcada na rampa cinzenta (a clara é lisa e, no
    tronco fino, lia como cano). Mudar o estilo muda o id de todo build que se refizer.
  A quarta revisão passou o choupo e devolveu as outras duas com uma pergunta cada: a luz da massa passou a vir
  mais de lado que a de uma bola (`LUZ_DA_MASSA`: na moita de vários tufos o mesmo brilho se repetia em cada um), e
  a roseta de folhas largas ganhou o miolo escuro no pé (o centro era a parte mais clara). A quinta passou a
  samambaia e devolveu o arbusto pela silhueta (os três tufos faziam um V fundo no meio: era da composição, e os
  tufos mudaram de lugar); a sexta passou o arbusto. As dez plantas da prova têm pacote exportado e verificado; os
  sete das primeiras rodadas são de builds do motor de então, e refeitos agora dão outro desenho e pedem a crítica
  de novo.
- A ligação (pedido do dono: nada flutuando, o galho parte de um nó): o `tronco_em_pe` deixa o eixo dele (o x, a
  altura e o raio em cada estação); os `galhos` nascem do eixo do tronco declarado antes, onde ele passa nessa
  altura (antes saíam do prumo, e no tronco inclinado nasciam fora dele), e são recusados sem tronco, acima do alto
  dele ou mais grossos que ele ali. `design/ligacao.py` confere na geometria do mundo, antes de desenhar, que todo nó
  de planta toca o chão, uma peça que não é de planta ou outro nó já ligado (recusa `LIGACAO`, com o vão e a dica):
  a copa acima de um tronco curto passava, coberta pela frente. A copa que chega ao chão assenta o miolo nele (os
  lóbulos recuam da borda, e a moita ficava a 3 a 6 px do chão). Os galhos não ganharam argumento (já têm os 12 do
  teto): a ligação é com o tronco de antes.
- O hábito (pedido do dono: os princípios da forma das plantas, com menos argumentos): o campo `planta` da composição
  descreve a planta pelos traços (o hábito, a altura, a largura, a folha, a idade e, se a espécie foge do hábito, o
  fuste, a esbeltez e o vento), e `design/habito.py` deriva os nós. São traços gerais, não espécies: a esbeltez dá
  a grossura do tronco, o fuste diz onde a copa começa, o lóbulo tem o tamanho da folhagem (de 5 a 12 pela largura
  da copa na tela), o galho tem de metade a três quartos do tronco onde sai o mais alto, o tronco entra na copa. A
  composição pelos traços tem um quarto ou menos do tamanho da escrita peça por peça, e a prévia devolve os nós
  derivados. O campo novo não entra no id do build de quem não o usa.
- A medição de fora (um agente sem contexto, os mesmos dez pedidos da primeira prova, só pela skill, em
  `~/.pixel-forge/acervo-prova-habito`): 153 mil tokens contra 188 mil, 69 chamadas de ferramenta contra 86, 54 de
  `pfe` contra 65 (22 prévias contra 32) e 9,9 min contra 12,2. Só 4 das 10 plantas saíram pelos traços; o que a
  medição achou foi corrigido na causa: a conífera derivada caía em `LUZ_SEM_DIRECAO` (a medida vai de 0,03 a 0,19
  na conífera: o limite desceu a 0,02); no hábito aberto as nuvens se fundiam e a copa não ia com o tronco inclinado (as pontas dos galhos
  abrem em volta do alto do tronco; a nuvem tem 0,15 da largura; o vento desvia 18 % da altura); a moita alta
  saía em dois ovos (o número de massas vem da largura sobre a altura, e as massas se sobrepõem); o fuste não
  dizia onde a folhagem começa (o elipsoide desce até o fundo dos lóbulos cair nele); e as plantas de lâmina não
  tinham hábito (a `touceira`). O miolo da copa desceu de 0,6 a 0,5 da copa, e a copa alta e estreita conta os
  lóbulos pela altura (o miolo chapado aparecia em 16 % da copa do decurrente e em 34 % da do excurrente estreito;
  ficou em 6 % e 17 %).
- A segunda medição (as mesmas dez plantas, outro agente sem contexto, em `~/.pixel-forge/acervo-prova-habito2`):
  154 mil tokens, 52 chamadas de ferramenta, 46 de `pfe` (24 prévias), 7,7 min, 8 das 10 pelos traços, nenhum
  achado da crítica e nenhum `pfe atualizar`. Os tokens não desceram da primeira para a segunda medição; as
  chamadas e o tempo, sim. As plantas derivadas não passaram por revisor de fora. O que ela achou e foi corrigido:
  a touceira sem `folha` saía samambaia (sem ela é a lâmina fina); o padrão do fuste por hábito não estava na
  skill; o miolo da copa entrava nas `escondidas`; a recusa `TRACO_SEM_SILHUETA` não dizia quais partes tocam a
  borda. Fica aberto: o chorão e o capim florido ainda saíram nó por nó (não há traço para alongar a cortina; a
  flor pede a lâmina quase reta), a altura medida difere em até 5 % da pedida, a `casca_cinzenta` lê como cano
  azulado, o `vento` mal se lê nas nuvens do hábito aberto e os frutos do `salpico` caem no contorno.
- A ligação é da estrutura, não do pixel (correção do dono: "o capim estava correto, as lâminas são separadas
  porque isso é da genética delas"; o pedido era para a árvore de galho sem ligação e de folhagem solta do galho).
  Saiu o que juntava pixel: o recorte da beira da folhagem já não guarda só o que toca o miolo da máscara (a folha
  solta na beira é da planta), e a crítica não tem mais o aviso `PEDACO_SOLTO`. A recusa `LIGACAO` fica como é: a
  geometria do tronco, do galho e da folhagem no mundo. A touceira derivada de lâmina fina nascia quase de um
  ponto (o raio do pé era 0,15 da largura, e o junco saía numa barra): o pé tem 0,3 da largura e a abertura leva
  as pontas até a largura pedida, como no capim composto à mão que o dono aprovou; o controle com o pé antigo
  acusa. Prancha: `~/.pixel-forge/acervo/pranchas/mudancas/22_laminas_separadas.png`.
- O que o agente lê (pedido do dono: gastar menos tokens): a skill e as regras estão em inglês (os identificadores
  ficam como estão: mudá-los quebra as composições do acervo); o catálogo tem dois níveis, o resumo e um arquivo por
  família (`pfe catalogo flora`: 19 mil caracteres no lugar dos 85 mil do kit inteiro), em JSON sem espaço a mais; a
  prévia e o catálogo dizem as partes numeradas em faixa (`copa_00..copa_29`).
- O que a segunda medição e o "que sobra" deixaram aberto (pedido do dono, 2026-11-25: um agente por frente, cada
  um no seu ramo, conferido e trazido para a `main`; nenhuma das pranchas passou ainda por revisor de fora):
  - **O chorão** (`design/habito.py`): o pendente tem os lóbulos miúdos (8 a mais que os da largura) e o `pende`
    sai do fuste; o ramo mais curto desce pela parte do fuste que a `cortina` pede (0,75 no pendente; traço novo,
    de 0 a 1, só da copa em massa: fora dela, recusa `PLANTA`). O de 5 m tem 70 ramos (eram 40) e o mais curto
    para a 0,38 do fuste (era 0,57). Com a cortina densa, o chorão pode receber o aviso `TRONCO_SUMIDO`.
  - **O capim de flor:** a lâmina fina derivada abre no máximo 0,35 e cai no máximo 0,08 (abria até 0,9 e caía
    0,12); na touceira baixa e larga a largura vem do pé, cada lâmina no seu. As pontas da frente, onde o
    `salpico` põe a flor, foram de 0,18 a 0,39 da altura na tela (40 × 70 cm).
  - **A altura:** no aberto, no seco e na touceira o alto era o da ponta sorteada na peça (de -22 % a +12 % do
    pedido). A engine monta o que derivou, mede o alto fora o tronco e acerta: fica abaixo de 2 % ou 1 px.
  - **O vento no aberto:** o vento só inclinava o tronco. Agora os galhos em volta encurtam até 50 % e um galho
    bifurcado a mais (`galhos_b`, com as nuvens em `copa_b`) sai a sotavento: com o vento em 1, o meio da
    folhagem fica de 0,09 a 0,19 da largura além do alto do tronco. Sem vento, os nós são os de antes.
  - **Os cinzentos** (`dados/estilo_base.json`): a `casca_cinzenta` usava a rampa da ardósia, da pedra e do metal
    (matiz de 235° a 249°) e lia como cano azulado. Os índices que o oráculo usa não mudam: entram `cinza_fundo`,
    `cinza_escuro`, `cinza` e `cinza_claro` (50 a 53: de (44,42,40) a (158,153,140), matiz de 30° a 43°) e os
    materiais `cinza`, `cinza_fundo` e `copa_cinzenta`. A casca cinzenta passa à rampa nova, com o sulco mais
    longo e fundo e a crista clara ao lado. A `casca_clara` e a `casca_anelada` seguem na rampa lilás (o oráculo
    usa a clara); a `copa_cinzenta` sozinha lê como pedra, e a planta pelos traços não escolhe a folha cinzenta.
  - **A agulha da copa aberta** (`pecas_copa.py`): com material de agulha, cada nuvem é um tufo de dois leques
    pregueados empilhados, de pontas finas (de 12 a 15 pontas na silhueta; a de folha tem de 2 a 7, e não muda).
    Lê como estrela espinhosa mais que como almofada de pinheiro, e na árvore velha as nuvens se fundem.
  - **A sombra da copa alta** (`raster/sombra.py`): o volume de folhagem se lança no chão exato, pela luz (era a
    elipse de cada volume na tela, curta: o choupo de 10 m saía em duas manchas). Os outros elipsoides seguem
    como no motor antigo (o personagem não muda), e o canvas perdeu a folga `ALTURA_NA_SOMBRA`. Mudam as sombras
    das árvores (os exemplos `arvore_folhosa` e `arvore_aberta`, a composição `arvore`).
  - **A irmã de outra categoria** (`application/critica.py`): a única da categoria no acervo ficava sem irmã. A
    planta se compara com as da mesma categoria e com as de outra no mesmo porte (a figura menor com pelo menos
    metade da altura da maior: `flora.MESMO_PORTE`). Nos acervos de prova a razão de altura vai de 0,11 a 0,36
    da árvore à flora baixa (com assinaturas de até 0,75: a moita redonda e a copa redonda) e de 0,52 a 0,88
    entre touceiras e entre árvores; o limite cai no vão. As irmãs saem com a categoria.
  - **As ervas** (`pecas_ervas.py`): o `salpico` escolhe os pontos da âncora pela normal na massa contra a
    câmera da vista que melhor os vê, e o ponto da face de um volume entra na folhagem (0,6 do raio mais os 2 px
    que o detalhe vence): de frente aparece, e na beira a folhagem o cobre. Nas variações do kit (6 sementes) os
    pontos no contorno foram de 90 para 16 na vista S e de 414 para 110 nas quatro vistas. O tom das lâminas é o
    do lado da luz na tela em cada vista: a IR ganhou o material da parte por vista (`ViewSpec.materials`; a
    vista S e as composições de vista única não mudam). A folha larga lisa é chapada (as faixas da peça lisa a
    faziam ler como tubo), com a nervura escura como a da pena. O capim de 20 a 40 cm (5 a 9 px de alto na tela)
    é limite da resolução: lê com poucas lâminas e `cai` 0, e nada mudou.
- A segunda rodada (as sobras que cada agente apontou em arquivo de outro; três agentes, conferidos e trazidos):
  - **A âncora `superficie`** (`pecas_copa.py`): cada volume da copa deixa, além do ponto para fora e para cima, o
    ponto de frente de cada vista declarada, os que nenhum outro volume contém. Na vista S, em seis sementes, os
    frutos da moita do kit aparecem 31 de 36 (eram 24, com 3 no contorno) e as flores 51 de 54 (eram 36, com 6),
    nenhum no contorno; na árvore, 60 de 60 (eram 50, com 10). Nas quatro vistas o contorno cai (moita de 36 para
    23, árvore de 83 para 57): o ponto de frente de uma vista fica de perfil nas laterais. Dois controles das
    ervas mudaram com ela (o do `MERGULHO` volta também a âncora de um ponto; o do lado de lá soma seis sementes).
  - **A cortina do chorão:** a ponta desce até 0,024 a 0,084 da altura de onde o ramo sai (era 0,07 a 0,25), com
    o raio de 0,035 da meia largura (0,7 px no mínimo) e a ponta a 0,3 dele: eram barras. Com 8 ramos por lóbulo
    lia melhor como véu, mas desfazia o controle do hábito; ficou em 5.
  - **A flor nas pontas** (`pecas_ervas.py`): o `salpico` nas pontas sorteia entre a metade mais alta na tela das
    vistas declaradas, cada flor a dois raios e 1 px das outras (as de outro salpico nas mesmas pontas também).
    Na vista S a flor foi de 0,27-0,53 a 0,68-0,78 da altura da touceira; nas quatro vistas fica em 0,5-0,7 (toda
    ponta abre para a câmera de alguma vista).
  - **A folha larga:** a roseta gira no meio do maior vão entre as câmeras declaradas, e nenhuma folha fica a
    menos de 0,2 fatia de uma câmera (só a S tinha a frente livre; a vista única S não muda). A nervura corre no
    eixo e vem à frente do corpo (`AssetBuilder.adianta`, o `depth_bias` da vista). A folha lisa não repete o tom
    da vizinha, e a de 5 px ou mais tem o contorno dela: a beira entre folhas do mesmo tom foi de 0,40 a
    0,11-0,21 na espada e de 0,57 a 0 na roseta de cinco folhas de 30 cm.
  - **A agulha, a folha cinzenta e as cascas alvas** (`estilo_base.json`, `habito.py`): a `copa_agulha` tinha a
    textura da folha larga e passou ao traço deitado de 3 a 6 px (a troca de tom na vertical foi de 1,04 e 0,95
    a 1,66 e 1,43 da horizontal, na conífera e no pinheiro aberto). A `copa_cinzenta` no cinza neutro lia como
    pedra: entram `cinza_verde_fundo` a `cinza_verde_claro` (54 a 57, matiz de 85° a 105°), a copa cinzenta
    passa a essa rampa e a planta pelos traços ganha `folha: cinzenta`. Entram a `casca_alva` (lisa) e a
    `casca_alva_anelada` (a bétula) na rampa neutra; a `casca_clara` (no oráculo) e a `casca_anelada` ficam.
- O que sobra: a casca clara e a anelada seguem lilases (as alvas são a escolha neutra); o traço da agulha é
  sempre deitado (a textura do volume não tem direção) e cruza a ponta caída do pinheiro; no chorão de 5 m os
  ramos têm 6 a 7 px no alto e a cortina é rala e reta; a nervura some na folha lisa escura; no capim pequeno
  oito flores não cabem afastadas; a roseta de poucas folhas muito largas lê como estrela; a nuvem de agulha
  lê como estrela espinhosa; a semelhança compara só a silhueta (duas
  plantas de silhuetas iguais e cores diferentes são acusadas). As composições antigas do acervo com `saia` não se
  leem mais, e as de `copa` dão outro desenho.
