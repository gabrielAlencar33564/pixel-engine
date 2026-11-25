"""O lado novo do oráculo: o RGBA de cada vista de um caso de ``tests/fixtures/oraculo/``."""

from __future__ import annotations

import copy
import hashlib
import json
import math
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from pixel_forge.application.estilo import estilo_base
from pixel_forge.application.quadros import quadro_de_repouso
from pixel_forge.contracts.carregar import ler, validar
from pixel_forge.contracts.estilo import StyleDoc
from pixel_forge.contracts.ir import AssetIR
from pixel_forge.design import humano as desenho_do_humano
from pixel_forge.design.construtor import PARTE, AssetBuilder, Parte, ellipse, qv
from pixel_forge.design.kit import humano, roupa
from pixel_forge.motion.receita import carregar
from pixel_forge.raster.estilo import estilo_render

CASOS = Path(__file__).parent / "fixtures" / "oraculo"
ABRE_BRACO_DO_ANTIGO = 15_000.0  # o `pixel-engine` abre o braço a 15° no repouso
ABERTURA_DO_ANTIGO = 0.080  # e põe cada tornozelo a 0,080 da estatura do meio do corpo
BALANCO_DO_ANTIGO = (23_000, 26_000)  # e, no andar, balança o ombro 23° e dobra o cotovelo 26° (mdeg)
# o tronco do `pixel-engine`: a junta do ombro na base do pescoço, o pescoço fino, o braço do tamanho real, o peito
# e a cintura como duas bolas (cada uma com a sua sombra e, no corpo, o seu contorno), a jaqueta sobre elas e a manga
# começando acima da junta; sem a linha do ombro
TRONCO_DO_ANTIGO = ((humano, "OMBRO_CAI", 0.0), (humano, "R_PESCOCO", 0.024), (humano, "BRACO", 0.186),
                    (humano, "ANTEBRACO", 0.146), (humano, "CINTURA", (0.30, 0.16)), (humano, "CINTURA_X", 0.075),
                    (humano, "QUADRIL_LARG_X", 0.095), (humano, "QUADRIL", ("pelvis", ())),
                    (roupa, "JAQUETA_CINTURA", (0.22, 0.26)), (roupa, "MANGA_DE", -0.05))
LINHA_DO_OMBRO = ("trap_", "jacket_yoke_")  # as partes que o `pixel-engine` não tem
# os membros do `pixel-engine`, nas medidas do corpo real: a esfera saliente em cada junta, a canela que afina até
# 0,021 da estatura, a mão fina e comprida, o pé de 0,152 e alto, e cada parte sombreada sozinha
MEMBROS_DO_ANTIGO = ((humano, "R_JUNTAS", (1.15, 1.0, 0.95, 1.1, 1.1)), (humano, "DEPOIS_DA_JUNTA", (0.95, 0.92)),
                     (humano, "MAO_FORMA", (0.6, 1.5, 0.45)), (humano, "PE_ALTO", (0.72, 0.45)),
                     (roupa, "PE_ALTO", (0.72, 0.45)), (humano, "MASSA_DO_MEMBRO", ()), (humano, "PE", 0.152),
                     (humano, "R_COXA", 0.047), (humano, "R_CANELA_BAIXO", 0.021))
# a bola do peito dele: o centro e a meia altura em frações do tronco (a do corpo e a da jaqueta, que tem folga), e
# o grupo de contorno de cada massa do tronco (na engine o peito e a cintura são uma massa só)
BOLA_DO_PEITO, BOLA_DA_JAQUETA = (0.70, 0.32), (0.68, 0.36)
GRUPO_DO_ANTIGO = {"chest": "chest", "waist": "waist", "jacket_chest": "jacket", "jacket_waist": "jacket"}
# a cabeça do `pixel-engine`: três massas (o crânio menor e mais alto, a mandíbula estreita e à frente e o queixo),
# com o chapéu assentado no crânio dela; na engine a cabeça é um ovo só
CABECA_DO_ANTIGO = ((humano, "CRANIO", (-0.06, 0.43, 0.41, 0.33)), (roupa, "CHAPEU", ((-0.02, 0.30), (0.06, 0.16))))


