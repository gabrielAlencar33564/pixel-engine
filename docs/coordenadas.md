# Coordenadas e convenções numéricas

| Grandeza | No documento | Interno |
|---|---|---|
| Posição | inteiro q8 (256 = 1 px); a composição escreve em metros | POS = q8 << 12 (1/2²⁰ px) |
| Ângulo | inteiro em miligraus | seno e cosseno Q30 por série de Taylor inteira |
| Tempo | inteiro em ms | — |
| Cor | RGBA 8 bits, alfa 0 ou 255 | índice de paleta |

## Eixos

- Mundo e corpo: **+X = lado anatômico esquerdo**, **+Y = frente (sul)**, **+Z = altura**.
- Tela: +u direita, +v baixo; o pixel (x, y) cobre `[256x, 256x+256) × [256y, 256y+256)` em q8.
- A origem do corpo cai no **centro** do pixel `pivot_px`.

## A câmera: o 3/4 oblíquo, a única

Para a direção de azimute `a` (S = 0°, SW = 45°, W = 90°, ... de 45 em 45, SE = 315°):

```text
x' = x·cos a − y·sin a        y' = x·sin a + y·cos a
u  = pivô_u + x'              v  = pivô_v + y'·0,6 − z·cos 45°
profundidade = y'·cos 45° + z·sin 45°     (maior = mais perto da câmera)
```

O objeto é visto de frente e de cima (o chão e o topo a 0,6; eram 0,35 no `pixel-engine`), com a altura a cos 45°. Na S, a mão esquerda fica à
direita da tela; na W, a frente aponta para a esquerda da tela; na E, para a direita.

## Arredondamento e ordem

`floor(valor + 0,5)` em aritmética inteira. A ordem é: geometria local → rotação local → translação → ancestrais →
projeção → quantização; nada é arredondado para pixel antes da projeção. A profundidade por pixel é quantizada a
1/16 px antes de qualquer comparação.

## Raiz e movimento da raiz

O x e o y da trajetória da raiz saem do render e vão ao export como `root_deltas_q8` por quadro; o z é desenhado.

## Rasterização

Amostra no centro do pixel. Elipse com a fronteira inclusiva; polígono por scanline par-ímpar com as arestas
semiabertas `y0 <= yc < y1` e o intervalo horizontal `[x_esq, x_dir)`: a borda compartilhada tem um dono só.
