"""O modelo de rig em dado (``dados/rigs/<modelo>.json``): os ossos, os pais e os limites, e os papéis.

- **Ossos:** id, pai (uma lista: vale o primeiro que existe), posição e comprimento (expressões em px nas medidas do
  corpo, avaliadas por quem monta o asset; esta camada só lê o texto), eixo, limites em graus e o ângulo de repouso.
  ``lados`` repete o bloco para ``l`` (``$lado`` = 1) e ``r`` (−1), na ordem.
- **Papéis:** cada papel (pelve, coluna, pescoço, cabeça, braço e perna de cada lado) diz o osso de cada junta dele.
  Os geradores de movimento citam ``(papel, junta)``, nunca o nome do osso. Os anexos são os papéis dos ossos que a
  roupa acrescenta (a saia).
- **IK de N segmentos:** a cadeia de cada perna diz o alvo do triângulo (os dois segmentos de cima) e os distais, que
  se orientam no mundo depois (a pata plana no apoio, o punho que dobra no balanço). Sem cadeia, o alvo é o pé.
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
class Cadeia:
    papel: str
    ate: str  # a junta da ponta (o pé)
    alvo: str  # a junta que o triângulo põe no alvo
    orienta: tuple[str, ...]  # as juntas distais, orientadas no mundo


@dataclass(frozen=True)
class RigModelo:
    id: str
    ossos: tuple[OssoModelo, ...]
    papeis: dict[str, dict[str, str]]
    ik: tuple[Cadeia, ...]


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
    ik = tuple(Cadeia(_por_lado(c["papel"], lado), c["ate"], c["alvo"], tuple(c["orienta"]))
               for c in raw.get("ik", []) for lado in ([ln for ln, _ in LADOS] if "{lado}" in c["papel"] else [""]))
    return RigModelo(raw["id"], tuple(ossos), {**_papeis(raw["papeis"]), **_papeis(raw.get("anexos", {}))}, ik)


@dataclass(frozen=True)
class Papeis:
    """Os papéis de um asset: ``osso(papel, junta)`` é o osso que o asset tem naquela junta (ou ``None``); as cadeias
    de IK, do osso do pé ao alvo do triângulo e aos distais."""

    mapa: dict[str, dict[str, str]]
    cadeias: dict[str, tuple[str, tuple[str, ...]]]

    def alvo(self, pe: str) -> str:
        """O osso que o IK do triângulo põe no alvo da perna que termina em ``pe`` (sem cadeia, o próprio pé)."""
        return self.cadeias.get(pe, (pe, ()))[0]

    def osso(self, papel: str, junta: str) -> str | None:
        return self.mapa.get(papel, {}).get(junta)

    def exige(self, papel: str, junta: str) -> str:
        b = self.osso(papel, junta)
        if b is None:
            raise Recusa("RIG_PAPEL", f"O rig não tem a junta '{junta}' do papel '{papel}'.",
                         "O movimento cita papéis do modelo do tipo (o humano: pelve, coluna, braço e perna).")
        return b


def papeis_do_asset(nome: str, ossos: set[str]) -> Papeis:
    """Os papéis do modelo, só com os ossos que o asset tem, e as cadeias de IK dele."""
    m = modelo(nome)
    mapa = {p: {j: b for j, b in juntas.items() if b in ossos} for p, juntas in m.papeis.items()}
    cadeias = {mapa[c.papel][c.ate]: (mapa[c.papel][c.alvo], tuple(mapa[c.papel][x] for x in c.orienta))
               for c in m.ik if c.ate in mapa[c.papel]}
    return Papeis(mapa, cadeias)
