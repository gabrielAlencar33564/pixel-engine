---
name: pixel-asset-engine
description: Cria, completa e corrige assets de pixel art de jogo (prop, flora, construção, humano, quadrúpede) com a engine local `pfe`, do pedido ao export verificado, no acervo e sem projeto de jogo.
---

# Pixel Asset Engine: do pedido ao export

As regras de desenho e de trabalho estão em `docs/regras.md`; leia antes. Aqui está o caminho. A engine é a mão: você
descreve o asset em dados (a **composição**), e ela desenha, confere e exporta. Rode tudo de dentro da pasta da engine
com `uv run pfe ...` (ou `.venv/Scripts/pfe.exe` no Windows) e sempre com `--json`.

## 1. O pedido

O agente do jogo pede com este formulário (ele também está em `docs/pedido.md`):

<!-- pedido -->
- **Verbo:** criar (um asset novo), completar (o que falta num asset: um clipe, uma vista pedida) ou corrigir (o
  desenho errado de um asset).
- **O quê:** o tipo (objeto, construção, árvore, arbusto, humano, quadrúpede), a função no jogo, se anda ou é
  estático, e o porte (a categoria da tabela de porte ou a altura em metros).
- **Onde fica:** o lugar no jogo (a orla de um campo, um pátio, uma casa), que diz o clima e o desgaste.
- **Referência:** a espécie, o modelo ou a imagem, se houver.
<!-- /pedido -->

## 2. A ficha

Antes de compor, escreva a ficha no campo `reference` da composição: a referência concreta (espécie, modelo, época),
as medidas reais em metros e o que dá vida à coisa (a copa larga e baixa, a palha gasta, a saia que balança).

## 3. O kit

`pfe catalogo --json` grava `<acervo>/catalogo/index.json` e uma prancha por peça (as 3 variações, da esquerda para a
direita). Cada peça tem o tipo (`prop`, `humanoide`, `quadrupede`), para que serve, os argumentos (nome, tipo, para que
serve, padrão; sem padrão = obrigatório), as variações com os argumentos de cada uma (o jeito mais rápido de ver as
unidades), as partes que ela gera na primeira variação (os ids que os traços citam), as âncoras que deixa e a lista
de materiais do estilo. Escolha as peças pela descrição e pela prancha. Só
existe o que é vigente: a peça que não está no catálogo não existe.

## 4. A composição

Um JSON `<id>.r<n>.json` (o `<id>` em minúsculas, `_` e dígitos). Campos:

| Campo | O que é |
|---|---|
| `id`, `revision` | o asset e a revisão (1 no primeiro) |
| `description`, `reference` | o que é e a ficha |
| `tipo` | `prop` (parado, na raiz), `humanoide` ou `quadrupede` (o rig do modelo) |
| `categoria` | o porte esperado (tabela abaixo); a engine mede a altura e recusa fora da faixa |
| `semente` | inteiro; a semente de cada nó sai dela e do id do nó |
| `medidas` | nomes → expressões, usados nos argumentos como `$nome` |
| `nos` | as peças, em ordem (veja abaixo) |
| `vistas` | o prop parado: `{"S": {}}` (2 ou 4 cardinais só se o pedido disser); quem anda: as 8 direções `S SW W NW N NE E SE` |
| `movimento` | o prop: `["static"]` (balanço `{"receita": "balanco", ...}` ou giro `{"receita": "giro", ...}` se o pedido disser); o humano e o quadrúpede: `["idle", "walk"]`; o humano armado, também `"attack"` (o golpe de espada, sem laço) |
| `landmarks` | pontos do jogo no prop (`"sort_front": ["0", "0", "0"]`) |
| `tracos` | o que tem de ler no sprite: `id`, `description`, `parts` (ids de partes), `verification` (`observable`: recusado se nenhuma vista mostra um pixel dele) e, se quiser, `reads_in_silhouette` (tem de tocar a borda da figura) |

**Expressões:** números com unidade (`1.2m`, `30cm`, `8mm`, `3px`, `120%`, `15deg`), `$medida`, `+ - * /`, `min`,
`max`, `round` e parênteses. O tamanho sai dos metros reais: o humano de 1,65 m tem ~44 px na tela.

