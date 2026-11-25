"""O humano: o corpo vestido dá o mesmo pixel que o `pixel-engine` no parado e no andar, nas 8 direções, quadro a
quadro (no tronco, na cabeça, na abertura de braço, no balanço e no apoio dele: os da engine mudaram de propósito);
cada peça de roupa veste o corpo; o peito e a cintura são uma massa só, sem linha entre os dois; a saia segue a coxa
ao andar; e quem anda tem as 8 direções."""

from __future__ import annotations

import hashlib
import json
from typing import Any

import numpy as np
import pytest

from pixel_forge.application.build import instantes
from pixel_forge.application.catalogo import de_uma_peca
from pixel_forge.application.estilo import estilo_base
from pixel_forge.application.quadros import quadro_da_pose, quadro_de_repouso
from pixel_forge.contracts.carregar import ler, validar
from pixel_forge.contracts.composicao import Composicao
from pixel_forge.core.recusa import Recusa
from pixel_forge.design.asset import ir_da_composicao, movimento
from pixel_forge.design.kit.humano import Corpo, medidas
from pixel_forge.design.kit.registro import PECAS
from pixel_forge.motion.gerar import gerar_clipe
from pixel_forge.raster.contorno import QUATRO, contorno_interno
from pixel_forge.raster.estilo import estilo_render
from pixel_forge.raster.grade import Mascara, shift
from pixel_forge.raster.montagem import Camadas, compor, tabelas
from pixel_forge.rig.fk import Skeleton
from pixel_forge.rig.pose import rest_pose
from pixel_forge.views.projetor import project_view

from .oraculo import (
    CASOS,
    apoio_do_antigo,
    balanco_do_antigo,
    braco_do_antigo,
    cabeca_do_antigo,
    no_canvas_antigo,
    tronco_do_antigo,
)

ESPERADO: dict[str, Any] = json.loads((CASOS / "humanos.esperado.json").read_text(encoding="utf-8"))["casos"]
MAOS_SOBRE_OS_OMBROS = 1.5  # no repouso, de frente, as mãos ficam a até 1,5× a largura dos ombros uma da outra
# no andar de perfil as mãos se afastam de 30 % a 45 % da altura do corpo: o braço balança (não fica parado) e não
# estica para a frente (a câmera achata a altura, e o balanço do antigo lia como um braço apontando)
MAOS_NO_ANDAR = (0.30, 0.45)
PES_NO_PERFIL = 3  # no parado de perfil os pés ficam a 3 px ou mais um do outro: as duas pernas leem
VARIACOES = [(pid, nome, args) for pid, p in sorted(PECAS.items()) if p.tipo == "humanoide"
             for nome, args in p.variacoes]


def _comp(nome: str) -> Composicao:
    return ler(CASOS / "humanos" / f"{nome}.r1.json", Composicao)


def _hashes(comp: Composicao, quer: dict[str, Any]) -> dict[str, Any]:
    """O tamanho e o hash de cada quadro de cada clipe e vista, no canvas do antigo."""
    ir, style = ir_da_composicao(comp), estilo_base()
    est = estilo_render(style)
    pal = {p.index: (p.rgba[0], p.rgba[1], p.rgba[2], p.rgba[3]) for p in style.palette}
    pedidos, mp = movimento(comp)
    out = {}
    for clip, receita in pedidos.items():
        its, _ = instantes(ir, clip, receita, mp)
        for d in ir.views:
            for it in its:
                k = f"{clip}/{d}/{it.index}"
                if k not in quer:
                    continue
                feito = no_canvas_antigo(quadro_da_pose(ir, est, it.pose, d).to_rgba(pal), quer[k]["tamanho"])
                out[k] = [feito["tamanho"], feito["rgba_sha256"]]
    return out


@pytest.mark.slow
def test_o_humano_vestido_parado_e_andando_igual_ao_oraculo(monkeypatch: pytest.MonkeyPatch) -> None:
    tronco_do_antigo(monkeypatch)
    cabeca_do_antigo(monkeypatch)
    braco_do_antigo(monkeypatch)
    balanco_do_antigo(monkeypatch)
    apoio_do_antigo(monkeypatch)
    quer = ESPERADO["vestido"]
    feito = _hashes(_comp("vestido"), quer)
    diferentes = sorted(k for k in quer if feito.get(k) != [quer[k]["tamanho"], quer[k]["rgba_sha256"]])
    assert feito.keys() == quer.keys() and not diferentes, diferentes[:8]


@pytest.mark.parametrize(("peca", "nome", "args"), VARIACOES, ids=[f"{p}/{n}" for p, n, _ in VARIACOES])
def test_cada_peca_veste_o_corpo(peca: str, nome: str, args: dict[str, Any]) -> None:
    ir = ir_da_composicao(de_uma_peca(peca, args))
    q = quadro_de_repouso(ir, estilo_render(estilo_base()), "S")
    assert q.clipping_px == 0 and len(ir.views) == 8, (peca, nome)


