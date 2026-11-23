# Plano da engine corrigida: o motor numa pasta nova, sem o treino

Data: 2026-11-23. Esta versão substitui as anteriores deste arquivo.

**Decisão do dono:**
- A correção não acontece neste repositório. A engine corrigida nasce numa pasta nova,
  **`D:\gabri\Projetos\Gabriel\pixel-asset-engine`**, com um repositório git novo, sem histórico.
- Este repositório (`pixel-engine`) fica como está: ele é a fonte de leitura e o oráculo de pixel, e ninguém escreve
  nele durante a correção.
- O dono não responde perguntas. **O Claude faz a correção sozinho, seguindo a lógica deste plano**, porque a engine é
  a ferramenta dele. Cada escolha que o plano não fixa é decidida pelas regras da seção 4 e registrada em uma linha.
  O dono olha o resultado no fim: o relatório, as pranchas e a prova de fora.

## 1. O objetivo da engine

- **A engine é a mão de uma IA para fazer pixel art.** A IA não gera imagem: ela descreve o asset em dados (forma,
  medidas, materiais, esqueleto, movimento), e a engine desenha, confere e exporta.
- **O que sai é o asset completo de jogo:** os quadros, as vistas, as animações quando houver, e o export com os
  metadados que o jogo lê (pivô, linha de base, pegada).
- **As direções:**
  - **8 direções** (S, SW, W, NW, N, NE, E, SE) só para o que **se move ou vira no cenário**: personagens,
    criaturas, NPCs, veículos. Vale para toda animação deles.
  - **O objeto estático** é visto de uma perspectiva só: **uma vista**, a do jogo, salvo quando o jogo pede outra.
    A animação ambiente (balanço, giro) sai só nessa vista.
- **Quem faz o quê:**
  - **o agente do jogo** monta as cenas e pede: criar, completar, corrigir;
  - **a engine** faz a autoria e entrega.
- **Fora do escopo:** construir o jogo, montar a cena e a lógica dela.
- **Os treinos** (cenas, personagens, fauna e flora feitos com a engine) existiram para **corrigir a engine**: sombra,
  forma, referência, modelos de personagem, fauna e flora. **O treino não vai para a pasta nova.** Dele vai só a
  correção, aplicada no motor e provada por uma fixture sintética mínima.

## 2. Por que uma pasta nova

A auditoria de 2026-11-23 achou sete mecanismos que trazem os mesmos problemas de volta a cada rodada.

| # | Mecanismo | A prova no `pixel-engine` |
|---|---|---|
| 1 | **O treino vira prova, e a prova não pode sair.** | 17 assets de treino seguram os goldens. 58 testes citam `challenge/`, que tem 90% dos 9 621 arquivos rastreados. |
| 2 | **A correção fica escrita, não aplicada.** | A ADR 0144 trocou a folhagem `pacotes` pelo `pontilhado`, mas a skill, o catálogo e os exemplos ainda levam à `pacotes`. O carvalho de prova saiu com a folhagem rejeitada. |
| 3 | **O agente cumpre a métrica, não a intenção.** | A trava de 400 linhas virou quebrar a clareira e o sítio em mais arquivos (ADR 0186). A trava "o kit não importa asset" virou copiar os tons da bétula para o kit. |
| 4 | **O plano carrega o erro.** | A v2 migrou "28 bípedes" (26 eram revisões de ninjas e espadachim) e fez do agente do jogo o autor. |
| 5 | **O executor se aprova sozinho.** | M0–M9 em 3 dias, cada um aprovado pelo resumo do próprio agente. |
| 6 | **Vários agentes escrevem ao mesmo tempo.** | Durante a auditoria, outra sessão commitou no `main`. O `AGENTS.md` está velho e há três skills divergentes. As regras moram na memória pessoal de um agente. |
| 7 | **Toda revisão antiga precisa ser reconstruível.** | O registro tem 147 gramáticas, das quais 17 em uso. A tabela de hashes segura todas, e convivem três formatos de composição. |