**Um nó:** `{"id", "peca", "args"}` e, se precisar: `repete` (`{"sobre": "lados", "n": 2}` dá `$lado` −1 e 1;
`"linha"` dá `$i` e `$t`; `"anel"` dá `$cos` e `$sen`), `grupo` (o contorno: partes do mesmo grupo não se contornam
entre si), `pilha` e `camada` (na mesma pilha, o nó de camada maior cobre o de camada menor que ele toca: o telhado
numa camada acima da parede cobre o alto dela onde o beiral desce na tela; as faces internas de uma peça ficam entre a
camada dela e a seguinte; para nada se cobrir, use pilhas diferentes), `osso`
(`raiz`; com balanço, `tronco` ou `cadeia`; com giro, `giro`). Um argumento pode citar a âncora de um nó de antes: `"pontas": "galhos.pontas"`.

**Limites:** `description` e os textos dos traços até 400 caracteres, `reference` até 2000, até 64 nós, e o sprite até
512 px de lado (o canvas inclui a sombra no chão, à direita). Passar de um limite é recusa com a medida e a dica.

**Coordenadas:** +X à esquerda do asset, +Y para a frente (a câmera do S), +Z para cima; a origem é o pé do asset.

**A câmera** é uma só, o 3/4 oblíquo: a altura aparece a cos 45° e o chão e o topo a 0,6 (o que está à frente desce na
tela 0,6 px por px); a luz vem de cima e da esquerda, e a sombra no chão cai à direita. O contrato está em
`docs/coordenadas.md`.

**O humano:** o primeiro nó é `corpo_humano`; a roupa vem depois, cada peça um nó. A `espada` vai na mão direita e dá ao canvas 16 px a mais em cima e de cada lado; com ela, o clipe `attack` (480 ms, 8 quadros, sem laço) sobe a lâmina por cima do ombro e corta para a frente. **O quadrúpede:** um nó
`corpo_canino`, com as marcas e as orelhas como argumentos.

**A pedra solta** é o `penedo`, não o `elipsoide` (que lê como ovo): um poliedro sorteado pela semente, com faces, quinas e o tom pela normal; `agudo` fecha a ponta, `inclina` deita o topo, `irregular` lasca, `musgo` cobre as faces de cima, `fendas` racha as maiores, e `material` é a família (`alvenaria`, o granito; `palha`, o arenito, com `tom` -1). Outra semente dá outra pedra do mesmo tipo: para variar o cenário, varie a semente e a forma, não só o tamanho.

**A planta** não tem uma receita só. Escolha a construção pela ficha da espécie; num conjunto, use mais de uma:

| Construção | Nós | O que dá |
|---|---|---|
| a massa | `tronco_em_pe` + `copa` | a folhosa de copa fechada. `perfil`: 0 a redonda, 1 a gota (fina no alto), -1 o guarda-sol (só a metade de cima). `tufos` e `tamanho`: a copa pesada (6 de 0.45) ou a leve (14 de 0.22). `pende`: a cortina de ramos finos em volta da copa (1 desce até o fundo dela; 2 ou mais, com o `perfil` negativo, é o chorão) |
| a aberta | `tronco_em_pe` + `galhos` com `sobe` + `copa_aberta` | os galhos à mostra e uma nuvem de folhas em cada ponta: a árvore velha, a de copa rala, a de copa em nuvens |
| os andares | `tronco_em_pe` + `copa_conica` | a conífera de saias recortadas; `pontas`, `recorte` e `cai` dão a saia cheia ou a magra |
| a roseta no alto | `tronco_em_pe` + `touceira` com o `pe` no alto do tronco, `largura` e `pena` | a palma (em pena), a folha em espada (lisa) |
| a seca | `tronco_em_pe` + `galhos` | a árvore sem folha |
| a moita | `copa` no chão, sem tronco | o arbusto; com `salpico` na `superficie` dela, a flor e o fruto; a moita de duas ou três massas são nós de `copa` com `desvio`, no mesmo `grupo` |
| a touceira | `touceira` | lâminas: finas, o capim e o junco; com `largura` e `pena`, a samambaia; com `salpico` nas `pontas`, a flor do campo e a espiga (a flor pede a lâmina quase reta, `cai` até 0.1; a espiga em pé, `alonga` 3) |

