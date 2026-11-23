# Estado da engine corrigida

Plano: `docs/plano.md` (cópia do plano de 2026-11-23). Decisões: `docs/decisoes.md`. Regras: `docs/regras.md`.
Oráculo: o `pixel-engine` em 3df5fe42 (motor 2.3.0), só leitura (I7: `git status` limpo no início e agora).

## Feito

**N0 — o esqueleto com as travas.** Repositório novo (`main`, sem remoto), `uv`, ruff (F, ARG, ERA, C901, PLR0912/0913/
0915, sem lista de exceções), mypy estrito em `src`, `tests` e `scripts`, e `scripts/check.py`. As travas, verdes no
repositório vazio e cada uma com controle negativo (`tests/travas/`):
- código limpo (I10): código morto por referência, nenhuma marca de silêncio, a config sem exceção;
- camadas: render, rig e export não importam desenho nem movimento; núcleo e contratos não importam nada acima;
- nada de asset em `src/` (I4) e nada de treino nem acervo rastreado (I2);
- teto de 400 linhas por módulo e de 1 500 linhas em `docs/`;
- uma fonte de regras (I6): `CLAUDE.md`, `AGENTS.md` e a skill citam `docs/regras.md`, sem repetir; o espelho da skill.
O oráculo (`scripts/oraculo.py`): `git archive` do `pixel-engine` numa pasta temporária, com ambiente próprio.

**N1 — o núcleo por demanda.** Três fixtures sintéticas (`tests/fixtures/oraculo/`: o bloco com a bola e a caixa, o
tronco de revolução, o telhado de faces pela normal), 7 vistas, **iguais pixel a pixel ao oráculo**, com controle
negativo. Portados, já no padrão I10: q8 e Taylor, IR e estilo, FK de repouso, a câmera oblíqua, a projeção (leque,
revolução, elipse), o raster (z-buffer, tons, textura, sombra entre peças e no chão, contornos, pixel-perfect,
limpeza de cor isolada), o build e o export `pfe-jogo/1` com o leitor do jogo e o `--verificar` (o roundtrip).

**N2 — a composição única, o kit e o humano.** O formato único (o da v2, sem versão nem migração),
as recusas antes de montar, o prop com a sombra de contato, as pilhas, as vistas 1/2/4 e o canvas pelo tamanho; 18
peças vigentes (madeira, pedra, telhados, carpintaria, vãos, formas) e 6 de flora (o tronco sólido, os galhos finos e
grossos com a âncora das pontas, o `pontilhado`, os `galhos_em_pena`, as cortinas): **as 72 variações iguais ao
oráculo** na mesma entrada, e 3 composições sintéticas (a árvore no balanço, o abrigo, o marco de 4 vistas) também,
fora a sombra das vistas E/N/W (mudança intencional). O estilo base com a paleta por função e os verdes de folhosa;
`pfe build <composição>` e `pfe catalogo`.
O humano: o rig `humano` por papéis, o IK de duas juntas, o parado e a passada com IK, o corpo e as roupas
(jaqueta, faixa, calça, olhos, cabelo, chapéu, bolsa, sandália, tabi, e as novas saia e lenço): **o vestido nas 8
direções, parado e andando, 176 quadros iguais ao oráculo**; as 102 variações do kit (com as roupas) também. O porte
por categoria, recusado no build com o porte típico na dica.

## Números

| Medida | N0 | N1 | N2a | N2b | N2c |
|---|---|---|---|---|---|
| Linhas em `src/` | 1 | 2 431 | 4 833 | 5 613 | 7 228 |
| Arquivos rastreados | 24 | 72 | 101 | 111 | 127 |
| `check.py` completo | 9 s, 18 testes | 9 s, 26 testes | 10 s, 83 testes | 12 s, 108 testes | 17 s, 182 testes |

## Próximo passo

**N2, o resto:** o balanço e o giro do prop como clipe; o quadrúpede (o canino) com o rig por papéis e a passada;
a corrida e a ação por acessório; o inventário das lições. Depois o **N3**: a CLI mínima e o acervo.