def abertura_do_antigo(monkeypatch: pytest.MonkeyPatch) -> None:
    """As pernas abertas do `pixel-engine`: os tornozelos a 0,080 da estatura do meio (26 cm um do outro), mais
    afastados que as juntas do quadril. A engine os põe sob elas (mudança intencional), e o oráculo compara o resto
    do humano na abertura dele."""
    monkeypatch.setattr(humano, "TORNOZELO_X", ABERTURA_DO_ANTIGO)


def membros_do_antigo(monkeypatch: pytest.MonkeyPatch) -> None:
    """Os braços, as pernas, as mãos e os pés nas formas do `pixel-engine` (as do corpo real): na engine são formas
    simples, para a câmera de cima (mudança intencional), e o oráculo compara o resto do humano nos membros dele."""
    for modulo, nome, valor in MEMBROS_DO_ANTIGO:
        monkeypatch.setattr(modulo, nome, valor)


def braco_do_antigo(monkeypatch: pytest.MonkeyPatch) -> None:
    """O braço do humano na abertura do `pixel-engine`: a engine abre menos (mudança intencional), e o oráculo
    compara o resto do humano (o corpo, o rig, o movimento e o render) na abertura dele."""
    monkeypatch.setattr(humano, "ABRE_BRACO_MDEG", ABRE_BRACO_DO_ANTIGO)


def _bola(c: dict[str, float], folga: float) -> tuple[float, float, float]:
    """(a meia profundidade, a altura do centro, a meia altura) da bola do peito; com folga, a da jaqueta."""
    z, rz = BOLA_DA_JAQUETA if folga else BOLA_DO_PEITO
    return c["peito_y"] * 1.12 + 0.35 if folga else c["peito_y"], z * c["tronco"], rz * c["tronco"]


def _peito_do_antigo(c: dict[str, float], folga: float = 0.0,
                     larg: tuple[float, float] = (1.0, 0.0)) -> dict[str, Any]:
    ry, cz, rz = _bola(c, folga)
    return ellipse(qv(0, 0.1, cz), qv(c["peito_x"] * larg[0] + larg[1], ry, rz))


def _frente_do_antigo(c: dict[str, float], z: float, folga: float = 0.0) -> float:
    ry, cz, rz = _bola(c, folga)
    u = (z - cz) / rz
    return 0.1 + ry * math.sqrt(max(0.0, 1 - u * u))


def _partes_do_antigo(monkeypatch: pytest.MonkeyPatch, grupos: dict[str, str], fora: tuple[str, ...]) -> None:
    """As partes de ``grupos`` no grupo de contorno do antigo, cada uma sombreada sozinha, e sem as de ``fora`` (os
    ids que começam assim: as partes que o `pixel-engine` não tem)."""
    parte = AssetBuilder.part

    def do_antigo(b: AssetBuilder, id: str, material: str, geometry: dict[str, Any], como: Parte = PARTE) -> None:
        if id in grupos:
            como = replace(como, group=grupos[id], tags=tuple(t for t in como.tags if t != "shade_group"))
        if not id.startswith(fora):
            parte(b, id, material, geometry, como)

    monkeypatch.setattr(AssetBuilder, "part", do_antigo)


def sem_as_partes(monkeypatch: pytest.MonkeyPatch, *prefixos: str) -> None:
    """O corpo sem as partes cujo id começa por um dos ``prefixos`` (o controle de uma parte nova)."""
    _partes_do_antigo(monkeypatch, {}, prefixos)


def _olhos_do_antigo(v: roupa.Veste) -> roupa.Vista:
    """Os olhos do `pixel-engine`: na testa (a meio caminho entre o centro e o alto do crânio), com o contorno em
    volta, e por cima do cabelo e do lenço por regra."""
    cy, cz, rx, ry, rz = humano.cranio(v.c)
    z = cz + 0.5 * rz
    for side, sx in humano.SIDES:
        x = sx * 0.42 * rx
        y = cy + ry * math.sqrt(max(0.0, 1 - (x / rx) ** 2 - ((z - cz) / rz) ** 2))
        v.part(f"eye_{side}", ellipse(qv(x, y, z), qv(0.6, 0.5, 0.9)), ("head", "eyes"))
    return roupa.Vista(hide_back=["eye_l", "eye_r"], hide_w=["eye_r"], hide_e=["eye_l"],
                       front_rules=[roupa.regra(f"eye_{s}", o) for s in ("l", "r")
                                    for o in ("skull", "hair_cap", "scarf")])