A folhagem é uma massa de luz só (o claro em cima e à esquerda) por `grupo`: os nós de folhagem do mesmo grupo
clareiam e escurecem juntos, cada lóbulo é um relevo na massa, e a beira de cada um sai recortada em folhas. O
`desvio` tira a copa do eixo (a copa de um lado só, a árvore batida pelo vento). Tudo é sorteado pela semente: outra semente dá outra planta da mesma espécie. **Para variar o cenário,** duas plantas do
mesmo conjunto não saem da mesma receita com outra semente e outro tamanho: varie a construção, o `perfil`, a
proporção da copa, o tronco (a `curva`, a `inclinacao`, as `raizes`, dois troncos) e a folhagem; dentro da mesma
espécie, a semente e o `irregular`. A crítica (seção 6) mede a silhueta contra as irmãs do acervo e acusa a parecida.
A planta não se faz de `elipsoide`, `poligono` nem `fios`: a crítica acusa o ovo, o cone liso e o tom chapado. A erva
de menos de 40 cm vai na categoria `objeto` (o `arbusto` começa em 0,25× o humano).

A copa em massa mostra o alto e cobre o tronco pela frente: do tronco sobra na tela a altura do centro da copa × 0,71
menos √((meio fundo × 0,6)² + (meia altura × 0,71)²); para ele aparecer mais, suba a copa ou diminua o `fundo`. A
sombra da copa cai no chão à direita e entra no canvas. Leve o tronco até perto do centro da copa (os lóbulos recuam
da borda: o tronco que para na base dela a deixa no ar). Sob a copa em massa os `galhos` quase não aparecem (deixam
as pontas para ela pôr um tufo em cada uma) e saem em `escondidas`: é esperado. Os `galhos` acompanham o topo do
tronco inclinado. O tronco não é um cilindro: por padrão o pé abre no chão e o fuste engrossa
e afina; dê a ele o que a espécie tem (a `curva` do tronco novo, as `raizes` e os `nos` do velho, a casca
`casca_sulcada` com o veio em pé ou `casca_anelada` com os anéis deitados).

**Porte por categoria** (em humanos de 1,65 m):

<!-- portes -->
| Categoria | Faixa | Típico |
|---|---|---|
| `arvore_grande` | de 1.8× a 4.0× | ~2,5× (~4 m no jogo) |
| `arvore_pequena` | de 1.0× a 2.0× | ~1,5× |
| `arbusto` | de 0.25× a 1.0× | ~0,6× |
| `casa` | de 1.3× a 3.0× | ~2× |
| `estrutura` | de 0.3× a 2.5× | de 0,3× a 2,5× |
| `objeto` | de 0.1× a 1.5× | de 0,1× a 1,5× |
| `prop_de_mao` | de 0.03× a 0.6× | ~0,3× |
| `humano` | de 0.6× a 1.25× | ~1× |
| `quadrupede` | de 0.15× a 1.2× | ~0,5× |
<!-- /portes -->

**Exemplos feitos pelo padrão vigente** (leia o que for do mesmo tipo antes de compor; não copie: o asset nasce da
ficha dele): `tests/fixtures/exemplos/banco.r1.json` (estático de vista única), `arvore_folhosa.r1.json` (árvore de copa em
massa), `arvore_aberta.r1.json` (árvore de galhos à mostra, com a `copa_aberta`), `viajante.r1.json` (humano, 8 direções) e `canino.r1.json` (quadrúpede, 8 direções).

## 5. O caminho

O acervo é `~/.pixel-forge/acervo` (ou `--acervo`, ou `PFE_ACERVO`). Grave a composição em `<acervo>/composicoes/`.

1. `pfe previa <composição> --json`: o repouso de cada vista com as mesmas recusas do build, a prancha
   (`previas/<id>.r<n>.png`, recorte real ampliado até 4×) e os números: vistas, canvas, altura, porte, os ids das
   `partes` (que os traços citam), as `escondidas` (por vista, as partes que a vista desenha e nenhum pixel mostra;
   os volumes de uma copa não entram: o lado de lá dela fica sempre escondido), os pixels de cada traço em cada vista
   (`tracos`) e, da planta, a `critica` (as medidas e os achados da seção 6, sem as irmãs). Leia os números, depois a
   prancha; ajuste a composição e repita. A parte escondida que devia aparecer (o olho sob a aba, a mão de lá) é
   defeito, e o achado `defeito` também: não siga com eles.
2. `pfe radiografia <composição> --json`: o modelo ampliado até 4× pela geometria, de frente, de perfil e de costas
   em elevação (sem a câmera do jogo) e, na fileira de baixo, na câmera do jogo (`radiografias/<id>.r<n>.png`). É
   onde a forma se analisa: no tamanho do jogo um rosto tem 5 px, e o defeito da forma se confunde com a perda da
   redução. Do humano vêm as `medidas` do corpo, cada uma com a faixa do corpo real e o que ela quer dizer: a que
   está fora da faixa é defeito do modelo (do motor), não da composição; diga, não disfarce com roupa nem com pose.
