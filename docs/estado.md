# Estado da engine corrigida

Plano, decisões e regras: `docs/plano.md`, `decisoes.md`, `regras.md`. Oráculo: o clone local `pixel-engine` em 3df5fe42.
Remoto: `gabrielAlencar33564/pixel-engine`, cuja `main` é esta engine desde 2026-11-23. **N0 a N5 feitos.**

## O que a engine tem

- **Núcleo** igual ao `pixel-engine` pixel a pixel (oráculo por `git archive`): q8, IR, FK/IK de 2 e de N segmentos,
  a câmera 3/4 oblíqua (profundidade 0,6, os dois), a projeção, o raster e o pacote `pfe-jogo/1`. Motor 0.2.0.
- **Kit vigente** (37 peças): construção, telhados, carpintaria, vãos, formas, flora (`pontilhado`, galhos, cortinas,
  pena), o humano com as roupas (e as novas saia e lenço), o corpo canino. Composição num formato só, com o porte.
- **Movimento:** o parado e a passada do humano, o parado e o passo do quadrúpede, o balanço e o giro do prop.
- **CLI** `pfe` no acervo (`~/.pixel-forge/acervo`), sem projeto: `previa`, `checar`, `build`, `exportar`,
  `olhar`, `catalogo`, `conjunto`, `revisar`, `atualizar`. **Skill única** com o formulário de pedido e 4 exemplos.

## Números contra a linha de base

| Medida | `pixel-engine` | engine nova |
|---|---|---|
| Linhas em `src/` | 32 701 | 8 259 |
| Arquivos rastreados | 9 672 | 151 |
| Suíte completa (`check.py`) | 5 min 13 s, 918 testes | 29 s, 226 testes |
| Carvalho: relógio do agente | ~9 min | 3 min 49 s |
| Carvalho: máquina | ~2 min 57 s (prévia 5 s, novo 2 min 27 s, build 23 s, export 2 s) | 27 s em 11 chamadas |
| Poço / camponesa: máquina | — | 17 s / 25 s, 11 chamadas cada |
| Recusa sem dica | 1 | 0 |

## A prova de fora

- **Rodada 1 (falhou):** o carvalho parou em tetos internos (canvas de 256 px, 64 vértices no galho) que vazavam como
  erro da IR com dica genérica; havia falhas caladas (traço com parte inexistente, nó vazio, camada interna cobrindo o
  nó seguinte). Poço e camponesa exportaram. Corrigido na causa (8b29bd8); acervo dela em `~/.pixel-forge/acervo-rodada1`.
- **Rodada 2 (passou):** os 3 exports verificados; o carvalho com `pontilhado`; vistas 1, 1 e 8; uma recusa (`TRACO`,
  com dica); nada piorado para passar; estático bem abaixo de 1 min de máquina. A dica do traço apontava para a prévia
  que a recusava: agora lista as partes, e o catálogo diz as partes de cada peça.
- **Câmera a 0,6 (2026-11-23):** reconstruídos e verificados: `carvalho_roble.r1.56813c99a932`,
  `poco_pedra.r1.88cd1cdde9ff`, `camponesa.r1.98f3c0ef2a49` e, das fixtures, `abrigo.r1.a1d0577ebd7a` e
  `marco.r1.41ef53825299` (os de 0,35 ficam nos ids da rodada 2). Pranchas em `~/.pixel-forge/acervo/olhar/`.

## Mudanças intencionais de pixel (pranchas em `~/.pixel-forge/acervo/pranchas/mudancas/`, antes em cima)

1. A paleta por função e os verdes de folhosa (os materiais de cena saíram do estilo).
2. A sombra de contato reescalada também nas vistas E, N e W (fica 3:1 na tela em toda vista).
3. O canvas inclui a sombra que o asset projeta no chão (o antigo a cortava calado); a luz é da câmera.
4. A pegada do quadrúpede gira com o corpo (a antiga, de lado, saía 2× mais longa e cortada).
5. A câmera mais de cima: a profundidade de 0,35 para 0,6 (escolha do dono; a altura segue a cos 45°).
6. As faces da peça nos degraus da camada do nó (a 0,6, a pedra da parede do abrigo cobria a beira do telhado).
Além delas: a saia mede a barra pelo quadril; a camada do nó separa os nós; o id do build leva os pixels.

## O que não veio ou não passou

- A corrida, o galope, a ação por acessório e a bateria canina (sentar, deitar, latir, uivar): nenhum pedido os usa.
- O que a rodada 2 apontou sem recusa: a copa do `pontilhado` não faz a linha reta de pasto; a palha não envelhece
  para o cinza; o `olhar` do humano é grande e sem rótulos; a prévia não avisa parte escondida atrás de outra.
- A camponesa: a saia larga em 3/4 lê como saco; o andar (igual ao antigo) gira o tronco nas diagonais.

## Espera o dono

A revisão artística dos builds a 0,6 e das mudanças intencionais (`pfe revisar <build> --veredito ...`). Nenhuma
arte foi aprovada pela engine nem por mim; os pacotes saem como prévia (`art_review: pending`).
