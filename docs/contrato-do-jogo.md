# O contrato do jogo — `pfe-jogo/1`

O que o jogo recebe da engine: a pasta `exports/<build>/` do acervo, com o `atlas.json` e as páginas PNG (RGBA, alfa
0 ou 255). O formato é neutro; o adaptador de um motor de jogo lê este contrato.

## `atlas.json`

| Campo | O que é |
|---|---|
| `contract` | `"pfe-jogo/1"`. O leitor recusa versão que não conhece. |
| `asset` | `{id, revision}`. |
| `engine` | a versão da engine que fez o build (o build é preso a ela). |
| `build_id` | o sha256 da composição, do estilo, da versão e dos pixels: o mesmo id é sempre o mesmo desenho. |
| `status` | `preview` ou `release_candidate` (aprovado pelo dono). O jogo não publica `preview`. |
| `art_review` | `pending`, `approved` ou `changes_requested`: só a revisão do dono muda. |
| `directions` | as direções do asset: o estático tem a vista do jogo; quem anda ou vira tem as 8. |
| `pages` | as páginas PNG (`image`, `size`). |
| `frames[]` | um por quadro, nome `<asset>/<clip>/<direção>/<índice>`. |
| `clips[]` | uma sequência por clip e direção: os nomes dos quadros em ordem, `loop`, `duration_ms`, `root_deltas_q8`. |

Cada quadro: `page`, `rect` `[x, y, w, h]` na página; `source_size` (o canvas) e `source_rect` (onde o recorte cai
nele); `pivot_px` (o pé do asset: o jogo põe esse pixel na posição do mundo); `landmarks` em px do canvas
(`sort_front` é a linha de base da frente, a ordem de desenho na cena; o ponto de uma peça oculta na vista continua
no quadro); `duration_ms` e `events`.

## A câmera e a escala

Todo quadro sai na mesma câmera, o 3/4 oblíquo (o contrato completo está em `docs/coordenadas.md`), e na mesma escala
do mundo, 32,73 px por metro:

| No mundo | Na tela |
|---|---|
| 1 m de lado (x) | 32,7 px na horizontal |
| 1 m de chão para a frente (y) | 19,6 px para baixo (o chão aparece a 0,6) |
| 1 m de altura (z) | 23,1 px para cima (a altura aparece a cos 45°) |

Um tile de chão de 1 m × 1 m ocupa 32,7 × 19,6 px: o chão e os tiles do jogo usam a mesma proporção. A luz vem de cima
e da esquerda, e a sombra no chão já vem no quadro, à direita da base (0,71 px por px de altura). A câmera mudou de
0,35 para 0,6 no motor 0.2.0: não misture na mesma cena pacotes de `engine` 0.1.x com os de 0.2.x.

## Ler

1. Confira `contract`. 2. Abra as páginas. 3. Para cada quadro, recorte `rect` da página e cole em `source_rect` de
um canvas `source_size` transparente. 4. Toque cada sequência de `clips` com a duração de cada quadro. O leitor de
referência é `src/pixel_forge/export/pacote.py` (`ler_pacote`); `pfe exportar <build> --verificar` confere o pacote
contra o build. Mudança incompatível do formato = `pfe-jogo/2`; campo novo opcional não muda a versão.
