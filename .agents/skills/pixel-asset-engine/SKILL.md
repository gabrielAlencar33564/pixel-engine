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
| `sombra` | só no prop: `meia_largura` (e `proporcao_pm`, `dx`, `dy`) da sombra de contato |
| `nos` | as peças, em ordem (veja abaixo) |
| `vistas` | o prop parado: `{"S": {}}` (2 ou 4 cardinais só se o pedido disser); quem anda: as 8 direções `S SW W NW N NE E SE` |
| `movimento` | o prop: `["static"]` (balanço `{"receita": "balanco", ...}` ou giro `{"receita": "giro", ...}` se o pedido disser); o humano e o quadrúpede: `["idle", "walk"]` |
| `landmarks` | pontos do jogo no prop (`"sort_front": ["0", "0", "0"]`) |
| `tracos` | o que tem de ler no sprite: `id`, `description`, `parts` (ids de partes), `verification` (`observable`) |

**Expressões:** números com unidade (`1.2m`, `30cm`, `8mm`, `3px`, `120%`, `15deg`), `$medida`, `+ - * /`, `min`,
`max`, `round` e parênteses. O tamanho sai dos metros reais: o humano de 1,65 m tem ~44 px na tela.

**Um nó:** `{"id", "peca", "args"}` e, se precisar: `repete` (`{"sobre": "lados", "n": 2}` dá `$lado` −1 e 1;
`"linha"` dá `$i` e `$t`; `"anel"` dá `$cos` e `$sen`), `grupo` (o contorno: partes do mesmo grupo não se contornam
entre si), `pilha` e `camada` (na mesma pilha, o nó de camada maior cobre o de camada menor que ele toca; as faces
internas de uma peça ficam entre a camada dela e a seguinte; para nada se cobrir, use pilhas diferentes), `osso`
(`raiz`; com balanço, `tronco` ou `cadeia`; com giro, `giro`). Um argumento pode citar a âncora de um nó de antes: `"cachos": "galhos.pontas"`.

**Limites:** `description` e os textos dos traços até 400 caracteres, `reference` até 2000, até 64 nós, e o sprite até
512 px de lado (o canvas inclui a sombra no chão, à direita). Passar de um limite é recusa com a medida e a dica.

**Coordenadas:** +X à esquerda do asset, +Y para a frente (a câmera do S), +Z para cima; a origem é o pé do asset.

**O humano:** o primeiro nó é `corpo_humano`; a roupa vem depois, cada peça um nó. **O quadrúpede:** um nó
`corpo_canino`, com as marcas e as orelhas como argumentos.

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
ficha dele): `tests/fixtures/exemplos/banco.r1.json` (estático de vista única), `arvore_folhosa.r1.json` (árvore com
`pontilhado`), `viajante.r1.json` (humano, 8 direções) e `canino.r1.json` (quadrúpede, 8 direções).

## 5. O caminho

O acervo é `~/.pixel-forge/acervo` (ou `--acervo`, ou `PFE_ACERVO`). Grave a composição em `<acervo>/composicoes/`.

1. `pfe previa <composição> --json`: o repouso de cada vista com as mesmas recusas do build, a prancha
   (`previas/<id>.r<n>.png`, recorte real ampliado até 4×) e os números (vistas, canvas, altura, porte e os ids das
   `partes`, que os traços citam). Leia os números, depois a prancha; ajuste a composição e repita.
2. `pfe conjunto <composição> ... --json`: os assets lado a lado pelo chão, com o humano de 1,65 m de régua.
3. `pfe checar <composição> --json`: todos os quadros do build conferidos (os clipes de quem anda), sem gravar.
4. `pfe build <composição> --json`: os quadros no acervo; devolve o `build`.
5. `pfe exportar <build> --json` e `pfe exportar <build> --verificar --json`: o pacote do jogo (`pfe-jogo/1`, atlas e
   JSON) e a releitura dele contra o build.
6. `pfe olhar <build> --json`: a prancha de todos os quadros do pacote e os números.

Toda recusa vem como `{"ok": false, "errors": [{"code", "message", "hint", "path"}]}`, com o caminho na composição:
siga a dica e corrija. A recusa `MOTOR` é defeito da engine, não seu: pare e registre.

## 6. Completar e corrigir

A revisão é imutável: o build recusa (`IDENTIDADE`) a mesma revisão com outro desenho. Para completar ou corrigir,
edite a composição e rode `pfe atualizar <composição> --json`: ela vira a revisão seguinte no acervo; siga o caminho
com o arquivo que ele devolve.

## 7. A entrega

Entregue o caminho do pacote (`exports/<build>/atlas.json`), a prancha do `olhar` e os números. O pacote sai como
prévia, com a arte pendente: só o dono a revisa (`pfe revisar <build> --veredito ... --nota ... --por ...`), e só o
build aprovado sai com `pfe exportar <build> --publicar`.
