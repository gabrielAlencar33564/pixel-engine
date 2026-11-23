"""O modelo de rig em dado (``dados/rigs/<modelo>.json``): os ossos, os pais e os limites, e os papéis.

- **Ossos:** id, pai (uma lista: vale o primeiro que existe), posição e comprimento (expressões em px nas medidas do
  corpo, avaliadas por quem monta o asset; esta camada só lê o texto), eixo, limites em graus e o ângulo de repouso.
  ``lados`` repete o bloco para ``l`` (``$lado`` = 1) e ``r`` (−1), na ordem.
- **Papéis:** cada papel (pelve, coluna, pescoço, cabeça, braço e perna de cada lado) diz o osso de cada junta dele.
  Os geradores de movimento citam ``(papel, junta)``, nunca o nome do osso. Os anexos são os papéis dos ossos que a
  roupa acrescenta (a saia).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Any

from ..core.recusa import Recusa

DIR = Path(__file__).resolve().parents[1] / "dados" / "rigs"
LADOS = (("l", 1), ("r", -1))


@dataclass(frozen=True)
class OssoModelo:
    id: str
    pai: tuple[str, ...]
    pos: tuple[str, str, str]
    eixo: str
    comp: str
    limites: tuple[int, int]  # graus
    repouso: str
    lado: int  # 0 no centro; 1 (l) ou −1 (r) no bloco de lados


@dataclass(frozen=True)
class RigModelo:
    id: str
    ossos: tuple[OssoModelo, ...]
    papeis: dict[str, dict[str, str]]


def _por_lado(texto: str, lado: str) -> str:
    return texto.replace("{lado}", lado)


def _osso(raw: dict[str, Any], lado: tuple[str, int] | None) -> OssoModelo:
    nome, sx = lado or ("", 0)
    lim = raw["limites"][nome] if isinstance(raw["limites"], dict) else raw["limites"]
    return OssoModelo(_por_lado(raw["id"], nome), tuple(_por_lado(p, nome) for p in raw["pai"]), tuple(raw["pos"]),
                      raw["eixo"], raw.get("comp", "0"), (int(lim[0]), int(lim[1])), raw.get("repouso", "0"), sx)


def _papeis(raw: dict[str, dict[str, str]]) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for nome, juntas in raw.items():
        for lado in ([ln for ln, _ in LADOS] if "{lado}" in nome else [""]):
            out[_por_lado(nome, lado)] = {j: _por_lado(b, lado) for j, b in juntas.items()}
    return out


@cache
def modelo(nome: str) -> RigModelo:
    arq = DIR / f"{nome}.json"
    if not arq.is_file():
        raise Recusa("RIG_MODELO", f"O rig '{nome}' não tem modelo.", "Os rigs de quem anda são os do tipo do asset.")
    raw = json.loads(arq.read_text(encoding="utf-8"))
    ossos: list[OssoModelo] = []
    for item in raw["ossos"]:
        ossos += [_osso(o, lado) for lado in LADOS for o in item["lados"]] if "lados" in item else [_osso(item, None)]
    return RigModelo(raw["id"], tuple(ossos), {**_papeis(raw["papeis"]), **_papeis(raw.get("anexos", {}))})


@dataclass(frozen=True)
class Papeis:
    """Os papéis de um asset: ``osso(papel, junta)`` é o osso que o asset tem naquela junta (ou ``None``)."""

    mapa: dict[str, dict[str, str]]

    def osso(self, papel: str, junta: str) -> str | None:
        return self.mapa.get(papel, {}).get(junta)

    def exige(self, papel: str, junta: str) -> str:
        b = self.osso(papel, junta)
        if b is None:
            raise Recusa("RIG_PAPEL", f"O rig não tem a junta '{junta}' do papel '{papel}'.",
                         "O movimento cita papéis do modelo do tipo (o humano: pelve, coluna, braço e perna).")
        return b


def papeis_do_asset(nome: str, ossos: set[str]) -> Papeis:
    """Os papéis do modelo, só com os ossos que o asset tem."""
    return Papeis({p: {j: b for j, b in juntas.items() if b in ossos} for p, juntas in modelo(nome).papeis.items()})
