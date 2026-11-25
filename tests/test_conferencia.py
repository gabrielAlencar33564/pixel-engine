"""A conferência do que se vê: a prévia diz, por vista, as partes que nenhum pixel mostra e os pixels de cada traço;
o traço observável sem pixel em nenhuma vista é recusado, na prévia e no build pelo mesmo caminho (I8), e o traço de
silhueta que nunca toca a borda da figura também. O chapéu cobre os olhos pela profundidade: sob a aba do viajante
eles aparecem, e a aba mais larga os esconde."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from pixel_forge.application.build import renderizar
from pixel_forge.application.previa import previa
from pixel_forge.contracts.carregar import validar
from pixel_forge.contracts.composicao import Composicao
from pixel_forge.core.recusa import Recusa

VIAJANTE = Path(__file__).parent / "fixtures" / "exemplos" / "viajante.r1.json"
OLHOS = {"id": "olhos", "description": "Os dois olhos no rosto", "parts": ["eye_l", "eye_r"]}


ABA_LARGA = "220%"  # a aba do viajante tem 150 % da cabeça e deixa os olhos à mostra; a de 220 % os cobre


def _viajante(tracos: list[dict[str, Any]], sem: str = "", aba: str = ABA_LARGA) -> Composicao:
    """O viajante parado com os traços dados, o chapéu com a aba ``aba`` (a larga, que cobre os olhos; vazia: a
    dele) e, com ``sem``, sem a peça desse nome."""
    dado = json.loads(VIAJANTE.read_text(encoding="utf-8"))
    dado["nos"] = [n for n in dado["nos"] if n["peca"] != sem]
    for no in dado["nos"]:
        if no["peca"] == "chapeu" and aba:
            no["args"]["largura"] = aba
    dado["tracos"] = tracos
    dado["movimento"] = ["idle"]  # o parado basta para a oclusão, e o build fica curto
    return validar(dado, Composicao, "teste")


def test_a_previa_diz_as_partes_que_ninguem_ve(tmp_path: Path) -> None:
    r = previa(_viajante([]), tmp_path)
    assert {"eye_l", "eye_r"} <= set(r["escondidas"]["S"])  # a aba larga do chapéu cobre os olhos
    assert "pants_thigh_r" in r["escondidas"]["W"]  # de perfil, a perna de cá cobre a de lá
    assert "hat_brim" not in r["escondidas"]["S"]


def test_sob_a_aba_do_viajante_os_olhos_aparecem(tmp_path: Path) -> None:
    r = previa(_viajante([{**OLHOS, "verification": "observable"}], aba=""), tmp_path)
    assert not {"eye_l", "eye_r"} & set(r["escondidas"].get("S", [])) and r["tracos"]["olhos"]["S"] > 0


def test_controle_sem_o_chapeu_os_olhos_nao_estao_escondidos(tmp_path: Path) -> None:
    r = previa(_viajante([{**OLHOS, "verification": "observable"}], sem="chapeu"), tmp_path)
    assert not {"eye_l", "eye_r"} & set(r["escondidas"].get("S", [])) and r["tracos"]["olhos"]["S"] > 0


def test_o_traco_observavel_escondido_e_recusado_na_previa_e_no_build(tmp_path: Path) -> None:
    comp = _viajante([{**OLHOS, "verification": "observable"}])
    for caminho in (lambda: previa(comp, tmp_path), lambda: renderizar(comp)):
        with pytest.raises(Recusa) as e:
            caminho()
        assert e.value.codigo == "TRACO_ESCONDIDO" and "escondidas" in e.value.dica and e.value.onde == "/tracos/0"


def test_controle_o_traco_so_visual_escondido_passa(tmp_path: Path) -> None:
    r = previa(_viajante([{**OLHOS, "verification": "visual_only"}]), tmp_path)
    assert not any(r["tracos"]["olhos"].values())


def test_o_traco_de_silhueta_tem_de_tocar_a_borda(tmp_path: Path) -> None:
    aba = {"id": "aba", "description": "A aba larga", "parts": ["hat_brim"], "verification": "observable"}
    # a aba de cima da gola: a de baixo toca a borda de perfil (a frente do peito), e a de cima fica por dentro
    gola = {"id": "gola", "description": "A aba de cima da gola", "parts": ["lapel_l"], "verification": "observable"}
    assert previa(_viajante([{**aba, "reads_in_silhouette": True}]), tmp_path)["tracos"]["aba"]["S"] > 0
    assert previa(_viajante([gola]), tmp_path)["tracos"]["gola"]["S"] > 0  # a gola se vê, mas por dentro do corpo
    with pytest.raises(Recusa) as e:
        previa(_viajante([{**gola, "reads_in_silhouette": True}]), tmp_path)
    assert e.value.codigo == "TRACO_SEM_SILHUETA"
