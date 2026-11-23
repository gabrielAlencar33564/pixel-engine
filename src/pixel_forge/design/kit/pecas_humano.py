"""O corpo e a roupa do humano como peças do kit. ``corpo_humano`` é o primeiro nó: o corpo do cânone no rig do
modelo (a estatura em metros, as cabeças, a largura, a grossura e o quadril em %); a roupa veste o corpo do nó de
antes e diz às vistas o que cobre. ``detalhe`` é o segundo material (a gola, a ponta da faixa, a barra, as pontas)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ...core.recusa import Recusa
from ..escala import PPM
from . import roupa
from .humano import Corpo, corpo, esqueleto, medidas
from .peca import Arg, Ctx, Peca

TESTE = "tests/test_humano.py::test_cada_peca_veste_o_corpo"
OITO = ("S", "SW", "W", "NW", "N", "NE", "E", "SE")
X = Arg


def corpo_dos_args(a: dict[str, Any]) -> Corpo:
    """O corpo nos inteiros do cânone (mm e milésimos): o mesmo corpo dá a mesma IR."""
    return Corpo(round(a["estatura"] / PPM * 1000) / 1000, round(a["cabecas"] * 1000) / 1000,
                 round(a["largura"] * 1000) / 1000, round(a["espessura"] * 1000) / 1000,
                 round(a["quadril"] * 1000) / 1000)


def _corpo(c: Ctx, a: dict[str, Any]) -> None:
    med = medidas(corpo_dos_args(a))
    esqueleto(c.b, med)
    corpo(c.b, med, a["pele"], a["juntas"])
    c.humano.update(medidas=med, vista=roupa.Vista())


def _veste(peca: str, opcoes: dict[str, str]) -> Callable[[Ctx, dict[str, Any]], None]:
    """A peça de roupa ``peca`` com as opções da composição (``largura`` em % vira ``largura_pct``)."""
    def desenha(c: Ctx, a: dict[str, Any]) -> None:
        if "medidas" not in c.humano:
            raise Recusa("CORPO", f"Nó '{c.no}': a roupa '{peca}' veste o corpo, e o nó 'corpo_humano' não veio antes.",
                         "Ponha o corpo como o primeiro nó.", "/nos")
        op = {chave: round(a[arg] * 100) if arg in ("largura", "comprimento") else a[arg]
              for arg, chave in opcoes.items()}
        c.humano["vista"].merge(roupa.PECAS[peca](roupa.Veste(c.b, c.humano["medidas"], a["material"],
                                                               a.get("detalhe", ""), op)))

    return desenha


MATERIAL = X("material", "material", "o material da peça")
DETALHE = X("detalhe", "material", "o segundo material (vazio: o mesmo da peça)", "")


def _roupa(peca: str, descricao: str, args: tuple[Arg, ...], opcoes: dict[str, str],
           variacoes: tuple[tuple[str, dict[str, Any]], ...]) -> Peca:
    return Peca(peca, descricao, (MATERIAL, *args), _veste(peca, opcoes), variacoes, TESTE,
                (_veste, roupa.PECAS[peca]), vistas=OITO, tipo="humanoide")


PECAS_HUMANO = [
    Peca("corpo_humano", "O corpo do cânone no rig do humano, com uma esfera em cada junta (a roupa veste por cima)", (
        X("estatura", "comprimento", "do chão ao alto do crânio", "1.65m"),
        X("cabecas", "escalar", "a estatura em cabeças", "6"),
        X("largura", "escalar", "a largura do tronco sobre o cânone", "100%"),
        X("espessura", "escalar", "a grossura dos segmentos sobre o cânone", "100%"),
        X("quadril", "escalar", "a altura da junta do quadril, em fração da estatura", "53%"),
        X("pele", "material", "o material do corpo (gente: pele)", "fibra"),
        X("juntas", "material", "o material das esferas das juntas", "madeira_cortada")),
        _corpo, (("adulto de madeira", {}), ("criança", {"estatura": "1.25m", "cabecas": "5", "quadril": "49%"}),
                 ("forte, de pele", {"estatura": "1.76m", "largura": "120%", "espessura": "115%", "pele": "pele",
                                     "juntas": "pele"})),
        TESTE, (_corpo, corpo_dos_args, esqueleto, corpo, medidas), vistas=OITO, tipo="humanoide"),
    _roupa("jaqueta", "Blusa ou jaqueta cruzada com gola em V e mangas: sem manga, ao cotovelo, ao meio do antebraço, "
           "ao punho", (DETALHE, X("largura", "escalar", "a abertura da manga para a ponta", "140%"),
                        X("manga", "inteiro", "0 sem, 1 cotovelo, 2 meio do antebraço, 3 punho", "2")),
           {"largura": "largura_pct", "manga": "manga"},
           (("curta", {"material": "linho", "manga": "1", "largura": "115%"}),
            ("larga", {"material": "pano_azul", "detalhe": "linho", "largura": "160%"}),
            ("ao punho", {"material": "pano_cinza", "manga": "3"}))),
    _roupa("faixa", "Faixa na cintura com o nó na frente e a ponta solta", (DETALHE,), {},
           (("palha", {"material": "fibra"}), ("couro", {"material": "couro"}),
            ("ponta de outra cor", {"material": "pano_cinza", "detalhe": "fibra"}))),
    _roupa("calca", "Calça em dois tubos: justa, larga, presa na canela", (
           DETALHE, X("largura", "escalar", "a abertura da barra", "150%"),
           X("barra", "inteiro", "1 prende a canela com uma faixa em 'detalhe'", "0")),
           {"largura": "largura_pct", "barra": "barra"},
           (("folgada", {"material": "pano_cinza", "largura": "120%"}),
            ("larga", {"material": "pano_cinza", "largura": "180%"}),
            ("presa", {"material": "pano_azul", "detalhe": "linho", "barra": "1"}))),
    _roupa("saia", "Saia em A da cintura à canela ou ao tornozelo: as metades seguem a coxa com atraso ao andar", (
           DETALHE, X("largura", "escalar", "a barra sobre o quadril: 100% reta, 160% em A, 220% rodada", "160%"),
           X("comprimento", "escalar", "a fração da perna que ela cobre (100% = até o tornozelo)", "100%")),
           {"largura": "largura_pct", "comprimento": "comprimento_pct"},
           (("longa", {"material": "pano_marrom"}), ("rodada", {"material": "pano_azul_escuro", "largura": "220%"}),
            ("ao meio da canela", {"material": "pano_ferrugem", "detalhe": "linho", "comprimento": "75%"}))),
    _roupa("lenco", "Lenço na cabeça: cobre o alto e a nuca, deixa o rosto, com o nó e as pontas atrás", (DETALHE,), {},
           (("vermelho", {"material": "pano_vermelho"}), ("de linho", {"material": "linho"}),
            ("pontas escuras", {"material": "pano_azul", "detalhe": "pano_azul_escuro"}))),
    _roupa("olhos", "Dois olhos na frente do crânio (somem de costas)", (), {},
           (("escuros", {"material": "olho"}), ("couro", {"material": "couro"}), ("claros", {"material": "linho"}))),
    _roupa("cabelo_preso", "Cabelo puxado para trás com o coque no alto", (), {},
           (("escuro", {"material": "couro"}), ("pano", {"material": "pano_azul"}), ("palha", {"material": "fibra"}))),
    _roupa("chapeu", "Chapéu mole de aba larga, a copa baixa e a aba caída", (
           DETALHE, X("largura", "escalar", "a aba sobre a largura da cabeça", "180%")), {"largura": "largura_pct"},
           (("de feltro", {"material": "couro"}), ("aba curta", {"material": "pano_azul", "largura": "140%"}),
            ("de palha", {"material": "fibra", "largura": "210%"}))),
    _roupa("bolsa", "Bolsa a tiracolo: a alça cruzando o peito e o saco no quadril direito", (DETALHE,), {},
           (("de pano", {"material": "linho", "detalhe": "couro"}), ("de couro", {"material": "couro"}),
            ("escura", {"material": "pano_cinza", "detalhe": "fibra"}))),
    _roupa("sandalia", "Sola sob o pé e a tira sobre o peito do pé", (DETALHE,), {},
           (("palha", {"material": "fibra"}), ("tira de couro", {"material": "fibra", "detalhe": "couro"}),
            ("couro", {"material": "couro"}))),
    _roupa("tabi", "Calçado fechado sobre o pé e o tornozelo (meia, tamanco, bota baixa)", (), {},
           (("linho", {"material": "linho"}), ("escuro", {"material": "pano_azul"}), ("couro", {"material": "couro"}))),
]