Estado do código no `pixel-engine`:
- 16 funções de topo sem referência;
- 15 usadas só por testes;
- 3 pacotes vazios;
- reexportações por compatibilidade;
- 346 violações de argumento sem uso e de complexidade;
- `.git` de 605 MB;
- 24,5 mil linhas de markdown em `docs/`.

**A pasta nova quebra os mecanismos 1, 6 e 7 pela construção:**
- nada entra sem ser pedido pelo fluxo ou por uma fixture;
- nenhuma outra sessão escreve nela;
- não há revisão antiga a preservar.

**Os mecanismos 2, 3, 4 e 5 continuam possíveis** e são cobrados pelas invariantes (seção 3) e pela prova de fora
(seção 7).

## 3. As invariantes (valem desde o primeiro commit)

Cada uma é verificada por teste ou pela prova de fora, nunca por um resumo.

| Invariante | Como se verifica |
|---|---|
| **I1. O pronto vem de fora.** A correção só termina quando a prova de fora passa, feita por um agente sem contexto que não escreveu o código. | o relatório da prova, com números e pranchas |
| **I2. Nenhum treino na pasta nova.** A prova de cada capacidade é uma fixture sintética mínima: o menor caso que mostra a capacidade, mais o controle negativo. | teste: nada rastreado com nome de asset ou cena de treino; nenhum workspace fora de `tests/fixtures/` |
| **I3. Uma correção só conta quando a engine recusa o jeito antigo.** O que foi substituído não é portado. Se a forma antiga ainda puder ser pedida, ela é recusada com código e dica. | teste: a composição com a forma antiga é recusada |
| **I4. Nada em `src/` conhece um asset.** Sem gramática, composição, módulo, tom ou constante com nome de asset ou de cena. O registro lê composições de uma pasta que recebe. | teste por AST e por nome de arquivo, com controle negativo |
| **I5. Um formato de composição, sem leitor de migração.** | o loader com um formato só; nenhum `migracao` |
| **I6. Uma fonte de regras.** O `docs/regras.md` (até 120 linhas), citado pelo `CLAUDE.md`, pelo `AGENTS.md` e pela skill única. O que dá para checar é checagem, não texto. | teste: os três citam o `regras.md` e não repetem regra |
| **I7. O `pixel-engine` é só leitura.** Nenhuma escrita, commit, build ou workspace dentro dele. | `git status` do `pixel-engine` igual ao do início |
| **I8. O que a prévia aceita, o asset aceita.** A `previa` e o `checar` aplicam os mesmos limites e recusas do build, e toda recusa traz código e dica. | teste: uma composição acima do limite é recusada igual na prévia e no build |
| **I9. Pare em vez de piorar.** Se um limite obriga a perder qualidade visível, a causa é corrigida no motor (a peça, o limite), não no desenho. | prancha antes/depois no relatório |
| **I10. Código limpo: só fica o que é usado.** Não ficam: import, variável, argumento, função, classe, módulo ou pacote sem uso; código comentado; código usado só por teste; reexportação; `noqa`; `type: ignore`; lista de exceções. Funções dentro dos tetos de tamanho e complexidade, por desenho, não por corte. | o ruff com `F`, `ARG`, `ERA`, `C901`, `PLR0912/0913/0915`; um teste de código morto por referência, com controle negativo; o mypy estrito; tudo no `check.py`, sem exceção |
| **I11. Fiel ao que já funcionava.** Toda capacidade portada dá o mesmo pixel que o `pixel-engine` na mesma entrada, salvo as mudanças intencionais da seção 5. | o teste de oráculo da seção 4, nas fixtures |

## 4. Como portar: por demanda, com oráculo

- **Nada se copia por pasta.** Um módulo, função ou peça só entra quando o fluxo de um asset (seção 6) ou uma fixture
  precisa dele. Entra a função, não o arquivo, e já no padrão da I10.
- **O oráculo:** para cada fixture, o `pixel-engine` (lido, nunca escrito) gera os quadros da mesma entrada, e a pasta
  nova tem de dar o mesmo pixel. O oráculo roda a partir de uma cópia exportada (`git archive`) numa pasta
  temporária, nunca dentro do `pixel-engine`. A diferença só é aceita se estiver na lista de mudanças intencionais
  (seção 5), com prancha.
