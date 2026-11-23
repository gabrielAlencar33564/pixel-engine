"""A escala do mundo, a mesma para todo asset: o humano de 1,65 m tem 54 px no mundo (~44 px na tela a 45°). O canvas
nunca define o tamanho: ele sai do tamanho do asset.

A régua do kit nasceu em px por personagem (``PX_POR_M``); a escala do mundo é o inteiro ``MPX_POR_M`` (milipixels por
metro). As duas diferem na quinta casa; as peças que medem na régua antiga multiplicam pelo fator ``K``.
"""

from __future__ import annotations

ESTATURA_M = 1.65
ESTATURA_PX = 54.0
PX_POR_M = ESTATURA_PX / ESTATURA_M
MPX_POR_M = round(PX_POR_M * 1000)  # 32727
PPM = MPX_POR_M / 1000  # px do mundo por metro
K = PPM / PX_POR_M  # a régua antiga do kit na escala do mundo


def m(metros: float) -> float:
    return metros * PPM
