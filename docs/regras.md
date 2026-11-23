# Regras da engine

A fonte única das regras que não viraram checagem. O `CLAUDE.md`, o `AGENTS.md` e a skill citam este arquivo e não
repetem nada dele. O que dá para checar é teste, não linha aqui.

## O que a engine é

- A engine é a mão de uma IA para pixel art: a IA descreve o asset em dados, e a engine desenha, confere e exporta.
- O agente do jogo pede (criar, completar, corrigir) e monta as cenas; a engine faz a autoria e entrega, sem montar
  cena nem jogo.

## Desenho

- Forma antes de cor: a entrega fraca se corrige na construção (peças, medidas, primitivas), não trocando tons.
- Referência concreta antes de desenhar: a ficha cita a fonte, as medidas reais e o que dá vida à coisa; ela informa
  os dados e nunca vira recorte 2D.
- Anatomia contra a referência: se o rig não faz a pose, diga antes de desenhar.
- Criação, não reuso: um asset novo nasce da ficha dele, não de um exemplo esticado.
- O tamanho vem dos metros reais na escala do mundo, nunca do canvas.
- A solução se mede no pixel final do sprite e no custo, não num render 3D sofisticado.

## Limites e correções

- Pare em vez de piorar: se um limite obriga a perder qualidade visível, corrija a causa no motor (a peça, o
  limite), nunca o desenho, e mostre o antes e o depois.
- Treino corrige o motor: a falha que um asset expõe vira capacidade geral, provada por fixture sintética com
  controle negativo; nunca remendo no asset, e o asset de treino não fica no repositório.
- Um fator por vez, com o antes e o depois lado a lado antes de declarar melhoria.
- A correção só conta quando a engine recusa o jeito antigo ou quando ele não existe mais.

## Arte e aprovação

- Só o dono aprova arte: o `art_review` muda só por revisão humana registrada.
- Ninguém aprova o próprio trabalho: o pronto vem de uma prova feita por quem não escreveu o código.

## Trabalho

- Só uma sessão escreve neste repositório por vez.
- Imagem: leia primeiro os números; a prancha é o recorte no tamanho real, ampliado no máximo 4×.
- A decisão que o plano não fixa vai em uma linha em `docs/decisoes.md`; o porquê vai no commit.
- O acervo de trabalho e os builds ficam fora do git.