def _cabelo_do_antigo(v: roupa.Veste) -> roupa.Vista:
    """O cabelo preso do `pixel-engine`: a massa recuada 20 % da cabeça, com o crânio por cima dela de frente."""
    cab = v.c["cabeca"]
    cy, cz, rx, ry, rz = humano.cranio(v.c)
    v.part("hair_cap", ellipse(qv(0, cy - 0.20 * cab, cz + 0.13 * cab), qv(rx + 0.25, ry + 0.05, rz)), ("head", "hair"))
    v.part("topknot", ellipse(qv(0, cy - 0.16 * cab, cz + 0.42 * cab), qv(0.14 * cab, 0.16 * cab, 0.13 * cab)),
           ("head", "hair"))
    return roupa.Vista(rules=[roupa.regra("topknot", "hair_cap")], front_rules=[roupa.regra("skull", "hair_cap")],
                       back_rules=[roupa.regra("hair_cap", "skull")])


def _cabeca_do_antigo(b: AssetBuilder, c: dict[str, float], pele: str) -> None:
    """As três massas da cabeça do `pixel-engine`: o crânio, a mandíbula e o queixo, cada uma sombreada sozinha."""
    cab = c["cabeca"]
    cy, cz, rx, ry, rz = humano.cranio(c)
    cabeca = Parte(bone="head", group="head")
    b.part("skull", pele, ellipse(qv(0, cy, cz), qv(rx, ry, rz)), cabeca)
    b.part("jaw", pele, ellipse(qv(0, 0.08 * cab, 0.02 * cab), qv(0.26 * cab, 0.30 * cab, 0.25 * cab)), cabeca)
    b.part("chin", pele, ellipse(qv(0, 0.27 * cab, -0.15 * cab), qv(0.13 * cab, 0.10 * cab, 0.10 * cab)), cabeca)


def _regras_do_antigo(d: str) -> list[dict[str, str]]:
    """De frente, o queixo e a mandíbula sobre o pescoço; de costas, o crânio sobre a mandíbula e o queixo."""
    out = [{"front": "chest", "back": "waist"}, {"front": "waist", "back": "pelvis_block"}]
    if d in humano.FRONT_VIEWS:
        return [*out, {"front": "chin", "back": "neck"}, {"front": "jaw", "back": "neck"}]
    return [*out, {"front": "skull", "back": "jaw"}, {"front": "skull", "back": "chin"}]


def cabeca_do_antigo(monkeypatch: pytest.MonkeyPatch) -> None:
    """A cabeça, os olhos e o cabelo preso do humano como no `pixel-engine`: na engine a cabeça é um ovo só, feito
    para a câmera de cima (mudança intencional), e o oráculo compara o resto do humano na cabeça dele. O chapéu
    segue o crânio, e volta junto."""
    for modulo, nome, valor in CABECA_DO_ANTIGO:
        monkeypatch.setattr(modulo, nome, valor)
    monkeypatch.setattr(humano, "_cabeca", _cabeca_do_antigo)
    for modulo in (humano, desenho_do_humano):
        monkeypatch.setattr(modulo, "regras", _regras_do_antigo)
    monkeypatch.setitem(roupa.PECAS, "olhos", _olhos_do_antigo)
    monkeypatch.setitem(roupa.PECAS, "cabelo_preso", _cabelo_do_antigo)


