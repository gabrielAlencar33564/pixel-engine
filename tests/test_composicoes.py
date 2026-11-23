"""As composições sintéticas (a árvore no balanço com os cachos nas pontas dos galhos, o abrigo de pedra e palha, o
marco nas 4 vistas) dão o mesmo pixel que o `pixel-engine` na mesma entrada. A mudança intencional: a sombra de contato
das vistas E, N e W sai reescalada para o oblíquo como a da S (no antigo, ela ficava achatada pela metade)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, cast

import numpy as np
import pytest

from pixel_forge.application.build import instantes
from pixel_forge.application.estilo import estilo_base
from pixel_forge.application.quadros import quadro_da_pose, quadro_de_repouso
from pixel_forge.contracts.base import Direcao
from pixel_forge.contracts.carregar import ler, validar
from pixel_forge.contracts.composicao import Composicao
from pixel_forge.core.recusa import Recusa
from pixel_forge.design.asset import ir_da_composicao, movimento
from pixel_forge.raster.estilo import estilo_render

from .oraculo import CASOS, no_canvas_antigo
from .test_humano import _hashes

ESPERADO: dict[str, Any] = json.loads((CASOS / "composicoes.esperado.json").read_text(encoding="utf-8"))["casos"]
SOMBRA_GIRADA = {("marco", "E"), ("marco", "N"), ("marco", "W")}
VISTAS = [(c, v) for c in sorted(ESPERADO) if "/" not in c for v in ESPERADO[c] if (c, v) not in SOMBRA_GIRADA]


def rgba(nome: str, vista: str) -> np.ndarray[Any, np.dtype[np.uint8]]:
    style = estilo_base()
    comp = ler(CASOS / "composicoes" / f"{nome}.r1.json", Composicao)
    q = quadro_de_repouso(ir_da_composicao(comp), estilo_render(style), cast(Direcao, vista))
    return q.to_rgba({p.index: (p.rgba[0], p.rgba[1], p.rgba[2], p.rgba[3]) for p in style.palette})


@pytest.mark.parametrize(("nome", "vista"), VISTAS, ids=[f"{c}/{v}" for c, v in VISTAS])
def test_igual_ao_oraculo(nome: str, vista: str) -> None:
    quer = ESPERADO[nome][vista]
    feito = no_canvas_antigo(rgba(nome, vista), quer["tamanho"])
    assert [feito["tamanho"], feito["rgba_sha256"]] == [quer["tamanho"], quer["rgba_sha256"]]


def _altura_da_sombra(img: np.ndarray[Any, np.dtype[np.uint8]]) -> int:
    chao = next(p.rgba for p in estilo_base().palette if p.id == "sombra_chao")
    ys = np.nonzero(np.all(img == np.array(chao, dtype=np.uint8), axis=-1))[0]
    return int(ys.max() - ys.min() + 1)


def test_a_sombra_de_contato_tem_a_mesma_altura_em_toda_vista() -> None:
    alturas = {v: _altura_da_sombra(rgba("marco", v)) for v in ("S", "E", "N", "W")}
    assert max(alturas.values()) - min(alturas.values()) <= 1, alturas


def test_controle_o_oraculo_acusa_a_sombra_girada_de_antes() -> None:
    feitos = {v: no_canvas_antigo(rgba("marco", v), ESPERADO["marco"][v]["tamanho"])["rgba_sha256"]
              for v in ("E", "N", "W")}
    assert all(feitos[v] != ESPERADO["marco"][v]["rgba_sha256"] for v in feitos)


def test_composicao_de_fixture_tem_um_arquivo_por_caso() -> None:
    assert sorted(p.stem.removesuffix(".r1") for p in (CASOS / "composicoes").glob("*.json")) == sorted(
        c for c in ESPERADO if "/" not in c)


def test_controle_a_ancora_citada_antes_de_ser_deixada_e_recusada(tmp_path: Path) -> None:
    from pixel_forge.core.recusa import Recusa

    dado = json.loads((CASOS / "composicoes" / "arvore.r1.json").read_text(encoding="utf-8"))
    dado["nos"] = [dado["nos"][0], dado["nos"][2], dado["nos"][1]]
    arq = tmp_path / "x.json"
    arq.write_text(json.dumps(dado), encoding="utf-8")
    with pytest.raises(Recusa) as e:
        ir_da_composicao(ler(arq, Composicao))
    assert e.value.codigo == "ANCORA" and "acima" in e.value.dica


TODAS = sorted((CASOS.parent).rglob("*.r1.json"))


@pytest.mark.parametrize("arq", TODAS, ids=[a.stem for a in TODAS])
def test_nenhuma_vista_sai_do_canvas(arq: Path) -> None:
    """O canvas inclui a sombra que o asset projeta no chão (no antigo, ela saía do canvas e era cortada)."""
    ir = ir_da_composicao(ler(arq, Composicao))
    est = estilo_render(estilo_base())
    assert {d: quadro_de_repouso(ir, est, d).clipping_px for d in ir.views} == dict.fromkeys(ir.views, 0)


def test_controle_sem_a_sombra_no_canvas_o_abrigo_sai_dele() -> None:
    ir = ir_da_composicao(ler(CASOS / "composicoes" / "abrigo.r1.json", Composicao))
    estreito = ir.model_copy(update={"canvas": ir.canvas.model_copy(update={"width": ir.canvas.width - 40})})
    assert quadro_de_repouso(estreito, estilo_render(estilo_base()), "S").clipping_px > 0


@pytest.mark.slow
def test_o_balanco_da_arvore_igual_ao_oraculo() -> None:
    """O balanço por deslocamento, quadro a quadro (a cadeia ``sway_*`` em px inteiros)."""
    quer = ESPERADO["arvore/clipes"]
    feito = _hashes(ler(CASOS / "composicoes" / "arvore.r1.json", Composicao), quer)
    assert [k for k in quer if feito[k] != [quer[k]["tamanho"], quer[k]["rgba_sha256"]]] == []
    assert len({quer[k]["rgba_sha256"] for k in quer}) > 1  # ele se mexe


def _cata_vento(quadros: int) -> Composicao:
    return validar({"id": "cata_vento", "revision": 1, "description": "Fixture sintética: uma pá que gira",
                    "reference": "fixture sintética mínima", "tipo": "prop", "categoria": "objeto", "semente": 2,
                    "nos": [{"id": "pa", "peca": "poligono", "osso": "giro", "args": {
                        "pontos": [["-30cm", "0", "40cm"], ["30cm", "0", "40cm"], ["30cm", "0", "50cm"],
                                   ["-30cm", "0", "50cm"]], "material": "tabua"}}],
                    "vistas": {"S": {}}, "tracos": [],
                    "movimento": ["static", {"receita": "giro", "centro": ["0", "0", "45cm"], "periodo_ms": 800,
                                             "quadros": quadros}]}, Composicao, "teste")


def test_o_giro_fecha_o_laco_e_cada_quadro_gira() -> None:
    comp = _cata_vento(8)
    ir, est = ir_da_composicao(comp), estilo_render(estilo_base())
    pedidos, mp = movimento(comp)
    its, loop = instantes(ir, "spin", pedidos["spin"], mp)
    hashes = [hashlib.sha256(quadro_da_pose(ir, est, it.pose, "S").index.tobytes()).hexdigest() for it in its]
    assert loop and len(its) == 8 and len(set(hashes)) >= 4


def test_controle_o_giro_que_nao_divide_o_periodo_e_recusado_ja_na_previa() -> None:
    with pytest.raises(Recusa) as e:
        ir_da_composicao(_cata_vento(6))  # 800 ms não se divide em 6 quadros
    assert e.value.codigo == "GIRO" and "quadros" in e.value.dica


def _mourao(**mudar: Any) -> Composicao:
    dado = json.loads((CASOS.parent / "composicoes" / "mourao.r1.json").read_text(encoding="utf-8"))
    return validar({**dado, **mudar}, Composicao, "teste")


def test_o_traco_que_cita_parte_inexistente_e_recusado_com_as_parecidas() -> None:
    with pytest.raises(Recusa) as e:
        ir_da_composicao(_mourao(tracos=[{"id": "t", "description": "d", "parts": ["poste_frente"],
                                          "verification": "observable"}]))
    assert e.value.codigo == "TRACO" and "pfe previa" in e.value.dica and e.value.onde == "/tracos/0/parts/0"


def test_o_asset_maior_que_o_sprite_e_recusado_com_a_medida() -> None:
    dado = json.loads((CASOS.parent / "composicoes" / "mourao.r1.json").read_text(encoding="utf-8"))
    no = dado["nos"][0]
    with pytest.raises(Recusa) as e:
        ir_da_composicao(_mourao(categoria="estrutura", tracos=[],
                                 nos=[{**no, "args": {**no["args"], "altura": "30m"}}]))
    assert e.value.codigo == "TAMANHO" and "px por metro" in e.value.dica and "×" in e.value.mensagem


def test_o_no_que_nao_desenha_nada_e_recusado() -> None:
    no = {"id": "parede", "peca": "parede_tabuas", "args": {"x0": "-1m", "x1": "1m", "y": "0", "z0": "1m",
                                                             "altura": "1m"}}
    with pytest.raises(Recusa) as e:
        ir_da_composicao(_mourao(nos=[no], tracos=[]))
    assert e.value.codigo == "NO_VAZIO" and e.value.onde == "/nos/0/args"


def test_o_galho_longo_cabe_no_teto_de_vertices() -> None:
    """O galho grosso de uma copa de 8 m: o polígono do trecho tem no máximo 32 linhas (64 vértices)."""
    dado = json.loads((CASOS / "composicoes" / "arvore.r1.json").read_text(encoding="utf-8"))
    dado["medidas"] = {**dado["medidas"], "h": "6m", "a": "4m"}
    dado["categoria"] = "arvore_grande"
    ir = ir_da_composicao(validar(dado, Composicao, "teste"))
    assert any(p.id.startswith("galhos") for p in ir.parts)
