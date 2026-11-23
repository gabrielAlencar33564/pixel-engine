"""As camadas: a base não importa o que está acima dela. O render (``views``, ``raster``), o rig e o export não
importam o desenho (``design``) nem o movimento (``motion``); o núcleo e os contratos não importam nada acima."""

from __future__ import annotations

from pathlib import Path

from .fontes import SRC, arquivos_py, importados

PACOTE = "pixel_forge"
ACIMA_DO_RENDER = {"design", "motion", "quality", "application", "cli"}
PROIBIDO = {
    "core": {"contracts", "views", "raster", "rig", "export", *ACIMA_DO_RENDER},
    "contracts": {"views", "raster", "rig", "export", *ACIMA_DO_RENDER},
    "views": ACIMA_DO_RENDER,
    "raster": ACIMA_DO_RENDER,
    "rig": ACIMA_DO_RENDER,
    "export": ACIMA_DO_RENDER,
}


def violacoes(raiz: Path) -> list[str]:
    out = []
    for arquivo in arquivos_py(raiz / PACOTE):
        camada = arquivo.relative_to(raiz / PACOTE).parts[0].removesuffix(".py")
        for alvo in sorted(importados(arquivo, raiz)):
            partes = alvo.split(".")
            if partes[0] == PACOTE and len(partes) > 1 and partes[1] in PROIBIDO.get(camada, set()):
                out.append(f"{arquivo.relative_to(raiz).as_posix()} importa {alvo}")
    return out


def test_camadas() -> None:
    assert violacoes(SRC) == []


def test_controle_o_render_que_importa_o_desenho_e_achado(tmp_path: Path) -> None:
    raster = tmp_path / PACOTE / "raster"
    raster.mkdir(parents=True)
    (raster / "passe.py").write_text("from ..design.kit import peca\nfrom ..core import q8\n", encoding="utf-8")
    (raster / "outro.py").write_text("import pixel_forge.motion.passada\n", encoding="utf-8")
    assert violacoes(tmp_path) == [
        "pixel_forge/raster/outro.py importa pixel_forge.motion.passada",
        "pixel_forge/raster/passe.py importa pixel_forge.design.kit",
        "pixel_forge/raster/passe.py importa pixel_forge.design.kit.peca",
    ]
