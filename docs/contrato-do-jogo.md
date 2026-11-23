# O contrato do jogo — `pfe-jogo/1`

O que o jogo recebe da engine: a pasta `exports/<build>/` do acervo, com o `atlas.json` e as páginas PNG (RGBA, alfa
0 ou 255). O formato é neutro; o adaptador de um motor de jogo lê este contrato.

## `atlas.json`

| Campo | O que é |
|---|---|
| `contract` | `"pfe-jogo/1"`. O leitor recusa versão que não conhece. |
| `asset` | `{id, revision}`. |
| `engine` | a versão da engine que fez o build (o build é preso a ela). |
| `build_id` | o sha256 da entrada do build. |
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

## Ler

1. Confira `contract`. 2. Abra as páginas. 3. Para cada quadro, recorte `rect` da página e cole em `source_rect` de
um canvas `source_size` transparente. 4. Toque cada sequência de `clips` com a duração de cada quadro. O leitor de
referência é `src/pixel_forge/export/pacote.py` (`ler_pacote`); `pfe exportar <build> --verificar` confere o pacote
contra o build. Mudança incompatível do formato = `pfe-jogo/2`; campo novo opcional não muda a versão.
