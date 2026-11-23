"""A prancha: os quadros no recorte real, sobre o tom médio do chão, ampliados por inteiro (até 4×), em fileiras
alinhadas pela base."""

from __future__ import annotations

from typing import Any

import numpy as np

Rgba = np.ndarray[Any, np.dtype[np.uint8]]
FUNDO = (112, 116, 104, 255)  # o tom médio do chão, para a prancha ler como no jogo
VAO = 4


def amplia_para(alto_px: int, alvo_px: int = 480) -> int:
    """A ampliação inteira (de 1 a 4) que leva o quadro mais alto perto de ``alvo_px``."""
    return max(1, min(4, alvo_px // max(1, alto_px)))


def no_fundo(rgba: Rgba, amplia: int) -> Rgba:
    fundo = np.empty_like(rgba)
    fundo[...] = FUNDO
    opaco = rgba[..., 3] == 255
    fundo[opaco] = rgba[opaco]
    return np.repeat(np.repeat(fundo, amplia, axis=0), amplia, axis=1)


def grade(linhas: list[list[Rgba]], amplia: int, chao: list[list[int]] | None = None) -> Rgba:
    """As fileiras de quadros, cada quadro sobre o fundo e ampliado; na fileira, os quadros se alinham pelo chão (a
    linha ``chao`` do pivô de cada um) ou, sem ela, pela base. O vão é transparente."""
    feitas = [[no_fundo(q, amplia) for q in linha] for linha in linhas]
    bases = [[c * amplia for c in cs] for cs in chao] if chao else [[q.shape[0] for q in linha] for linha in feitas]
    acima = [max(bs) for bs in bases]
    abaixo = [max(q.shape[0] - b for q, b in zip(linha, bs, strict=True)) for linha, bs in zip(feitas, bases,
                                                                                             strict=True)]
    largura = max(sum(q.shape[1] for q in linha) + VAO * (len(linha) - 1) for linha in feitas)
    out = np.zeros((sum(acima) + sum(abaixo) + VAO * (len(feitas) - 1), largura, 4), dtype=np.uint8)
    y = 0
    for i, linha in enumerate(feitas):
        x = 0
        for q, b in zip(linha, bases[i], strict=True):
            out[y + acima[i] - b:y + acima[i] - b + q.shape[0], x:x + q.shape[1]] = q
            x += q.shape[1] + VAO
        y += acima[i] + abaixo[i] + VAO
    return out
