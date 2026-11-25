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
| `movimento` | o prop: `["static"]` (balanço `{"receita": "balanco", ...}` ou giro `{"receita": "giro", ...}` se o pedido disser); o humano e o quadrúpede: `["idle", "walk"]` |
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

**O humano:** o primeiro nó é `corpo_humano`; a roupa vem depois, cada peça um nó. **O quadrúpede:** um nó
`corpo_canino`, com as marcas e as orelhas como argumentos.

**A árvore e a moita** são volumes: `tronco_em_pe` e a copa, que é `copa` (a folhosa, em tufos redondos; no chão e
sem tronco é a moita; com `pende`, os ramos caem) ou `copa_conica` (a conífera, em andares). A copa mostra o alto e
cobre o tronco pela frente: do tronco sobra na tela a altura do centro da copa × 0,71 menos
√((meio fundo × 0,6)² + (meia altura × 0,71)²); para ele aparecer mais, suba a copa ou diminua o `fundo`. A sombra
da copa cai no chão à direita e entra no canvas. Os `galhos` são opcionais (a copa cobre quase todos; sozinhos, são
a árvore seca) e deixam as pontas para a copa pôr um tufo em cada uma. O tronco não é um cilindro: por padrão o pé
abre no chão e o fuste engrossa e afina; dê a ele o que a espécie tem (a `curva` do tronco novo, as `raizes` e os
`nos` do velho, a casca `casca_sulcada` com o veio em pé ou `casca_anelada` com os anéis deitados).

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
ficha dele): `tests/fixtures/exemplos/banco.r1.json` (estático de vista única), `arvore_folhosa.r1.json` (árvore com a
`copa` em volumes), `viajante.r1.json` (humano, 8 direções) e `canino.r1.json` (quadrúpede, 8 direções).

## 5. O caminho

O acervo é `~/.pixel-forge/acervo` (ou `--acervo`, ou `PFE_ACERVO`). Grave a composição em `<acervo>/composicoes/`.

1. `pfe previa <composição> --json`: o repouso de cada vista com as mesmas recusas do build, a prancha
   (`previas/<id>.r<n>.png`, recorte real ampliado até 4×) e os números: vistas, canvas, altura, porte, os ids das
   `partes` (que os traços citam), as `escondidas` (por vista, as partes que a vista desenha e nenhum pixel mostra) e
   os pixels de cada traço em cada vista (`tracos`). Leia os números, depois a prancha; ajuste a composição e
   repita. A parte escondida que devia aparecer (o olho sob a aba, a mão de lá) é defeito: não siga com ela.
2. `pfe radiografia <composição> --json`: o modelo ampliado até 4× pela geometria, de frente, de perfil e de costas
   em elevação (sem a câmera do jogo) e, na fileira de baixo, na câmera do jogo (`radiografias/<id>.r<n>.png`). É
   onde a forma se analisa: no tamanho do jogo um rosto tem 5 px, e o defeito da forma se confunde com a perda da
   redução. Do humano vêm as `medidas` do corpo, cada uma com a faixa do corpo real e o que ela quer dizer: a que
   está fora da faixa é defeito do modelo (do motor), não da composição; diga, não disfarce com roupa nem com pose.
3. `pfe conjunto <composição> ... --json`: os assets lado a lado pelo chão, com o humano de 1,65 m de régua.
4. `pfe checar <composição> --json`: todos os quadros do build conferidos (os clipes de quem anda), sem gravar.
5. `pfe build <composição> --json`: os quadros no acervo; devolve o `build`.
6. `pfe exportar <build> --json` e `pfe exportar <build> --verificar --json`: o pacote do jogo (`pfe-jogo/1`, atlas e
   JSON) e a releitura dele contra o build.
7. `pfe olhar <build> --json`: a prancha de todos os quadros do pacote e os números (uma fileira por clipe e direção,
   na ordem de `clipes` e, dentro do clipe, das direções em ordem alfabética: E, N, NE, NW, S, SE, SW, W).

Toda recusa vem como `{"ok": false, "errors": [{"code", "message", "hint", "path"}]}`, com o caminho na composição:
siga a dica e corrija. A recusa `MOTOR` é defeito da engine, não seu: pare e registre.

## 6. Completar e corrigir

A revisão é imutável: o build recusa (`IDENTIDADE`) a mesma revisão com outro desenho. O build também: o id dele leva
a composição, o estilo, a versão do motor e os pixels, então o mesmo id é sempre o mesmo desenho; se o motor mudar o
pixel, o mesmo pedido dá outro build, e o pacote antigo segue valendo para o build antigo. Para completar ou corrigir,
edite a composição e rode `pfe atualizar <composição> --json`: ela vira a revisão seguinte no acervo; siga o caminho
com o arquivo que ele devolve.

## 7. A entrega

Entregue o caminho do pacote (`exports/<build>/atlas.json`), a prancha do `olhar` e os números. O pacote sai como
prévia, com a arte pendente: só o dono a revisa (`pfe revisar <build> --veredito ... --nota ... --por ...`), e só o
build aprovado sai com `pfe exportar <build> --publicar`.
