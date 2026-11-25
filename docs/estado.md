# Estado da engine corrigida

Entrada: `README.md`. Plano, decisões e regras: `docs/plano.md`, `decisoes.md`, `regras.md`. **N0 a N5 feitos.**
Remoto: `gabrielAlencar33564/pixel-engine`, só a `main` (esta engine), em dia. Oráculo: o clone local `pixel-engine`.

## O que a engine tem

- **Núcleo** igual ao `pixel-engine` pixel a pixel (oráculo por `git archive`): q8, IR, FK/IK de 2 e de N segmentos,
  a câmera 3/4 oblíqua (profundidade 0,6, os dois), a projeção, o raster e o pacote `pfe-jogo/1`. Motor 0.2.0.
- **Kit vigente** (37 peças): construção, telhados, carpintaria, vãos, formas, flora (`pontilhado`, galhos, cortinas,
  pena), o humano com as roupas (e as novas saia e lenço), o corpo canino. Composição num formato só, com o porte.
- **Movimento:** o parado e a passada do humano, o parado e o passo do quadrúpede, o balanço e o giro do prop.
- **CLI** `pfe` no acervo (`~/.pixel-forge/acervo`), sem projeto: `previa`, `radiografia`, `checar`, `build`,
  `exportar`, `olhar`, `catalogo`, `conjunto`, `revisar`, `atualizar`. **Skill única** com o formulário de pedido e 4 exemplos.

## Números contra a linha de base

| Medida | `pixel-engine` | engine nova |
|---|---|---|
| Linhas em `src/` | 32 701 | 8 273 |
| Arquivos rastreados | 9 672 | 152 |
| Suíte completa (`check.py`) | 5 min 13 s, 918 testes | ~40 s, 279 testes |
| Carvalho: relógio do agente | ~9 min | 3 min 49 s |
| Carvalho: máquina | ~2 min 57 s (prévia 5 s, novo 2 min 27 s, build 23 s, export 2 s) | 27 s em 11 chamadas |
| Poço / camponesa: máquina | — | 17 s / 25 s, 11 chamadas cada |
| Recusa sem dica | 1 | 0 |

## A prova de fora

- **Rodada 1 (falhou):** o carvalho parou em tetos internos (canvas de 256 px, 64 vértices no galho) que vazavam como
  erro da IR com dica genérica; havia falhas caladas (traço com parte inexistente, nó vazio, camada interna cobrindo o
  nó seguinte). Poço e camponesa exportaram. Corrigido na causa (8b29bd8); acervo em `~/.pixel-forge/acervo-rodada1`.
- **Rodada 2 (passou):** os 3 exports verificados; o carvalho com `pontilhado`; vistas 1, 1 e 8; uma recusa (`TRACO`,
  com dica); nada piorado para passar; estático bem abaixo de 1 min de máquina. A dica do traço apontava para a prévia
  que a recusava: agora lista as partes, e o catálogo diz as partes de cada peça.
- **Câmera a 0,6 (2026-11-23):** reconstruídos e verificados: `carvalho_roble.r1.56813c99a932`,
  `poco_pedra.r1.88cd1cdde9ff`, `camponesa.r1.98f3c0ef2a49` e, das fixtures, `abrigo.r1.a1d0577ebd7a` e
  `marco.r1.41ef53825299` (os de 0,35 ficam nos ids da rodada 2). Pranchas no acervo: `olhar/` e `pranchas/revisao/`.

## Mudanças intencionais de pixel (pranchas em `~/.pixel-forge/acervo/pranchas/mudancas/`, antes em cima)

