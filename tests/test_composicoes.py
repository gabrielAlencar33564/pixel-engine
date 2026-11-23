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

from pixel_forge.application.estilo import estilo_base
from pixel_forge.application.quadros import quadro_de_repouso
from pixel_forge.contracts.base import Direcao
from pixel_forge.contracts.carregar import ler
from pixel_forge.contracts.composicao import Composicao
from pixel_forge.design.asset import ir_da_composicao
from pixel_forge.raster.estilo import estilo_render

from .oraculo import CASOS

ESPERADO: dict[str, Any] = json.loads((CASOS / "composicoes.esperado.json").read_text(encoding="utf-8"))["casos"]
SOMBRA_GIRADA = {("marco", "E"), ("marco", "N"), ("marco", "W")}
VISTAS = [(c, v) for c in sorted(ESPERADO) for v in ESPERADO[c] if (c, v) not in SOMBRA_GIRADA]


def rgba(nome: str, vista: str) -> np.ndarray[Any, np.dtype[np.uint8]]:
    style = estilo_base()
    comp = ler(CASOS / "composicoes" / f"{nome}.r1.json", Composicao)
    q = quadro_de_repouso(ir_da_composicao(comp), estilo_render(style), cast(Direcao, vista))
    return q.to_rgba({p.index: (p.rgba[0], p.rgba[1], p.rgba[2], p.rgba[3]) for p in style.palette})


@pytest.mark.parametrize(("nome", "vista"), VISTAS, ids=[f"{c}/{v}" for c, v in VISTAS])
def test_igual_ao_oraculo(nome: str, vista: str) -> None:
    img = rgba(nome, vista)
    quer = ESPERADO[nome][vista]
    assert [[img.shape[1], img.shape[0]], hashlib.sha256(img.tobytes()).hexdigest()] == [quer["tamanho"],
                                                                                        quer["rgba_sha256"]]


def _altura_da_sombra(img: np.ndarray[Any, np.dtype[np.uint8]]) -> int:
    chao = next(p.rgba for p in estilo_base().palette if p.id == "sombra_chao")
    ys = np.nonzero(np.all(img == np.array(chao, dtype=np.uint8), axis=-1))[0]
    return int(ys.max() - ys.min() + 1)


def test_a_sombra_de_contato_tem_a_mesma_altura_em_toda_vista() -> None:
    alturas = {v: _altura_da_sombra(rgba("marco", v)) for v in ("S", "E", "N", "W")}
    assert max(alturas.values()) - min(alturas.values()) <= 1, alturas


def test_controle_o_oraculo_acusa_a_sombra_girada_de_antes() -> None:
    feitos = {v: hashlib.sha256(rgba("marco", v).tobytes()).hexdigest() for v in ("E", "N", "W")}
    assert all(feitos[v] != ESPERADO["marco"][v]["rgba_sha256"] for v in feitos)


def test_composicao_de_fixture_tem_um_arquivo_por_caso() -> None:
    assert sorted(p.stem.removesuffix(".r1") for p in (CASOS / "composicoes").glob("*.json")) == sorted(ESPERADO)


def test_controle_a_ancora_citada_antes_de_ser_deixada_e_recusada(tmp_path: Path) -> None:
    from pixel_forge.core.recusa import Recusa

    dado = json.loads((CASOS / "composicoes" / "arvore.r1.json").read_text(encoding="utf-8"))
    dado["nos"] = [dado["nos"][0], dado["nos"][2], dado["nos"][1]]
    arq = tmp_path / "x.json"
    arq.write_text(json.dumps(dado), encoding="utf-8")
    with pytest.raises(Recusa) as e:
        ir_da_composicao(ler(arq, Composicao))
    assert e.value.codigo == "ANCORA" and "acima" in e.value.dica