- **O que não se porta nunca:**
  - `challenge/` e qualquer workspace;
  - `design/cenas/`, os `registro_*` por cena;
  - `design/compositions/` (ninjas, espadachim, aldeão, cão, raposa, plantas, props);
  - as gramáticas em Python de asset;
  - `design/migracao.py` e os formatos `biped_*`/`plant_*`;
  - a tabela `grammar_hashes.json`;
  - os movimentos de cena (saudação a outro lobo, combate, posturas);
  - as peças substituídas (a folhagem `pacotes`);
  - as ADRs, as revisões, as evidências, as referências de treino, `examples/` e `benchmarks/`;
  - as três skills atuais;
  - a skill do jogo como manual de autoria.
- **As lições vêm de um inventário, não das pastas.** Fontes:
  - o Anexo A do `docs/reviews/2026-11-21-plano-v2.md`;
  - as ADRs de flora, luz e sombra, rig e movimento;
  - a memória pessoal do Claude listada na seção 9 (só leitura).

  Cada lição vira peça vigente, checagem ou padrão do estilo, com a fixture que a prova. Nenhuma lição fica só como
  texto: o que não dá para checar vira uma linha do `regras.md`.
- **Como decidir sem perguntar:** quando o plano não fixa uma escolha, aplique nesta ordem:
  1. o objetivo (seção 1);
  2. as invariantes;
  3. "o menor que funciona";
  4. "o que o `pixel-engine` fazia, se não for treino nem jeito substituído".

  Registre a decisão em uma linha em `docs/decisoes.md` (a escolha e a regra que a justifica). Nunca pare para
  perguntar ao dono.

## 5. Decisões já tomadas e mudanças intencionais

- **Nome e pastas:**
  - a pasta é `D:\gabri\Projetos\Gabriel\pixel-asset-engine`;
  - o pacote Python continua `pixel_forge` e a CLI continua `pfe`;
  - Python 3.12 e `uv`, como hoje.
- **Git e treino:** repositório git novo, branch `main`, sem histórico, sem remoto e sem push. O `af8f72eb` e o resto
  do treino ficam no `pixel-engine`.
- **O acervo de trabalho** (onde a engine cria, completa e corrige assets) fica fora do git, numa pasta configurável.
  O padrão é `~/.pixel-forge/acervo`. Os builds também ficam fora do git.
- **Porte por categoria**, em relação ao humano de 1,65 m (~44 px):

  | Categoria | Porte |
  |---|---|
  | árvore grande | ~2,5× (~4 m no jogo) |
  | árvore pequena | ~1,5× |
  | arbusto | ~0,6× |
  | casa | ~2× |
  | prop de mão | ~0,3× |

  É checado: fora da faixa da categoria recusa com dica.
- **Vistas:**
  - o estático tem 1 vista por padrão (pode declarar 2 ou 4 se o pedido disser);
  - quem anda ou vira tem 8, em toda animação;
  - o que não cumprir recusa.
- **Mudanças intencionais de pixel, com prancha contra o oráculo:**
  - a folhagem de copa é o `pontilhado`;
  - a paleta base troca os nomes de espécie de treino (`birch_leaf`…) por nomes de função (`folha_clara`, `folha`,
    `folha_escura`, `casca`…) e ganha os verdes de folhosa;
  - o `max_parts` é revisto pela folhagem vigente.
- **Fora desta correção** (entram num plano seguinte, depois da prova de fora): tiles e autotile, plano de fundo,
  combate e um formato de pedido mais rico. A skill desta correção já atende `criar`, `completar` e `corrigir` de
  personagem, criatura, prop e flora.
- **O teto de `docs/`:** 1 500 linhas no total, com o plano copiado, `regras.md`, `estado.md`, `decisoes.md`, o
  contrato do jogo e as coordenadas.
- **ADR:** nenhuma. A decisão vai em `docs/decisoes.md` e o porquê vai no commit.

## 6. Os passos (uma sessão pode fazer todos; o `docs/estado.md` passa de uma para a outra)

