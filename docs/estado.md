# Estado da engine corrigida

Entrada: `README.md`. Plano, decisões e regras: `docs/plano.md`, `decisoes.md`, `regras.md`. **N0 a N5 feitos.**
Remoto: `gabrielAlencar33564/pixel-engine`, só a `main` (esta engine); os commits desde `20004c3` (2026-11-25) ainda
não foram enviados. Oráculo: o clone local `pixel-engine`.

## O que a engine tem

- **Núcleo** igual ao `pixel-engine` pixel a pixel (oráculo por `git archive`): q8, IR, FK/IK de 2 e de N segmentos,
  a câmera 3/4 oblíqua (profundidade 0,6, os dois), a projeção, o raster e o pacote `pfe-jogo/1`. Motor 0.2.0.
- **Kit vigente** (40 peças): construção, telhados, carpintaria, vãos, formas, a flora em sete construções
  (`tronco_em_pe`, `galhos`, `copa`, `copa_aberta`, `copa_conica`, `touceira`, `salpico`), o humano com as roupas (e as
  novas saia e lenço) e a espada, o penedo, o corpo canino. Composição num formato só, com o porte.
- **Movimento:** o parado, a passada e o golpe de espada (sem laço) do humano, o parado e o passo do quadrúpede, o
  balanço e o giro do prop.
- **CLI** `pfe` no acervo (`~/.pixel-forge/acervo`), sem projeto: `previa`, `radiografia`, `checar`, `build`,
  `critica`, `exportar`, `olhar`, `catalogo`, `conjunto`, `revisar`, `atualizar`. **Skill única** (em inglês) com o
  formulário de pedido e 5 exemplos. A planta só sai com a crítica: medida, comparada com as irmãs do acervo e
  revisada por outro agente.
- **A planta pelos traços:** o campo `planta` (o hábito, a altura, a largura, a folha, a idade) de onde a engine
  deriva o tronco, os galhos e a copa; e a recusa `LIGACAO` do que fica no ar (o galho nasce do eixo do tronco).
  A ligação é da estrutura, conferida na geometria: o pixel não se junta, e as lâminas do capim ficam separadas.
  Na última prova de fora (dez plantas só pela skill, 2026-11-25) nove saíram pelos traços com uma prévia cada;
  o revisor de fora passou cinco e devolveu cinco (a samambaia, o chorão, a oliveira, os dois arbustos). Das
  cinco só a samambaia foi mexida (`73f4488`), e o dono devolveu a cor dela (em "O que não veio ou não passou").

## Números contra a linha de base

| Medida | `pixel-engine` | engine nova |
|---|---|---|
| Linhas de Python em `src/` | 32 701 | 10 389 (8 273 antes da flora) |
| Arquivos rastreados | 9 672 | 175 |
| Suíte completa (`check.py`) | 5 min 13 s, 918 testes | 1 min 14 s a 1 min 35 s, 513 testes (2026-11-28) |
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

- **Flora variada (2026-11-25):** um agente sem contexto fez dez plantas de uma cena pela skill, e outros três, um
  por rodada, as revisaram pela crítica. Passaram 2, 4 e 7 das 10; cada rodada devolveu defeitos de motor, corrigidos
  na causa (em `docs/decisoes.md`). As três que ficaram (a samambaia, o arbusto baixo e claro, o choupo) passaram
  em mais três rodadas, depois de outras correções de motor. Os 10 pacotes estão em
  `~/.pixel-forge/acervo-prova-flora`, com os pareceres em `criticas/` e `revisao/`; os 7 primeiros são de builds
  do motor de então (refeitos agora, dão outro desenho e pedem a crítica de novo).

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
15. A cabeça do humano é um ovo: uma parte só, sem face, queixo nem nariz (decisão do dono: a figura é para a
    câmera de cima, não a anatomia). Os olhos no meio do ovo, o chapéu um pouco para trás. Na `15b`, de perto.
16. Os membros em formas simples: as juntas rentes, a perna em tubo, o pé curto e baixo, a mão da largura do
    punho, cada membro numa massa. Na `16b`, de perto.
17. O tronco é um bloco: o quadril no mesmo grupo e na mesma massa do tronco (a linha em volta dele lia como
    sunga), a cintura e o quadril quase da largura do peito.
18. A sombra no chão é só a projetada: a mancha de contato saiu (o campo `sombra` da composição é recusado), o
    tronco e a copa pontilhada passam a se lançar no chão, e a limpeza não conta o chão como figura. A 2 e a 4
    (a sombra de contato) ficam sem objeto. Na `18`, banco, abrigo, árvore, humano e canino.