def _maos_sobre_os_ombros() -> float:
    """A distância entre as mãos do corpo em repouso, de frente, sobre a largura dos ombros."""
    q = quadro_de_repouso(ir_da_composicao(de_uma_peca("corpo_humano", {})), estilo_render(estilo_base()), "S")
    return abs(q.landmarks["hand_l"][0] - q.landmarks["hand_r"][0]) / 256 / (2 * medidas(Corpo())["ombro_x"])


def test_no_repouso_as_maos_caem_junto_do_corpo() -> None:
    assert _maos_sobre_os_ombros() <= MAOS_SOBRE_OS_OMBROS


def test_controle_o_braco_do_antigo_deixa_as_maos_longe(monkeypatch: pytest.MonkeyPatch) -> None:
    braco_do_antigo(monkeypatch)
    assert _maos_sobre_os_ombros() > MAOS_SOBRE_OS_OMBROS


def _camadas(comp: Composicao) -> tuple[Camadas, Mascara]:
    """De frente: as camadas do quadro e os pixels da linha de contorno entre peças, pelo passe da engine."""
    ir, est = ir_da_composicao(comp), estilo_render(estilo_base())
    cam = compor(project_view(ir, rest_pose(Skeleton(ir.bones)), "S"), est.materials, ir.canvas.width,
                 ir.canvas.height)
    return cam, contorno_interno(cam, tabelas(cam, est.materials), np.zeros(cam.part.shape, dtype=np.uint16))


def _tronco_numa_massa(comp: Composicao, peito: str, cintura: str) -> tuple[bool, int]:
    """De frente: (o peito e a cintura sombreiam como um volume só, os pixels de linha de contorno entre os dois: os
    da cintura com a linha, vizinhos do peito e de nenhuma outra peça)."""
    cam, linha = _camadas(comp)
    do_peito, outra = cam.part == cam.num[peito], ~np.isin(cam.part, [0, cam.num[peito], cam.num[cintura]])
    junto, perto = (np.logical_or.reduce([shift(m, dx, dy) for dx, dy in QUATRO]) for m in (do_peito, outra))
    uma = {peito, cintura} <= cam.massa.keys() and bool(np.array_equal(cam.massa[peito], cam.massa[cintura]))
    return uma, int((linha & (cam.part == cam.num[cintura]) & junto & ~perto).sum())


def test_o_peito_e_a_cintura_sao_uma_massa_so_sem_linha_entre_os_dois() -> None:
    assert _tronco_numa_massa(de_uma_peca("corpo_humano", {}), "chest", "waist") == (True, 0)
    assert _tronco_numa_massa(_comp("vestido"), "jacket_chest", "jacket_waist") == (True, 0)


def test_controle_o_tronco_do_antigo_tem_a_linha_do_busto(monkeypatch: pytest.MonkeyPatch) -> None:
    tronco_do_antigo(monkeypatch)
    uma, linha = _tronco_numa_massa(de_uma_peca("corpo_humano", {}), "chest", "waist")
    assert not uma and linha >= 4  # a linha sob a bola do peito, de um braço ao outro
    assert not _tronco_numa_massa(_comp("vestido"), "jacket_chest", "jacket_waist")[0]


def _na_cabeca(com: str = "") -> Composicao:
    """O corpo vestido sem o chapéu (o cabelo preso e os olhos à mostra) e, com ``com``, com essa peça na cabeça."""
    dado = json.loads((CASOS / "humanos" / "vestido.r1.json").read_text(encoding="utf-8"))
    dado["nos"] = [n for n in dado["nos"] if n["peca"] != "chapeu"]
    if com:
        dado["nos"].append({"id": com, "peca": com, "args": {"material": "pano_ferrugem"}})
    dado["tracos"] = []
    return validar(dado, Composicao, "teste")


def _os_olhos_de_frente(comp: Composicao) -> tuple[int, int]:
    """De frente: (os pixels dos dois olhos, os pixels de linha de contorno vizinhos deles)."""
    cam, linha = _camadas(comp)
    olho = np.isin(cam.part, [cam.num["eye_l"], cam.num["eye_r"]])
    junto = np.logical_or.reduce([shift(olho, dx, dy) for dx, dy in QUATRO])
    return int(olho.sum()), int((linha & junto & ~olho).sum())


def test_os_olhos_sao_dois_pixels_sem_contorno_em_volta() -> None:
    pixels, linha = _os_olhos_de_frente(_na_cabeca())
    assert 2 <= pixels <= 4 and linha == 0