def tronco_do_antigo(monkeypatch: pytest.MonkeyPatch) -> None:
    """O tronco, os ombros, o pescoço e o braço do humano nas medidas do `pixel-engine`, com o peito em bola (e
    cada massa do tronco sombreada e contornada sozinha) e sem a linha do ombro: a engine corrigiu a anatomia
    (mudança intencional), e o oráculo compara o resto do humano (o rig, a roupa, o movimento e o render) no tronco
    dele."""
    for modulo, nome, valor in TRONCO_DO_ANTIGO:
        monkeypatch.setattr(modulo, nome, valor)
    for modulo in (humano, roupa):
        monkeypatch.setattr(modulo, "peito", _peito_do_antigo)
    monkeypatch.setattr(roupa, "frente_do_peito", _frente_do_antigo)
    _partes_do_antigo(monkeypatch, GRUPO_DO_ANTIGO, LINHA_DO_OMBRO)


def apoio_do_antigo(monkeypatch: pytest.MonkeyPatch) -> None:
    """O parado com os pés lado a lado, como no `pixel-engine`: a engine os desencontra (mudança intencional), e o
    oráculo compara o resto do parado no apoio dele."""
    monkeypatch.delitem(carregar("parado"), "avanco_m")


def balanco_do_antigo(monkeypatch: pytest.MonkeyPatch) -> None:
    """O balanço do braço no andar com a amplitude do `pixel-engine` (o ombro e o cotovelo): a da engine é menor
    (mudança intencional), e o oráculo compara o resto do andar na amplitude dele."""
    receita = carregar("andar_poses")
    canais = copy.deepcopy(receita["canais"])
    for lado, sinal in (("r", 1), ("l", -1)):
        canais[f"braco_{lado}.frente"]["rot"]["termos"][1]["amp"] = sinal * BALANCO_DO_ANTIGO[0]
        canais[f"braco_{lado}.cotovelo"]["rot"]["termos"][1]["amp"] = BALANCO_DO_ANTIGO[1]
    monkeypatch.setitem(receita, "canais", canais)


def no_canvas_antigo(rgba: np.ndarray[Any, np.dtype[np.uint8]], tamanho: list[int]) -> dict[str, Any]:
    """O quadro no canvas do antigo, como o oráculo grava (o tamanho, o hash e o hash sem a sombra no chão): o canvas
    novo inclui a sombra que o asset projeta no chão (à direita e embaixo; o pivô não muda), então o antigo é o
    recorte de cima e da esquerda, e fora dele só há a sombra no chão."""
    w, h = tamanho
    chao = np.array(next(p.rgba for p in estilo_base().palette if p.id == "sombra_chao"), dtype=np.uint8)
    if rgba.shape[0] >= h and rgba.shape[1] >= w:
        fora = rgba.copy()
        fora[:h, :w] = 0
        assert np.all(np.all(fora[fora[..., 3] == 255] == chao, axis=-1)), "fora do canvas antigo: não é sombra"
        rgba = np.ascontiguousarray(rgba[:h, :w])
    sem = rgba.copy()
    sem[np.all(rgba == chao, axis=-1) | (rgba[..., 3] == 0)] = 0  # a sombra no chão e o fundo
    return {"tamanho": [int(rgba.shape[1]), int(rgba.shape[0])],
            "rgba_sha256": hashlib.sha256(rgba.tobytes()).hexdigest(),
            "sem_chao_sha256": hashlib.sha256(sem.tobytes()).hexdigest()}


def caso(nome: str) -> dict[str, Any]:
    dado: dict[str, Any] = json.loads((CASOS / f"{nome}.json").read_text(encoding="utf-8"))
    return dado


def esperado(nome: str) -> dict[str, Any]:
    dado: dict[str, Any] = json.loads((CASOS / f"{nome}.esperado.json").read_text(encoding="utf-8"))
    return dado


def rgba_por_vista(dado: dict[str, Any]) -> dict[str, tuple[list[int], str]]:
    style = ler(CASOS / dado["estilo"], StyleDoc)
    ir = validar(dado["ir"], AssetIR, "caso")
    est = estilo_render(style)
    palette = {p.index: (p.rgba[0], p.rgba[1], p.rgba[2], p.rgba[3]) for p in style.palette}
    out = {}
    for vista in dado["vistas"]:
        rgba = quadro_de_repouso(ir, est, vista).to_rgba(palette)
        out[vista] = ([int(rgba.shape[1]), int(rgba.shape[0])], hashlib.sha256(rgba.tobytes()).hexdigest())
    return out
