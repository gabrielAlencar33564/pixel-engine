"""Olhar o pacote como o jogo o lê: a prancha de todos os quadros (uma fileira por clipe e direção, no recorte real,
ampliada até 4×) e os números que se leem antes da imagem."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from ..export.imagem import salvar_png
from ..export.pacote import ler_pacote
from .exportar import pasta_do_pacote
from .prancha import amplia_para, grade


def olhar(build: Path) -> dict[str, Any]:
    pasta = pasta_do_pacote(build)
    pac = ler_pacote(pasta)
    linhas = [[pac.quadros[n].rgba for n in seq["frames"]] for _, seq in sorted(pac.sequencias.items())]
    quadros = [q for linha in linhas for q in linha]
    cores = max(len({tuple(c) for c in q[q[..., 3] == 255].tolist()}) for q in quadros)
    amplia = amplia_para(max(q.shape[0] for q in quadros) * len(linhas), 960)
    alvo = build.parent.parent / "olhar" / f"{build.name}.png"
    salvar_png(alvo, grade(linhas, amplia))
    return {"prancha": str(alvo), "amplia": amplia, "status": pac.status, "art_review": pac.art_review,
            "clipes": sorted({c for c, _ in pac.sequencias}), "direcoes": pac.directions, "quadros": len(quadros),
            "canvas": [int(quadros[0].shape[1]), int(quadros[0].shape[0])], "cores_no_quadro": cores,
            "pixels_opacos": int(max(np.count_nonzero(q[..., 3] == 255) for q in quadros))}