def test_controle_os_olhos_do_antigo_tem_a_mascara_em_volta(monkeypatch: pytest.MonkeyPatch) -> None:
    cabeca_do_antigo(monkeypatch)
    assert _os_olhos_de_frente(_na_cabeca())[1] >= 6  # o contorno em volta de cada olho, num rosto de 5 px


def test_o_lenco_deixa_o_rosto_e_o_no_fica_na_nuca() -> None:
    ir, est = ir_da_composicao(_na_cabeca("lenco")), estilo_render(estilo_base())
    frente, costas = (quadro_de_repouso(ir, est, d).visiveis for d in ("S", "N"))
    assert {"eye_l", "eye_r", "scarf", "jaw"} <= frente.keys() and "scarf_knot" not in frente
    assert "scarf_knot" in costas and "eye_l" not in costas


def _maos_no_andar_de_perfil() -> float:
    """O maior afastamento entre as mãos no andar de perfil (W), sobre a altura do corpo na tela (do pé à cabeça)."""
    comp = _comp("vestido")
    ir, est = ir_da_composicao(comp), estilo_render(estilo_base())
    pedidos, mp = movimento(comp)
    quadros = [quadro_da_pose(ir, est, it.pose, "W") for it in instantes(ir, "walk", pedidos["walk"], mp)[0]]
    altura = quadros[0].landmarks["foot_l"][1] - quadros[0].landmarks["head_top"][1]
    return max(abs(q.landmarks["hand_l"][0] - q.landmarks["hand_r"][0]) for q in quadros) / altura


def test_no_andar_de_perfil_o_braco_balanca_sem_apontar() -> None:
    assert MAOS_NO_ANDAR[0] <= _maos_no_andar_de_perfil() <= MAOS_NO_ANDAR[1]


def test_controle_o_balanco_do_antigo_estica_o_braco(monkeypatch: pytest.MonkeyPatch) -> None:
    balanco_do_antigo(monkeypatch)
    assert _maos_no_andar_de_perfil() > MAOS_NO_ANDAR[1]


def _pes_no_parado_de_perfil() -> float:
    """A distância na tela (px) entre os dois pés no parado de perfil (W)."""
    comp = _comp("vestido")
    ir = ir_da_composicao(comp)
    pedidos, mp = movimento(comp)
    q = quadro_da_pose(ir, estilo_render(estilo_base()), instantes(ir, "idle", pedidos["idle"], mp)[0][0].pose, "W")
    return abs(q.landmarks["foot_l"][0] - q.landmarks["foot_r"][0]) / 256


def test_no_parado_de_perfil_os_dois_pes_leem() -> None:
    assert _pes_no_parado_de_perfil() >= PES_NO_PERFIL


def test_controle_o_apoio_do_antigo_poe_um_pe_sobre_o_outro(monkeypatch: pytest.MonkeyPatch) -> None:
    apoio_do_antigo(monkeypatch)
    assert _pes_no_parado_de_perfil() < 1


def _rotacao_da_saia(comp: Composicao) -> list[int]:
    ir = ir_da_composicao(comp)
    pedidos, mp = movimento(comp)
    c = gerar_clipe(ir, pedidos["walk"], mp)
    return [k.bones["skirt_l"].rotation_mdeg for k in c.keyframes]


def test_a_saia_segue_a_coxa_ao_andar() -> None:
    dado = json.loads((CASOS / "humanos" / "vestido.r1.json").read_text(encoding="utf-8"))
    dado["nos"] = [n for n in dado["nos"] if n["peca"] != "calca"] + [
        {"id": "saia", "peca": "saia", "args": {"material": "pano_marrom"}}]
    rot = _rotacao_da_saia(validar(dado, Composicao, "teste"))
    assert max(rot) > 1000 and min(rot) < -1000


def test_controle_sem_a_saia_nao_ha_osso_de_saia() -> None:
    with pytest.raises(KeyError):
        _rotacao_da_saia(_comp("vestido"))


def test_controle_quem_anda_com_uma_vista_e_recusado() -> None:
    dado = json.loads((CASOS / "humanos" / "vestido.r1.json").read_text(encoding="utf-8"))
    dado["vistas"] = {"S": {}}
    with pytest.raises(Recusa) as e:
        ir_da_composicao(validar(dado, Composicao, "teste"))
    assert e.value.codigo == "VISTA" and "8 direções" in e.value.dica


def test_cada_direcao_tem_o_proprio_quadro() -> None:
    ir = ir_da_composicao(_comp("vestido"))
    est = estilo_render(estilo_base())
    hashes = {hashlib.sha256(quadro_de_repouso(ir, est, d).index.tobytes()).hexdigest() for d in ir.views}
    assert len(hashes) == 8