1. A paleta por função e os verdes de folhosa (os materiais de cena saíram do estilo).
2. A sombra de contato reescalada também nas vistas E, N e W (fica 3:1 na tela em toda vista).
3. O canvas inclui a sombra que o asset projeta no chão (o antigo a cortava calado); a luz é da câmera.
4. A pegada do quadrúpede gira com o corpo (a antiga, de lado, saía 2× mais longa e cortada).
5. A câmera mais de cima: a profundidade de 0,35 para 0,6 (escolha do dono; a altura segue a cos 45°).
6. As faces da peça nos degraus da camada do nó (a 0,6, a pedra da parede do abrigo cobria a beira do telhado).
7. O braço do humano no repouso a 6° (eram 15°): as mãos caem junto do corpo. Na `7b`, as alternativas de 4° e 8°.
8. O balanço do braço no andar a 16° no ombro e no cotovelo (eram 23° e 26°): de perfil o braço não estica mais para
   a frente. Na `8b`, as alternativas de 18° e de 12° e 10°.
9. Os pés desencontrados no parado do humano (5 cm para a frente e para trás): de perfil os dois pés leem.
10. O tronco e os ombros do humano: a junta do ombro 3,5 % da estatura mais baixa, a linha do ombro do pescoço ao
    braço, o peito e a cintura sem o estrangulamento, o pescoço mais largo, o braço a 0,90 e a jaqueta com a
    ombreira. Na `10r`, a radiografia do corpo, antes em cima.
11. O peito do humano em cunha, numa massa só com a cintura (era uma bola com a sua linha e a sua sombra, e lia
    como busto), no corpo e na jaqueta. Na `11r`, a radiografia, antes em cima.
12. A cabeça e os olhos do humano: a face larga e rente à testa, o nariz, os olhos de 1 px a 58 % da cabeça e sem
    contorno, o cabelo e o lenço como cascas sobre o crânio. Na `12b`, as cabeças de perto (8×); na `12r`, a
    radiografia.
13. O formato da cabeça e o cabelo: a face da largura do crânio na tela, o queixo rente à testa, o nariz uma
    fileira sob o olho e uma mecha de cabelo em cada têmpora. Na `13b`, as cabeças de perto (8×).
14. A abertura das pernas do humano: os pés sob as juntas do quadril (eram 26 cm um do outro, mais que o quadril).
    Na `14b`, o andar de frente e de perfil.
Além delas: a saia mede a barra pelo quadril; a camada do nó separa os nós; o id do build leva os pixels.

## O que não veio ou não passou

- A corrida, o galope, a ação por acessório e a bateria canina (sentar, deitar, latir, uivar): nenhum pedido os usa.
- O que a rodada 2 apontou sem recusa: a copa do `pontilhado` não faz a linha reta de pasto; a palha não envelhece
  para o cinza; o `olhar` sai sem rótulos (a skill diz a ordem das fileiras). A prévia já avisa a parte escondida.
- A camponesa: a saia larga em 3/4 lê como saco; o andar (igual ao antigo) gira o tronco nas diagonais.
- O modelo do humano não tem mais medida fora da faixa na radiografia (mudanças 10 a 12), mas as faixas são
  aproximações e a arte espera o dono. A radiografia não vê o que só aparece na câmera do jogo (a face estreita
  da mudança 12 passava nela): o formato na tela é medido nos testes do humano. O que sobra: o chapéu de aba
  acima de ~150 % cobre os olhos; do quadril para baixo, a análise de 2026-11-25 achou a esfera saliente no joelho
  e no tornozelo, a canela sem panturrilha, o pé alto, a cintura fina para o quadril e a barra da calça solta e
  da saia fechadas (em `docs/decisoes.md`); as
  mudanças 7 a 9 ajustaram a pose sobre o modelo antigo e não foram reafinadas no novo.
- O humano na tela: no andar em diagonal as mãos a até 21 px uma da outra; o perfil parado estreito (12 px, um
  braço cobrindo o outro); o andar em S e N com o balanço comprimido pela câmera.

## Espera o dono

A revisão artística dos builds a 0,6 e das mudanças intencionais (`pfe revisar <build> --veredito ...`). Nenhuma
arte foi aprovada pela engine nem por mim; os pacotes saem como prévia (`art_review: pending`). A camponesa do acervo
(`98f3c0ef2a49`) é a do humano antigo: com as mudanças 7 a 14 ela ainda não foi reconstruída.
