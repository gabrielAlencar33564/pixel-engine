# Pixel Asset Engine

A mão de uma IA para pixel art de jogo. O agente descreve o asset em dados (a **composição**, um JSON com as peças do
kit e as medidas reais em metros), e a engine desenha, confere e exporta o asset completo: todas as vistas, os clipes de
movimento e o pacote que o jogo lê. A engine não constrói o jogo: ela cria, completa e corrige os assets que ele pede.

Pacote Python `pixel_forge`, CLI `pfe`, versão 0.2.0.

## O que ela faz

- **Tipos de asset:** prop (objeto, estrutura, casa, árvore, arbusto), humano e quadrúpede, cada um montado com as peças
  do kit (construção, telhados, carpintaria, vãos, formas, flora, o corpo humano com as roupas, o corpo canino).
- **Câmera:** o 3/4 oblíquo de RPG, uma só para todo asset: a altura a cos 45° e o chão e o topo a 0,6; a luz vem de
  cima e da esquerda. O contrato completo está em [`docs/coordenadas.md`](docs/coordenadas.md).
- **Escala:** o tamanho sai dos metros (o humano de 1,65 m tem ~44 px na tela), e o porte é conferido pela categoria.
- **Vistas e movimento:** o estático sai na vista S (2 ou 4 cardinais só se o pedido disser); quem anda sai nas 8
  direções, em todos os clipes (o humano parado e andando, o quadrúpede parado e no passo); o prop balança ou gira.
- **Recusas com dica:** o que a engine não desenha direito ela recusa com o código, a medida, a dica e o caminho na
  composição, na prévia e no build pelo mesmo caminho.
- **Revisão humana:** o pacote sai como prévia, com a arte pendente; só sai publicado depois da revisão do dono.

## Instalação

Python 3.12 e [uv](https://docs.astral.sh/uv/):

```bash
uv sync
uv run pfe --help
```

Sem o uv: `pip install .` num ambiente virtual.

## Uso

Os assets ficam no acervo, `~/.pixel-forge/acervo` (ou `--acervo`, ou a variável `PFE_ACERVO`). O caminho de um asset:

```bash
uv run pfe previa  composicoes/poco.r1.json --json   # o repouso de cada vista, as recusas, o que não se vê e a prancha
uv run pfe radiografia composicoes/poco.r1.json --json   # o modelo ampliado, sem a câmera, e as medidas do corpo
uv run pfe checar  composicoes/poco.r1.json --json   # todos os quadros conferidos, sem gravar
uv run pfe build   composicoes/poco.r1.json --json   # os quadros no acervo; devolve o build
uv run pfe critica  <build> --json                   # a planta medida e comparada com as irmãs; o parecer de outro agente
uv run pfe exportar <build> --json                   # o pacote do jogo (pfe-jogo/1: atlas e JSON)
uv run pfe exportar <build> --verificar --json       # relê o pacote e confere contra o build
uv run pfe olhar    <build> --json                   # a prancha de todos os quadros e os números
```

Também há `catalogo` (o resumo das famílias do kit e, das famílias pedidas, os argumentos e a prancha de cada
peça), `conjunto` (assets lado a lado com o humano de régua), `atualizar` (o desenho mudado vira a revisão seguinte: a identidade é imutável) e `revisar` (o dono
registra o veredito; só o build aprovado sai com `exportar --publicar`). O formato do pacote está em
[`docs/contrato-do-jogo.md`](docs/contrato-do-jogo.md).

## Para agentes

- O passo a passo, o formato da composição e a tabela de porte estão na skill
  [`.claude/skills/pixel-asset-engine/SKILL.md`](.claude/skills/pixel-asset-engine/SKILL.md) (espelho em `.agents/`).
- As regras de desenho e de trabalho são uma fonte só: [`docs/regras.md`](docs/regras.md).
- O agente do jogo pede um asset pelo formulário [`docs/pedido.md`](docs/pedido.md).
- Há cinco exemplos de composição em `tests/fixtures/exemplos/` (um banco, uma árvore folhosa, uma árvore de galhos
  abertos, um viajante, um canino).

## Desenvolvimento

```bash
uv run python scripts/check.py          # ruff, mypy estrito e a suíte (~30 s); verde antes de cada commit
uv run python scripts/check.py --fast   # o ciclo rápido
```

- `src/pixel_forge/`: `contracts` (os modelos), `core` (ponto fixo q8, recusas), `design` (a composição e o kit),
  `rig` e `motion` (esqueleto, IK e clipes), `views` e `raster` (a câmera e o desenho), `quality`, `export`,
  `application` (os comandos) e `dados` (o estilo base, os rigs e as receitas).
- `tests/travas/`: as travas do código limpo (tetos de tamanho, sem código morto, sem treino, regras numa fonte só).
- `scripts/oraculo.py`: o oráculo de pixel. A engine nasceu da poda do `pixel-engine` antigo e desenha igual a ele pixel
  a pixel, salvo as mudanças intencionais registradas em [`docs/decisoes.md`](docs/decisoes.md). Regerar os esperados
  pede um clone local do motor antigo (`PFE_ORACULO_REPO`); os testes usam os esperados gravados.
- `scripts/skill.py`: gera da skill a tabela de porte, o espelho e o `docs/pedido.md`; um teste confere que estão em
  dia.

## Estado

O que a engine tem, os números e o que espera revisão estão em [`docs/estado.md`](docs/estado.md); as decisões, em
[`docs/decisoes.md`](docs/decisoes.md); o plano que a guiou, em [`docs/plano.md`](docs/plano.md). Desde 2026-11-23 este
repositório é a engine nova; o histórico do motor antigo não está mais aqui.
