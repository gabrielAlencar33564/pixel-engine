"""PNG RGBA (alfa 0 ou 255): gravar e ler."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

from .atlas import Rgba


def salvar_png(caminho: Path, rgba: Rgba) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(rgba, "RGBA").save(caminho)


def ler_rgba(caminho: Path) -> Rgba:
    with Image.open(caminho) as im:
        return np.asarray(im.convert("RGBA"), dtype=np.uint8).copy()
