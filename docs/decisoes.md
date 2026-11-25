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
  largura do tronco (os pés a 8,9 px um do outro), e de perfil a câmera a 45° punha o pé de lá 5,3 px acima do de
  cá, no meio da canela. Agora são 5,4 px e 3,2 px. O andar usa a mesma abertura e muda junto.
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

## O remoto (pedido do dono, 2026-11-23)

- O GitHub `gabrielAlencar33564/pixel-engine` passa a ser esta engine: a `main` de lá foi substituída pelo histórico
  daqui (force push com lease em 4a23b14), e o histórico antigo saiu dela por pedido do dono. O antigo fica no clone
  local `pixel-engine` (com os 81 commits que nunca subiram) e na branch `manequim` do GitHub, que não foi tocada. O
  oráculo segue lendo o clone local; o push daquele clone para a `main` sobrescreveria esta.