3. `pfe conjunto <composição> ... --json`: os assets lado a lado pelo chão, com o humano de 1,65 m de régua.
4. `pfe checar <composição> --json`: todos os quadros do build conferidos (os clipes de quem anda), sem gravar.
5. `pfe build <composição> --json`: os quadros no acervo; devolve o `build`.
6. Da planta, `pfe critica <build> --json` e o parecer de outro agente (seção 6): sem a crítica que passa, o pacote
   é recusado (`CRITICA_PENDENTE`).
7. `pfe exportar <build> --json` e `pfe exportar <build> --verificar --json`: o pacote do jogo (`pfe-jogo/1`, atlas e
   JSON) e a releitura dele contra o build.
8. `pfe olhar <build> --json`: a prancha de todos os quadros do pacote e os números (uma fileira por clipe e direção,
   na ordem de `clipes` e, dentro do clipe, das direções em ordem alfabética: E, N, NE, NW, S, SE, SW, W).

Toda recusa vem como `{"ok": false, "errors": [{"code", "message", "hint", "path"}]}`, com o caminho na composição:
siga a dica e corrija. A recusa `MOTOR` é defeito da engine, não seu: pare e registre.

## 6. A crítica da planta

A planta (a árvore, o arbusto, qualquer asset com `copa` ou `touceira`) só sai depois de medida e revisada por outro
agente. `pfe critica <build> --json` (só o caminho do build: o acervo é o dele) devolve:

- `medidas` e `achados`: cada achado tem o `codigo`, a `gravidade`, a `medida` e a `dica`. O `defeito` (a folhagem
  lisa, espelhada ou sem lado claro; a silhueta igual à de uma irmã) impede a crítica de passar: corrija a composição
  e volte ao passo 1 com `pfe atualizar`. O `aviso` (o tronco que sumiu, o pedaço solto) pede o olho de quem revisa. O
  defeito que você acha medido errado é defeito da engine: pare e registre, não contorne.
- `irmas`: as três composições da mesma categoria no acervo (com ou sem build) de silhueta mais parecida, e o quanto
  (de 0 a 1; a partir de `parecida_a_partir_de` é defeito). A touceira não tem medida de massa: dela só se compara a
  silhueta.
- `prancha` (`criticas/<build>.png`): em cima, o sprite e a silhueta dele; embaixo, as irmãs e as silhuetas delas.
- `perguntas` e `ficha`: o que só o olho responde.

Quem responde às perguntas não é quem compôs. Passe a outro agente (um subagente sem a sua conversa) só a prancha, a
ficha e as perguntas, sem a sua explicação; ele olha a imagem e responde cada pergunta com `ok` e uma nota do que
viu. Grave as respostas dele num arquivo e registre:

```json
{"respostas": {"silhueta": {"ok": true, "nota": "copa larga e baixa sobre um tronco curto: lê como árvore de quintal"},
               "massa_de_luz": {"ok": false, "nota": "o lado direito é uma mancha escura sem relevo"}}}
```

`pfe critica <build> --parecer <arquivo.json> --por <quem revisou> --json` (todas as perguntas, cada nota com 12
caracteres ou mais). O `veredito` é `passa` sem defeito medido e com todas as respostas boas; senão é `corrigir`, e
`a_corrigir` lista o que falta: mude a composição, rode `pfe atualizar` e refaça o caminho (o build novo pede a
crítica dele). A crítica não aprova a arte: isso segue com o dono (seção 8).

## 7. Completar e corrigir

A revisão é imutável: o build recusa (`IDENTIDADE`) a mesma revisão com outro desenho. O build também: o id dele leva
a composição, o estilo, a versão do motor e os pixels, então o mesmo id é sempre o mesmo desenho; se o motor mudar o
pixel, o mesmo pedido dá outro build, e o pacote antigo segue valendo para o build antigo. Para completar ou corrigir,
edite a composição e rode `pfe atualizar <composição> --json`: ela vira a revisão seguinte no acervo; siga o caminho
com o arquivo que ele devolve.

## 8. A entrega

Entregue o caminho do pacote (`exports/<build>/atlas.json`), a prancha do `olhar` e os números; da planta, também a
prancha da crítica, as irmãs e quem revisou. O pacote sai como
prévia, com a arte pendente: só o dono a revisa (`pfe revisar <build> --veredito ... --nota ... --por ...`), e só o
build aprovado sai com `pfe exportar <build> --publicar`.