19. A flora em volumes: a copa da folhosa em tufos (`copa`), a da conífera em andares (`copa_conica`) e os galhos
    roliços em volta do tronco (`galhos`), nas 4 vistas, com a sombra da copa no chão. Saíram o pontilhado, a
    pena, as cortinas e os galhos chapados. Na `19`, a árvore de exemplo e o carvalho da prova; na `19b` e na
    `19c`, as peças.
20. O tronco com forma de tronco: o pé que abre, o fuste que engrossa e afina, a curva, as raízes e os nós, e a
    casca com veio (`casca_sulcada`, `casca_anelada`). Na `20`, as três variações; na `20b`, nas árvores.
21. A flora variada: a copa em lóbulos desencontrados numa massa de luz só (com a gota, o guarda-sol e os ramos
    que caem), a copa aberta nos galhos, a conífera de saias recortadas, a touceira e o salpico. Na `21`, as peças,
    antes em cima; na `21b`, as construções novas; na `21c`, as plantas de prova lado a lado.
Além delas: a saia mede a barra pelo quadril; a camada do nó separa os nós; o id do build leva os pixels.

## O que não veio ou não passou

- A corrida, o galope, a ação por acessório e a bateria canina (sentar, deitar, latir, uivar): nenhum pedido os usa.
- O que a rodada 2 apontou sem recusa: a copa (hoje em tufos) não faz a linha reta de pasto; a palha não envelhece
  para o cinza; o `olhar` sai sem rótulos (a skill diz a ordem das fileiras). A prévia já avisa a parte escondida.
- A camponesa: a saia larga em 3/4 lê como saco; o andar (igual ao antigo) gira o tronco nas diagonais.
- O modelo do humano não tem mais medida fora da faixa na radiografia (mudanças 10 a 12), mas as faixas são
  aproximações e a arte espera o dono. A radiografia não vê o que só aparece na câmera do jogo (a face estreita
  da mudança 12 passava nela): o formato na tela é medido nos testes do humano. O que sobra: o chapéu de aba
  acima de ~200 % cobre os olhos; da análise de 2026-11-25 sobra a barra da calça solta e da saia, que
  fecha arredondada (em `docs/decisoes.md`); as
  mudanças 7 a 9 ajustaram a pose sobre o modelo antigo e não foram reafinadas no novo.
- O humano na tela: no andar em diagonal as mãos a até 21 px uma da outra; o perfil parado estreito (12 px, um
  braço cobrindo o outro); o andar em S e N com o balanço comprimido pela câmera.
- A flora em volumes (mudança 19): as bordas do tufo e da saia são lisas, a copa pendente é um domo com ramos
  caindo, e a sombra do elipsoide no chão é aproximada (em `docs/decisoes.md`). O carvalho do acervo foi
  refeito no modelo novo (`carvalho_roble.r3.3c42542d9f2a`, na `19`) e depois com o tronco novo
  (`carvalho_roble.r4.89fc47c82e08`, na `20b`); a `r1` e a `r2` usam as peças que saíram e não se leem mais. Os braços dele não leem como braços à mostra: somem na copa, e a linha de pasto não tem peça.
- O tronco (mudança 20): o perfil irregular não se lê abaixo de 40 cm, a curva é só de lado, e não há forquilha
  nem toco cortado.
- A flora variada (mudança 21): o tom das lâminas vale só para a vista S; o cinzento da paleta puxa para o lilás; a
  sombra da copa alta sai em manchas; a crítica não mede o brócolis (fica na pergunta de quem revisa) e compara só
  a silhueta. As plantas antigas do acervo não foram refeitas: as de `copa` dão outro desenho
  e as de `copa_conica` com `saia` não se leem mais (em `docs/decisoes.md`).
- A samambaia (`73f4488`, 2026-11-26): a fronde ganhou o corpo, o contorno partido e o lado claro, mas foi ao verde
  escuro da folhosa, e o dono a achou inferior na cor (prefere o tom claro de antes). Faltam a cor clara de volta,
  os cortes em cada braço da folha (os folíolos, pedido dele) e a prancha numerada em `mudancas/` (as de comparação
  estão em `pranchas/regressao_opus/`).
- As outras quatro que o revisor de fora devolveu (o chorão, a oliveira, o arbusto de frutos, o arbusto claro) não
  foram mexidas: o parecer é hipótese, e o desenho espera o dono ver a prancha e dizer se concorda com o defeito.

## Espera o dono

A revisão artística dos builds a 0,6 e das mudanças intencionais (`pfe revisar <build> --veredito ...`), com a
flora em volumes entre elas. Nenhuma
arte foi aprovada pela engine nem por mim; os pacotes saem como prévia (`art_review: pending`). A camponesa do acervo
(`98f3c0ef2a49`) é a do humano antigo: com as mudanças 7 a 18 ela ainda não foi reconstruída. Da flora, espera o
olho dele nas quatro plantas devolvidas, antes de qualquer correção.