Cada passo termina com:
- um commit;
- o `docs/estado.md` (até 60 linhas) com o feito, os números e o próximo passo.

Se a sessão acabar no meio, a próxima recomeça pelo `docs/estado.md` com o mesmo prompt.

### N0 — O esqueleto com as travas
- `git init` na pasta nova.
- `pyproject.toml` só com as dependências que o código usar, `uv`, ruff e mypy estrito.
- `scripts/check.py` com tudo.
- O plano copiado para `docs/plano.md`.
- **As travas, já verdes no repositório vazio e cada uma com controle negativo:**
  - código limpo (I10);
  - camadas (render, rig e export não importam desenho nem movimento);
  - nada de asset em `src/` (I4);
  - nada de treino (I2);
  - teto de módulo de 400 linhas sem lista de exceções;
  - teto de `docs/`;
  - uma fonte de regras (I6).
- **O oráculo:** um script que exporta o `pixel-engine` (`git archive HEAD`) para uma pasta temporária e roda nele a
  mesma entrada.

### N1 — O núcleo por demanda
- Porta o mínimo para renderizar e exportar, igual ao oráculo, três fixtures sintéticas:
  - um bloco com sombra projetada;
  - um tronco sólido de revolução;
  - uma face com a luz pela normal.
- Entram, conforme a fixture pedir: contratos, núcleo q8, geometria, projeção 3/4 (profundidade 0,35, ADR 0149),
  raster, contorno, sombra, export (`pfe-jogo/1`, com o roundtrip do atlas) e a qualidade mínima.

### N2 — O kit vigente e as lições
- **O inventário das lições** (`docs/decisoes.md` aponta cada linha para a peça, checagem ou padrão e a fixture).
- **O formato único de composição**, com:
  - tipo e rig;
  - medidas em metros;
  - nós do kit;
  - vistas;
  - landmarks;
  - movimento;
  - traços.
- **As peças vigentes**, portadas e conferidas contra o oráculo: as de construção, de pedra, de tronco, de galhos, o
  `pontilhado`, os `galhos_em_pena`, a cortina, o corpo humano e o canino, e as roupas e acessórios que forem gerais.
  - Cada peça tem até 12 argumentos e 250 linhas, prancha e teste com controle negativo.
- **O rig por papéis**, o IK de N segmentos e os geradores por tipo de corpo:
  - a passada;
  - o parado;
  - a corrida;
  - o balanço;
  - o giro;
  - a ação por acessório.
- **O estilo base com a paleta por função, o porte por categoria e as vistas**, todos checados.

### N3 — O caminho curto de um asset
- **A CLI mínima:** `previa`, `checar`, `build`, `exportar`, `olhar`, `catalogo`, `conjunto`, `revisar` e
  `atualizar`.
- **Um asset vive no acervo, sem projeto de jogo:** nada de `pfe init` como primeiro passo e nada de candidatos para
  composição sem sorteio. A identidade e as baselines saem em segundos.
- **A `previa` aplica os limites do build (I8).** Toda recusa vem com código e dica.
- **O catálogo diz para que serve cada peça.** Só existe o vigente.
- **Meta:** tempo de máquina abaixo de 1 min do pedido ao export de um estático.

### N4 — As regras e a skill
- **O `docs/regras.md`:** as lições que não viraram checagem, uma linha cada.
- **`CLAUDE.md` e `AGENTS.md` curtos**, os dois citando o `regras.md`.
- **Uma skill, a da engine** (`.claude/skills/` e o espelho em `.agents/skills/`, gerado e conferido por teste). Ela
  vai do pedido (`criar`, `completar`, `corrigir`) ao export.
- **Um formulário de pedido para o agente do jogo**, gerado da skill, dizendo:
  - o quê: o tipo, a função no jogo, se anda ou é estático, o porte;
  - onde fica;
  - a referência, se houver.
- **Quatro exemplos, feitos pelo padrão vigente**, em `tests/fixtures/exemplos/`:
  - um estático de vista única;
  - uma árvore com `pontilhado`;
  - um humanoide nas 8 direções;
  - um quadrúpede nas 8 direções.

