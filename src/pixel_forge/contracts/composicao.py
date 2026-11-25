"""A composição: o asset descrito em dados (o único formato). O tipo diz o rig (o prop na raiz; o humanoide e o
quadrúpede no rig do modelo deles); as medidas em unidades de gente; os nós do kit; as vistas; os pontos do jogo; o
movimento; e os traços que têm de ler no sprite. A revisão é imutável: mudar o desenho é uma revisão nova."""

from __future__ import annotations

from typing import Annotated, ClassVar, Literal

from pydantic import Field, StringConstraints

from .base import Direcao, Id, PosInt, Strict

# números, medidas ($nome), unidades (m, cm, mm, px, %, deg), + − × ÷, min, max, round e parênteses
Expr = Annotated[str, StringConstraints(min_length=1, max_length=240)]
ArgValue = bool | Expr | list[Expr] | list[list[Expr]]
Texto = Annotated[str, StringConstraints(min_length=1, max_length=400)]
Ficha = Annotated[str, StringConstraints(min_length=1, max_length=2000)]
Categoria = Literal["arvore_grande", "arvore_pequena", "arbusto", "casa", "estrutura", "objeto", "prop_de_mao",
                    "humano", "quadrupede"]


class Repeticao(Strict):
    """A repetição declarada: ``linha`` ($i, $t de 0 a 1), ``lados`` ($lado −1 e 1) ou ``anel`` ($cos, $sen do
    ângulo da volta). O nó vira ``<id>_<i>``, cada um com a semente dele."""

    sobre: Literal["linha", "lados", "anel"]
    n: Annotated[int, Field(ge=1, le=64, strict=True)]


class No(Strict):
    """Uma peça do kit com os argumentos em expressões. ``pilha`` e ``camada``: quem cobre quem na mesma face (a camada
    maior cobre a menor que ela toca). ``osso``: a raiz, o tronco do balanço, a cadeia do balanço (pela altura) ou o
    osso do giro."""

    id: Id
    peca: Id
    args: dict[Id, ArgValue] = Field(default_factory=dict)
    repete: Repeticao | None = None
    grupo: Id | None = None
    pilha: Id = "principal"
    camada: Annotated[int, Field(ge=0, le=99, strict=True)] = 0
    osso: Literal["raiz", "tronco", "cadeia", "giro"] = "raiz"


class Balanco(Strict):
    """O balanço: o osso do tronco até ``tronco`` e a cadeia de ``elos`` de ``base`` a ``topo``; a ponta desloca até
    ``desloca_px`` numa onda de ``onda_px`` por período, com ``atraso_mdeg`` por elo."""

    receita: Literal["balanco"]
    tronco: Expr
    base: Expr
    topo: Expr
    elos: Annotated[int, Field(ge=1, le=8, strict=True)] = 4
    periodo_ms: Annotated[int, Field(ge=200, le=20_000, strict=True)]
    desloca_px: Annotated[int, Field(ge=1, le=8, strict=True)]
    onda_px: PosInt = 160
    atraso_mdeg: Annotated[int, Field(ge=0, le=180_000, strict=True)] = 25_000
    amostra_ms: Annotated[int, Field(ge=50, le=2000, strict=True)] = 200


class Giro(Strict):
    """O giro: os nós com ``osso: giro`` dão ``voltas`` voltas em torno do ``centro``, no ``eixo``, em ``quadros``
    amostras por ``periodo_ms``, no ``sentido`` (±1)."""

    receita: Literal["giro"]
    centro: Annotated[list[Expr], Field(min_length=3, max_length=3)]
    eixo: Literal["x", "y", "z"] = "y"
    periodo_ms: Annotated[int, Field(ge=200, le=20_000, strict=True)]
    quadros: Annotated[int, Field(ge=4, le=64, strict=True)]
    voltas: Annotated[int, Field(ge=1, le=4, strict=True)] = 1
    sentido: Literal[-1, 1] = 1


class Clipe(Strict):
    """O clipe de quem anda, pela receita que o gera quando há mais de uma."""

    clip: Id
    receita: Id


class Vista(Strict):
    ocultas: list[Id] = Field(default_factory=list)


class Traco(Strict):
    """O que tem de ler no sprite: as partes que o mostram e como se confere."""

    id: Id
    description: Texto
    parts: Annotated[list[Id], Field(min_length=1)]
    verification: Literal["observable", "visual_only"]
    reads_in_silhouette: bool = False


class Composicao(Strict):
    # os campos que saíram do formato: a recusa diz o que fazer no lugar
    SAIRAM: ClassVar[dict[str, str]] = {
        "sombra": "A sombra de contato (a mancha redonda embaixo do asset) saiu: a sombra no chão é a que o asset "
                  "projeta, e ela já vem no quadro. Apague o campo `sombra`."}

    id: Id
    revision: PosInt
    description: Texto
    reference: Ficha  # a ficha: a referência concreta, as medidas reais e o que dá vida à coisa
    tipo: Literal["prop", "humanoide", "quadrupede"]
    categoria: Categoria
    semente: Annotated[int, Field(ge=0, le=999_999, strict=True)]
    medidas: dict[Id, Expr] = Field(default_factory=dict)
    nos: Annotated[list[No], Field(min_length=1, max_length=64)]
    vistas: dict[Direcao, Vista]
    landmarks: dict[Id, Annotated[list[Expr], Field(min_length=3, max_length=3)]] = Field(default_factory=dict)
    movimento: Annotated[list[Id | Balanco | Giro | Clipe], Field(max_length=96)]
    tracos: list[Traco]
