"""O penedo: a pedra solta tem forma de pedra (faces chapadas, quinas e arestas), não de ovo; a semente muda a pedra;
e só as faces que a câmera vê se desenham. Os controles: o elipsoide (a pedra de antes) lê como ovo, e a mesma
semente dá a mesma pedra."""

from __future__ import annotations

from typing import Any

import numpy as np
import pytest

from pixel_forge.application.catalogo import de_uma_peca
from pixel_forge.application.estilo import estilo_base
from pixel_forge.application.quadros import quadro_de_repouso
from pixel_forge.contracts.carregar import validar
from pixel_forge.contracts.composicao import Composicao
from pixel_forge.design.asset import ir_da_composicao
from pixel_forge.design.kit.registro import PECAS
from pixel_forge.raster.estilo import estilo_render

SOMBRA_CHAO = (43, 38, 56)
# a pedra cobre no máximo 90 % do ovo inscrito na caixa dela (as quinas cortam o ovo e as faces retas saem dele); o
# elipsoide cobre 93 % ou mais. E a pedra tem ao menos 3 tons nas faces (a luz pela normal em faces chapadas)
OVO_MAX, OVO_DO_ELIPSOIDE, TONS_MIN = 0.90, 0.93, 3
# outra semente muda ao menos 10 % dos pixels da pedra
OUTRA_SEMENTE = 0.10
VARIACOES = [args for _, args in PECAS["penedo"].variacoes]


def _rgba(peca: str, args: dict[str, Any], semente: int = 11) -> np.ndarray:
    comp = de_uma_peca(peca, args).model_dump()
    comp["semente"] = semente
    style = estilo_base()
    q = quadro_de_repouso(ir_da_composicao(validar(comp, Composicao, "penedo")), estilo_render(style), "S")
    pal = {p.index: (p.rgba[0], p.rgba[1], p.rgba[2], p.rgba[3]) for p in style.palette}
    return np.asarray(q.to_rgba(pal))


def _mascara(rgba: np.ndarray) -> np.ndarray:
    """Os pixels da pedra (sem a sombra no chão)."""
    chao = np.all(rgba[..., :3] == SOMBRA_CHAO, axis=-1)
    return np.asarray((rgba[..., 3] > 0) & ~chao)


def _no_ovo(m: np.ndarray) -> float:
    """A parte da pedra que cabe no ovo inscrito na caixa dela, sobre o tamanho dos dois (a interseção sobre a
    união): 1 é um ovo perfeito."""
    ys, xs = np.nonzero(m)
    cy, cx = (ys.min() + ys.max()) / 2, (xs.min() + xs.max()) / 2
    ry, rx = (ys.max() - ys.min() + 1) / 2, (xs.max() - xs.min() + 1) / 2
    yy, xx = np.mgrid[: m.shape[0], : m.shape[1]]
    ovo = ((yy - cy) / ry) ** 2 + ((xx - cx) / rx) ** 2 <= 1
    return float((m & ovo).sum() / (m | ovo).sum())


@pytest.mark.parametrize("args", VARIACOES)
def test_a_pedra_tem_quinas_e_nao_e_um_ovo(args: dict[str, Any]) -> None:
    rgba = _rgba("penedo", args)
    m = _mascara(rgba)
    tons = {tuple(c) for c in rgba[m][:, :3]}
    assert _no_ovo(m) <= OVO_MAX and len(tons) >= TONS_MIN


def test_controle_o_elipsoide_le_como_ovo() -> None:
    m = _mascara(_rgba("elipsoide", {"centro": ["0", "0", "35cm"], "raios": ["60cm", "45cm", "35cm"],
                                     "material": "pedra"}))
    assert _no_ovo(m) >= OVO_DO_ELIPSOIDE


def test_outra_semente_da_outra_pedra() -> None:
    a, b = (_mascara(_rgba("penedo", VARIACOES[0], s)) for s in (11, 12))
    h, w = max(a.shape[0], b.shape[0]), max(a.shape[1], b.shape[1])
    a, b = (np.pad(x, ((0, h - x.shape[0]), (0, w - x.shape[1]))) for x in (a, b))
    assert (a ^ b).sum() / (a | b).sum() >= OUTRA_SEMENTE


def test_controle_a_mesma_semente_da_a_mesma_pedra() -> None:
    assert np.array_equal(_rgba("penedo", VARIACOES[0], 11), _rgba("penedo", VARIACOES[0], 11))


def test_so_as_faces_que_a_camera_ve_se_desenham() -> None:
    ir = ir_da_composicao(de_uma_peca("penedo", VARIACOES[0]))
    q = quadro_de_repouso(ir, estilo_render(estilo_base()), "S")
    faces = [p.id for p in ir.parts if "fenda" not in p.id]
    assert len(faces) >= 5 and all(pid in q.visiveis for pid in faces)


def test_o_musgo_fica_nas_faces_de_cima() -> None:
    ir = ir_da_composicao(de_uma_peca("penedo", VARIACOES[1]))
    verdes = [p for p in ir.parts if p.material in ("musgo", "capim_claro", "capim_escuro")]
    assert verdes and len(verdes) < len(ir.parts)