### N5 — A prova de fora
- **Um subagente novo, sem contexto,** recebe só o caminho da pasta nova e o roteiro da seção 7. Ele não pode ler
  `docs/plano.md`, `docs/decisoes.md` nem o `pixel-engine`.
- **Se a prova falhar** (escolha errada oferecida, recusa sem dica, quebra de I8 ou I9, tempo acima da meta), a causa
  é corrigida **no motor**, não no asset, e a prova roda de novo com um subagente novo. São no máximo três rodadas.
- **O relatório final para o dono** (no chat e em `docs/estado.md`):
  - o que existe;
  - os números contra a linha de base;
  - as pranchas;
  - as mudanças intencionais;
  - o que não passou, se houver.

  A revisão artística fica pendente para o dono.

## 7. A prova de fora

- **Quem faz:** um agente que não escreveu o código, com acesso só à pasta nova e à skill dela.
- **Onde:** o trabalho acontece no acervo; nada é commitado.
- **Os três pedidos:**
  1. *Um carvalho-roble de pasto, árvore grande, copa larga e baixa, para a orla de um campo.* Estático, uma vista.
  2. *Um poço de pedra com telhadinho de palha e balde.* Estático, uma vista.
  3. *Uma camponesa de saia longa e lenço, parada e andando.* 8 direções.
- **O que se mede em cada pedido:**
  - o tempo de relógio e de máquina por etapa;
  - as chamadas e os tokens;
  - as recusas e se tinham dica;
  - as escolhas que a engine ofereceu e se alguma levava a um jeito substituído;
  - o que precisou ler fora da skill;
  - se perdeu qualidade para passar num limite.
- **Passa quando:**
  - os três exports verificam;
  - o carvalho sai com `pontilhado` sem ler nada além da skill;
  - as vistas estão certas (1, 1 e 8);
  - nenhuma recusa vem sem dica;
  - nenhum desenho foi piorado para caber;
  - o estático fica abaixo de 1 min de máquina.
- **A linha de base no `pixel-engine` (só o carvalho):**
  - ~9 min de relógio;
  - máquina: prévia 5 s, `novo` 30 s + 1 min 57 s, build 23 s, export 2 s;
  - uma recusa sem dica;
  - a folhagem rejeitada usada, e a copa piorada para caber.

## 8. O que não fazer

- Escrever, buildar ou criar workspace dentro do `pixel-engine`.
- Copiar uma pasta inteira "para depois limpar".
- Portar treino, peça substituída, formato antigo, leitor de migração, reexportação ou função sem uso.
- Cumprir uma trava de um jeito que mantém o problema: quebrar arquivo para caber, mover dado de asset para o kit,
  criar exceção, silenciar o linter.
- Escrever uma lição só como texto quando ela pode ser checagem.
- Degradar o desenho para passar num limite.
- Dar 8 direções a um estático, ou menos de 8 a quem anda.
- Parar para perguntar ao dono: decida pela seção 4 e registre.
- Declarar pronto sem a prova de fora.
- Acrescentar o que está fora desta correção (seção 5).

## 9. A memória pessoal do Claude (fonte de lições, só leitura)

`C:\Users\gabri\.claude\projects\D--gabri-Projetos-Gabriel-pixel-engine\memory\`.

**As que trazem lição para o inventário do N2:**
- o propósito: `proposito-fabrica-assets`, `feedback-treino-separado-do-motor`;
- a forma: `feedback-forma-nao-cor`, `feedback-anatomia-referencia`, `feedback-referencia-concreta-flora`,
  `feedback-referencia-nao-e-recorte`, `criacao-nao-reuso`, `feedback-solucao-pixel-art`;
- a escala e a câmera: `feedback-tamanho-por-asset`, `escala-do-mundo`, `camera-padrao-rpg`;
- o padrão do motor: `feedback-treino-corrige-motor`, `feedback-asset-novo-no-padrao`,
  `feedback-nao-degradar-para-passar`;
- o custo: `contexto-enxuto`.

**As outras são de treino ou de preferência pessoal e não entram.**

A pasta nova terá uma memória própria e vazia: as regras dela ficam no `regras.md`, não na memória.
