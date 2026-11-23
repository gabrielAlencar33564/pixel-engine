"""Aritmética de ponto fixo determinística (contrato em ``docs/coordenadas.md``).

- Coordenadas persistentes: inteiros q8 (256 = 1 px). Posições internas: q8 << 12 (1/2^20 px).
- Ângulos: inteiros em miligraus. A trigonometria sai de séries de Taylor em inteiros Python (Q30), sem ``math.sin``:
  o resultado é o mesmo em qualquer máquina.
"""

from __future__ import annotations

from functools import lru_cache
from math import isqrt

Q30_SHIFT = 30
ONE_Q30 = 1 << Q30_SHIFT
POS_EXTRA_SHIFT = 12
ONE_PX_POS = 1 << (8 + POS_EXTRA_SHIFT)
FULL_TURN_MDEG = 360_000

_Q60 = 60
_PI_Q60 = (314159265358979323846264338327950288419716939937510 << _Q60) // 10**50


def q8_to_pos(value_q8: int) -> int:
    return value_q8 << POS_EXTRA_SHIFT


def pos_to_q8(value_pos: int) -> int:
    return (value_pos + (1 << (POS_EXTRA_SHIFT - 1))) >> POS_EXTRA_SHIFT


def _serie(x_q60: int, primeiro: int, n0: int) -> int:
    """A série alternada de Taylor a partir do termo ``primeiro`` (seno: x, n0 = 2; cosseno: 1, n0 = 1)."""
    x2 = (x_q60 * x_q60) >> _Q60
    termo, soma, n, sinal = primeiro, primeiro, 1, -1
    while True:
        termo = (termo * x2) >> _Q60
        termo //= (2 * n + n0 - 2) * (2 * n + n0 - 1)
        if termo == 0:
            return soma
        soma += sinal * termo
        sinal, n = -sinal, n + 1


@lru_cache(maxsize=65536)
def sin_cos_q30(mdeg: int) -> tuple[int, int]:
    """(seno, cosseno) em Q30 de um ângulo inteiro em miligraus."""
    quadrante, r = divmod(mdeg % FULL_TURN_MDEG, 90_000)
    if r <= 45_000:
        x = r * _PI_Q60 // 180_000
        s60, c60 = _serie(x, x, 2), _serie(x, 1 << _Q60, 1)
    else:
        x = (90_000 - r) * _PI_Q60 // 180_000
        c60, s60 = _serie(x, x, 2), _serie(x, 1 << _Q60, 1)
    desloca = _Q60 - Q30_SHIFT
    s = (s60 + (1 << (desloca - 1))) >> desloca
    c = (c60 + (1 << (desloca - 1))) >> desloca
    return ((s, c), (c, -s), (-s, -c), (-c, s))[quadrante]


def round_half_up_div(n: int, d: int) -> int:
    """floor(n/d + 1/2) para d > 0, correto para negativos (sem ties-to-even)."""
    return (2 * n + d) // (2 * d)


def normalize_mdeg(a: int) -> int:
    """O ângulo em (-180000, 180000]."""
    a %= FULL_TURN_MDEG
    return a - FULL_TURN_MDEG if a > 180_000 else a


def shortest_arc_mdeg(a: int, b: int) -> int:
    """b - a pelo menor arco; o empate de 180° vale +180000."""
    d = (b - a) % FULL_TURN_MDEG
    return d - FULL_TURN_MDEG if d > 180_000 else d


def _atan_primeiro_octante(y: int, x: int) -> int:
    """O ângulo (mdeg) de 0 <= y <= x, x > 0, por bisseção exata em inteiros e o vizinho de menor resíduo."""
    lo, hi = 0, 45_000
    while lo < hi:
        mid = (lo + hi + 1) // 2
        s, c = sin_cos_q30(mid)
        if s * x <= y * c:
            lo = mid
        else:
            hi = mid - 1
    if lo < 45_000:
        s0, c0 = sin_cos_q30(lo)
        s1, c1 = sin_cos_q30(lo + 1)
        if abs(s1 * x - y * c1) < abs(s0 * x - y * c0):
            lo += 1
    return lo


def atan2_mdeg(y: int, x: int) -> int:
    """atan2 determinístico em miligraus, em (-180000, 180000]."""
    if x == 0 and y == 0:
        return 0
    ax, ay = abs(x), abs(y)
    base = _atan_primeiro_octante(ay, ax) if ay <= ax else 90_000 - _atan_primeiro_octante(ax, ay)
    if x >= 0:
        return normalize_mdeg(base if y >= 0 else -base)
    return normalize_mdeg(180_000 - base if y >= 0 else -(180_000 - base))


def acos_mdeg(num: int, den: int) -> int:
    """acos(num/den) em mdeg, com num/den limitado a [-1, 1]."""
    num = max(-den, min(den, num)) << 32
    den <<= 32
    return atan2_mdeg(isqrt(den * den - num * num), num)
