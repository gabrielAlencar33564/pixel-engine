"""A radiografia do modelo: a ampliação é da geometria (a figura cresce inteira, k vezes); a elevação mostra a altura
sem a câmera do jogo; as medidas do corpo acertam num corpo sintético de proporções reais e acusam cada defeito posto
nele; e o corpo do kit tem, hoje, uma lista conhecida de medidas fora da faixa (a lista encolhe quando o modelo é
corrigido, e nenhuma medida nova pode sair da faixa sem aparecer aqui). O tronco e os ombros já foram corrigidos: as
medidas deles estão na faixa, e o tronco do `pixel-engine` (com o peito em bola) volta a sair dela."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from pixel_forge.application import radiografia as rx
from pixel_forge.application.estilo import estilo_base
from pixel_forge.application.quadros import quadro_de_repouso
from pixel_forge.cli import main
from pixel_forge.contracts.carregar import ler, validar
from pixel_forge.contracts.composicao import Composicao
from pixel_forge.contracts.ir import AssetIR
from pixel_forge.design.asset import ir_da_composicao
from pixel_forge.design.escala import PPM
from pixel_forge.quality.anatomia import medidas_do_humano
from pixel_forge.raster.estilo import estilo_render
from pixel_forge.raster.grade import Mascara

from .oraculo import tronco_do_antigo

EXEMPLOS = Path(__file__).parent / "fixtures" / "exemplos"
# as medidas do corpo do kit que hoje saem da faixa do corpo real: os defeitos do modelo (os da cabeça), medidos em
# 2026-11-24; e as do tronco e dos ombros, que saíam dela até a correção do mesmo dia
DEFEITOS_DO_MODELO = {"rosto_sobre_o_cranio", "olhos_na_cabeca", "ponta_do_perfil", "cabelo_sobre_o_cranio"}
DEFEITOS_DO_TRONCO_ANTIGO = {"cintura_sobre_o_peito", "peito_na_caixa", "vao_no_ombro", "ombro_sobre_o_queixo",
                             "pescoco"}


def _ir(nome: str) -> AssetIR:
    return ir_da_composicao(ler(EXEMPLOS / f"{nome}.r1.json", Composicao))


def _caixa(ir: AssetIR) -> tuple[int, int]:
    """A largura e a altura da figura de frente, na elevação (sem a sombra no chão)."""
    q = quadro_de_repouso(ir, estilo_render(estilo_base()), "S", rx.ELEVACAO)
    ys, xs = np.nonzero(q.alpha == 255)
    return int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)


def _cresceu_inteira(nome: str) -> bool:
    """A figura ampliada mede k vezes a figura no tamanho do jogo (as duas na elevação, no canvas da ampliada), com
    a folga de 1,5 px por lado do tamanho do jogo: lá o contorno e o arredondamento do pixel pesam, e ampliada não."""
    ir = _ir(nome)
    grande, k = rx.ampliada(ir)
    (w, h), (wk, hk) = _caixa(ir.model_copy(update={"canvas": grande.canvas})), _caixa(grande)
    return k > 1 and abs(wk - k * w) <= 3 * k and abs(hk - k * h) <= 3 * k


@pytest.mark.parametrize("nome", ["viajante", "canino", "banco"])
def test_a_ampliacao_e_da_geometria(nome: str) -> None:
    assert _cresceu_inteira(nome)


def test_controle_o_campo_esquecido_na_ampliacao_e_acusado(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(rx, "ESCALAM", rx.ESCALAM - {"radii_q8"})  # os membros e as massas ficariam finos
    assert not _cresceu_inteira("viajante")


def _altura_do_viajante(lente: tuple[int, int] | None) -> float:
    """Do chão ao alto da cabeça na tela, sobre a estatura ampliada (1,72 m)."""
    ir, k = rx.ampliada(_ir("viajante"))
    q = quadro_de_repouso(ir, estilo_render(estilo_base()), "S", lente)
    return (ir.canvas.pivot_px[1] - q.landmarks["head_top"][1] / 256) / (1.72 * PPM * k)


def test_a_elevacao_mostra_a_altura_inteira() -> None:
    assert _altura_do_viajante(rx.ELEVACAO) == pytest.approx(1.0, abs=0.02)


def test_controle_a_camera_do_jogo_achata_a_altura() -> None:
    assert _altura_do_viajante(None) < 0.8


def _caixas(**partes: tuple[int, int, int, int]) -> dict[str, Mascara]:
    """As máscaras de um corpo sintético: cada parte é a caixa (fileira 0, fileira 1, coluna 0, coluna 1)."""
    out: dict[str, Mascara] = {}
    for nome, (y0, y1, x0, x1) in partes.items():
        m = np.zeros((260, 200), dtype=bool)
        m[y0:y1 + 1, x0:x1 + 1] = True
        out[nome] = m
    return out


def _sintetico(**muda: int) -> dict[str, Any]:
    """As medidas de um corpo de proporções reais (240 px de estatura, 40 de cabeça, o centro na coluna 100), com
    os defeitos pedidos: ``olho`` (a fileira dos olhos), ``vao`` e ``sobe`` (o ombro para fora e para cima),
    ``focinho`` (a mandíbula à frente), ``cabelo`` (o fundo do cabelo), ``estreita`` e ``fino`` (o rosto, o pescoço)
    ``aperta`` (a cintura) e ``bola`` (as fileiras do peito, de baixo para cima, com os cantos comidos)."""
    d = {"olho": 29, "vao": 0, "sobe": 0, "focinho": 0, "cabelo": 118, "estreita": 0, "fino": 0, "aperta": 0,
         "bola": 0, **muda}
    e, ombro = d["estreita"], 61 - d["sobe"]
    frente = _caixas(skull=(10, 34, 86, 113), jaw=(30, 46, 88 + e, 111 - e), chin=(44, 49, 94, 105),
                     eye_l=(d["olho"], d["olho"] + 1, 104, 106), eye_r=(d["olho"], d["olho"] + 1, 93, 95),
                     neck=(50, 58, 92 + d["fino"], 108 - d["fino"]), chest=(58 - d["sobe"], 110, 70, 129),
                     waist=(110, 130, 78 + d["aperta"], 121 - d["aperta"]), pelvis_block=(130, 150, 72, 127),
                     j_shoulder_l=(ombro, ombro + 12, 126 + d["vao"], 138 + d["vao"]),
                     j_shoulder_r=(ombro, ombro + 12, 61 - d["vao"], 73 - d["vao"]),
                     foot_l=(240, 249, 104, 114), foot_r=(240, 249, 85, 95))
    for colunas in (slice(70, 78), slice(122, 130)):  # os cantos de baixo do peito, até a largura da cintura
        frente["chest"][111 - d["bola"]:111, colunas] = False
    nariz = (31, 35, 80, 80) if d["focinho"] else (31, 35, 76, 80)
    perfil = _caixas(skull=(10, 34, 80, 113), jaw=(30, 46, 80 - d["focinho"], 105), chin=(44, 49, 82, 95),
                     nose=nariz, hair_cap=(8, 30, 84, d["cabelo"]))
    perfil["skull"] = perfil["skull"] | perfil.pop("nose")
    return {m["medida"]: m for m in medidas_do_humano(frente, perfil)}


def test_a_regua_aceita_o_corpo_de_proporcoes_reais() -> None:
    assert [m for m in _sintetico().values() if not m["ok"]] == []


@pytest.mark.parametrize(("defeito", "medida"), [
    ({"olho": 16}, "olhos_na_cabeca"), ({"vao": 12}, "vao_no_ombro"), ({"sobe": 12}, "ombro_sobre_o_queixo"),
    ({"focinho": 3}, "ponta_do_perfil"), ({"cabelo": 126}, "cabelo_sobre_o_cranio"),
    ({"estreita": 4}, "rosto_sobre_o_cranio"), ({"fino": 3}, "pescoco"), ({"aperta": 8}, "cintura_sobre_o_peito"),
    ({"bola": 36}, "peito_na_caixa")])
def test_controle_a_regua_acusa_cada_defeito(defeito: dict[str, int], medida: str) -> None:
    assert [m["medida"] for m in _sintetico(**defeito).values() if not m["ok"]] == [medida]


def _corpo_do_kit() -> Composicao:
    dado = json.loads((EXEMPLOS / "viajante.r1.json").read_text(encoding="utf-8"))
    dado["nos"] = dado["nos"][:1] + [{"id": "olhos", "peca": "olhos", "args": {"material": "olho"}},
                                     {"id": "cabelo", "peca": "cabelo_preso", "args": {"material": "couro"}}]
    dado["tracos"] = []
    return validar(dado, Composicao, "teste")


def _defeitos_do_kit() -> set[str]:
    medidas = rx.anatomia(rx.ampliada(ir_da_composicao(_corpo_do_kit()))[0], estilo_render(estilo_base()))
    return {m["medida"] for m in medidas if not m["ok"]}


def test_o_corpo_do_kit_tem_estes_defeitos_medidos_e_nenhum_outro() -> None:
    assert _defeitos_do_kit() == DEFEITOS_DO_MODELO


def test_controle_o_tronco_do_antigo_sai_da_faixa(monkeypatch: pytest.MonkeyPatch) -> None:
    tronco_do_antigo(monkeypatch)
    assert _defeitos_do_kit() == DEFEITOS_DO_MODELO | DEFEITOS_DO_TRONCO_ANTIGO


@pytest.mark.slow
def test_o_pfe_radiografia_grava_a_prancha_e_so_o_humano_tem_medidas(tmp_path: Path,
                                                                      capsys: pytest.CaptureFixture[str]) -> None:
    for nome, tem in (("viajante", True), ("banco", False)):
        assert main(["radiografia", str(EXEMPLOS / f"{nome}.r1.json"), "--acervo", str(tmp_path), "--json"]) == 0
        r = json.loads(capsys.readouterr().out)["result"]
        assert Path(r["prancha"]).is_file() and r["amplia"] == 4 and ("medidas" in r) is tem
