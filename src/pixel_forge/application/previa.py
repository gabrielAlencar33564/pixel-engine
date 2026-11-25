"""A prévia, o checar e o conjunto: o que a prévia aceita, o build aceita (I8). A prévia confere o repouso de cada
vista com as recusas do build (o porte, o quadro cortado, as cores, o traço que não lê), grava a prancha e diz, por
vista, as partes que ninguém vê e os pixels de cada traço (e, da flora, as medidas e os achados da crítica); o checar
confere todos os quadros do build sem gravar nada; o conjunto põe assets lado a lado, na mesma escala, com o humano
de 1,65 m de régua."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from ..contracts.carregar import validar
from ..contracts.composicao import Composicao
from ..core.direcoes import DIRECOES
from ..design.asset import ir_da_composicao
from ..design.escala import ESTATURA_M
from ..design.habito import expandida
from ..design.porte import altura_m, conferir_porte
from ..export.imagem import salvar_png
from ..quality.quadro import conferir_quadro, conferir_tracos, leitura_dos_tracos
from ..raster.estilo import estilo_render
from ..raster.renderer import Quadro
from . import critica
from .build import renderizar
from .catalogo import em_faixas
from .estilo import estilo_base
from .prancha import amplia_para, grade
from .quadros import quadro_de_repouso

REGUA = {"id": "regua", "revision": 1, "description": "O humano de 1,65 m, a régua do conjunto",
         "reference": "o cânone do kit", "tipo": "humanoide", "categoria": "humano", "semente": 1,
         "nos": [{"id": "corpo", "peca": "corpo_humano", "args": {}}], "vistas": dict.fromkeys(DIRECOES, {}),
         "movimento": ["idle"], "tracos": []}


def previa(comp: Composicao, acervo: Path) -> dict[str, Any]:
    t0 = time.perf_counter()
    ir, style = ir_da_composicao(comp), estilo_base()
    conferir_porte(comp.categoria, ir)
    est = estilo_render(style)
    pal = {p.index: (p.rgba[0], p.rgba[1], p.rgba[2], p.rgba[3]) for p in style.palette}
    quadros = {d: quadro_de_repouso(ir, est, d) for d in ir.views}
    for d, q in quadros.items():
        conferir_quadro(q, style, f"previa/{d}")
    por_vista: dict[str, list[Quadro]] = {d: [q] for d, q in quadros.items()}
    conferir_tracos(comp.tracos, por_vista)
    imagens = [q.to_rgba(pal) for q in quadros.values()]
    # as partes que a vista desenha (a peça não as escondeu) e que não ganham pixel: outra as cobre. O volume de
    # uma massa de folhagem e o miolo dela não contam: o lado de lá e o de dentro da copa ficam sempre escondidos
    soltas = [p.id for p in ir.parts if not any(t.startswith("massa_") or t == "miolo" for t in p.tags)]
    escondidas = {d: [p for p in soltas if p not in ir.views[d].visibility and p not in q.visiveis]
                  for d, q in quadros.items()}
    amplia = amplia_para(ir.canvas.height)
    alvo = acervo / "previas" / f"{comp.id}.r{comp.revision}.png"
    salvar_png(alvo, grade([imagens], amplia))
    alt = altura_m(ir)
    out = {"prancha": str(alvo), "amplia": amplia, "vistas": list(ir.views),
           "canvas": [ir.canvas.width, ir.canvas.height], "altura_m": round(alt, 2),
           "porte": f"{alt / ESTATURA_M:.2f}× o humano ({comp.categoria})",
           "partes": em_faixas([p.id for p in ir.parts]),
           "escondidas": {d: ps for d, ps in escondidas.items() if ps},
           "tracos": leitura_dos_tracos(comp.tracos, por_vista)}
    if comp.planta is not None:  # os nós que a engine derivou dos traços: para conferir, ou copiar e mexer
        out["nos"] = [n.model_dump(mode="json", exclude_defaults=True) for n in expandida(comp).nos]
    if critica.e_flora(comp):  # a flora já sai medida: os achados da crítica, sem as irmãs do acervo
        out["critica"] = critica.da_previa(comp, ir, quadros.get("S", next(iter(quadros.values()))))
    return {**out, "segundos": round(time.perf_counter() - t0, 2)}


def checar(comp: Composicao) -> dict[str, Any]:
    t0 = time.perf_counter()
    r = renderizar(comp)
    return {"ok": True, "clipes": sorted({s.clip for s in r.sequencias}), "vistas": list(r.ir.views),
            "quadros": sum(len(s.quadros) for s in r.sequencias), "segundos": round(time.perf_counter() - t0, 2)}


def conjunto(comps: list[Composicao], acervo: Path) -> dict[str, Any]:
    """Os assets na vista S, em repouso, lado a lado pela base e na mesma escala, com o humano de régua à esquerda."""
    style = estilo_base()
    est = estilo_render(style)
    pal = {p.index: (p.rgba[0], p.rgba[1], p.rgba[2], p.rgba[3]) for p in style.palette}
    todos = [validar(REGUA, Composicao, "régua"), *comps]
    irs = [ir_da_composicao(c) for c in todos]
    imagens = [quadro_de_repouso(ir, est, next(iter(ir.views))).to_rgba(pal) for ir in irs]
    alvo = acervo / "conjuntos" / ("+".join(c.id for c in comps) + ".png")
    salvar_png(alvo, grade([imagens], amplia_para(max(i.shape[0] for i in imagens)),
                           [[ir.canvas.pivot_px[1] for ir in irs]]))
    return {"prancha": str(alvo), "regua": "humano de 1,65 m à esquerda",
            "alturas": {c.id: f"{altura_m(ir):.2f} m ({altura_m(ir) / ESTATURA_M:.2f}× o humano)"
                        for c, ir in zip(comps, irs[1:], strict=True)}}
