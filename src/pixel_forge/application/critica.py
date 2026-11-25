"""A crítica da flora: a revisão que outro agente faz antes da entrega. A engine mede o quadro (``quality/flora.py``),
compara a planta com as irmãs do acervo (a mesma categoria ou o mesmo porte), grava a prancha de quem revisa (o
sprite e a silhueta dele; embaixo, as irmãs mais parecidas) e as perguntas que só o olho responde. Quem revisa não é
quem compôs: ele responde cada pergunta com uma nota, e o registro fica em ``criticas/<asset>.r<n>.json`` do acervo.

A crítica passa sem defeito medido e com todas as respostas boas; sem ela o pacote da flora não sai. Ela não aprova
a arte (isso é do dono, em ``revisao.py``): tira o defeito antes de o dono olhar."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

from ..contracts.carregar import ler
from ..contracts.composicao import Composicao
from ..contracts.ir import AssetIR
from ..core.recusa import Recusa
from ..design.asset import ir_da_composicao
from ..design.habito import expandida
from ..design.kit.registro import PECAS
from ..export.atlas import Rgba
from ..export.imagem import salvar_png
from ..quality import flora
from ..raster.estilo import estilo_render
from ..raster.renderer import Quadro
from .estilo import estilo_base
from .exportar import ler_manifesto
from .prancha import amplia_para, grade
from .quadros import quadro_de_repouso

ARVORES = ("arvore_grande", "arvore_pequena")
FLORA = (*ARVORES, "arbusto")
# o papel da parte de uma peça genérica (o elipsoide, o traço) sai do material dela, pelo começo do id
MATERIAIS = {"folhagem": ("copa_", "folh", "agulha", "capim", "musgo"), "lenho": ("casca", "madeira")}
SILHUETA = (24, 24, 28, 255)
NOTA_MINIMA = 12  # caracteres: a resposta diz o que se viu, não só "ok"
PERGUNTAS = {
    "silhueta": "Só pela silhueta (o painel escuro), dá para dizer que planta é e de que porte?",
    "massa_de_luz": "A folhagem lê como uma massa com um lado claro (em cima, à esquerda) e um escuro, com relevo "
                    "dentro, e não como bolas soltas nem como uma mancha chapada?",
    "assenta": "O tronco ou o pé aparece, tem a grossura que a altura pede e assenta no chão, com a sombra saindo "
               "dele?",
    "outra_coisa": "Nada no sprite lê como outra coisa (ovo, pedra, brócolis, funil, dente, guarda-chuva)?",
    "ficha": "O que a ficha diz que dá vida à espécie (a forma da copa, o tronco, a cor) está no sprite?",
    "irmas": "Ao lado das irmãs (a fileira de baixo: as plantas do acervo da mesma categoria ou do mesmo porte), é "
             "outra planta, com outra construção e outra silhueta, e não a mesma em outro tamanho ou cor?",
}
SEM_IRMA = ("O acervo ainda não tem outra planta da mesma categoria nem do mesmo porte (a fileira de baixo falta): "
            "não há com que comparar. Responda ok e diga isso na nota.")


def _papeis(comp: Composicao, partes: dict[str, str]) -> dict[str, str]:
    """O papel de cada parte na planta: o da peça do nó que a desenhou (o nó de id mais longo que a prefixa) ou,
    na peça genérica, o do material dela."""
    nos = sorted(comp.nos, key=lambda n: -len(n.id))
    out: dict[str, str] = {}
    for p, material in partes.items():
        no = next((n for n in nos if p == n.id or p.startswith(f"{n.id}_")), None)
        da_peca = PECAS[no.peca].flora if no is not None and no.peca in PECAS else ""
        out[p] = da_peca or next((papel for papel, ids in MATERIAIS.items() if material.startswith(ids)), "")
    return out


def _mascaras(comp: Composicao, q: Quadro, materiais: dict[str, str]) -> tuple[Any, Any, Any]:
    """A folhagem, o lenho e a figura no quadro, pelo dono de cada pixel."""
    papeis = _papeis(comp, {p: materiais[p] for p in q.part_table})
    nums = {papel: [i + 1 for i, p in enumerate(q.part_table) if papeis[p] == papel] for papel in ("folhagem", "lenho")}
    return np.isin(q.dono, nums["folhagem"]), np.isin(q.dono, nums["lenho"]), q.dono != 0


def e_flora(comp: Composicao) -> bool:
    """A planta: a categoria de árvore ou de arbusto, os traços em ``planta``, ou qualquer asset com uma peça de
    folhagem."""
    de_planta = any(no.peca in PECAS and PECAS[no.peca].flora in ("folhagem", "lamina") for no in comp.nos)
    return comp.categoria in FLORA or comp.planta is not None or de_planta


def leitura(comp: Composicao, ir: AssetIR, q: Quadro) -> flora.Leitura:
    """As medidas da flora num quadro da composição."""
    lut = np.zeros(65536, dtype=np.float64)
    for p in estilo_base().palette:
        lut[p.index] = 0.299 * p.rgba[0] + 0.587 * p.rgba[1] + 0.114 * p.rgba[2]
    folhagem, lenho, figura = _mascaras(expandida(comp), q, {p.id: p.material for p in ir.parts})
    return flora.ler(folhagem, lenho, figura, lut[q.index])


def da_previa(comp: Composicao, ir: AssetIR, q: Quadro) -> dict[str, Any]:
    """O que a prévia já diz da flora (sem as irmãs): as medidas e os achados do quadro."""
    m = leitura(comp, ir, q)
    return {"medidas": m.numeros(), "achados": flora.achados(m, comp.categoria in ARVORES, {})}


def medir(comp: Composicao) -> tuple[flora.Leitura, Quadro, Rgba]:
    """A composição montada e medida na vista do jogo: as medidas, o quadro e a imagem."""
    style = estilo_base()
    ir = ir_da_composicao(comp)
    q = quadro_de_repouso(ir, estilo_render(style), "S" if "S" in ir.views else next(iter(ir.views)))
    return (leitura(comp, ir, q), q,
            q.to_rgba({p.index: (p.rgba[0], p.rgba[1], p.rgba[2], p.rgba[3]) for p in style.palette}))


def irmas(comp: Composicao, m: flora.Leitura, acervo: Path) -> dict[str, tuple[str, flora.Leitura, Quadro, Rgba]]:
    """As outras plantas do acervo que dividem o cenário com esta, cada uma na última revisão que ainda se lê e se
    monta, com a categoria dela: as da mesma categoria e as de outra no mesmo porte (a touceira de objeto ao lado da
    de arbusto, a árvore pequena ao lado da grande). A de outra categoria e outro porte não é irmã: a moita redonda
    e a copa redonda coincidem na assinatura e não no cenário."""
    ultimas: dict[str, tuple[int, Path]] = {}
    for p in sorted((acervo / "composicoes").glob("*.r*.json")):
        r = re.fullmatch(r"(.+)\.r(\d+)\.json", p.name)
        if r and r.group(1) != comp.id and int(r.group(2)) >= ultimas.get(r.group(1), (0, p))[0]:
            ultimas[r.group(1)] = (int(r.group(2)), p)
    out: dict[str, tuple[str, flora.Leitura, Quadro, Rgba]] = {}
    for ident, (_, p) in ultimas.items():
        try:
            irma = ler(p, Composicao)
            medida = medir(irma) if e_flora(irma) else None
        except Recusa:  # a composição de um formato ou de uma peça que saiu não é mais irmã de ninguém
            continue
        if medida is not None and (irma.categoria == comp.categoria or flora.porte(m, medida[0]) >= flora.MESMO_PORTE):
            out[ident] = (irma.categoria, *medida)
    return out


def _silhueta(q: Quadro) -> Rgba:
    out = np.zeros((*q.dono.shape, 4), dtype=np.uint8)
    out[q.dono != 0] = SILHUETA
    return out


def _arquivo(build: Path) -> Path:
    m = ler_manifesto(build)
    return build.parent.parent / "criticas" / f"{m['asset']['id']}.r{m['asset']['revision']}.json"


def _composicao(build: Path) -> Composicao | None:
    m = ler_manifesto(build)
    alvo = build.parent.parent / "composicoes" / f"{m['asset']['id']}.r{m['asset']['revision']}.json"
    return ler(alvo, Composicao) if alvo.is_file() else None


def registros(build: Path) -> list[dict[str, Any]]:
    """Os registros da crítica deste build (o último vale)."""
    alvo = _arquivo(build)
    todos: list[dict[str, Any]] = json.loads(alvo.read_text(encoding="utf-8")) if alvo.is_file() else []
    return [r for r in todos if r["build_id"] == ler_manifesto(build)["build_id"]]


def _gravar(build: Path, registro: dict[str, Any]) -> dict[str, Any]:
    alvo = _arquivo(build)
    todos: list[dict[str, Any]] = json.loads(alvo.read_text(encoding="utf-8")) if alvo.is_file() else []
    alvo.parent.mkdir(parents=True, exist_ok=True)
    registro = {**registro, "quando": datetime.now(UTC).isoformat(timespec="seconds")}
    alvo.write_text(json.dumps([*todos, registro], ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return registro


def criticar(build: Path) -> dict[str, Any]:
    """Mede o build, compara com as irmãs do acervo, grava a prancha de quem revisa e abre o registro (pendente)."""
    comp = _composicao(build)
    if comp is None or not e_flora(comp):
        raise Recusa("CRITICA", f"{build.name} não é um build de flora com a composição no acervo.",
                     "A crítica mede a folhagem: vale para o asset com uma peça de copa ou de touceira, construído "
                     "com `pfe build`.")
    acervo = build.parent.parent
    m, q, rgba = medir(comp)
    todas = irmas(comp, m, acervo)
    perto = {i: (c, flora.semelhanca(m.assinatura, mi.assinatura)) for i, (c, mi, _, _) in todas.items()}
    vizinhas = sorted(perto, key=lambda i: -perto[i][1])[:flora.IRMAS_NA_PRANCHA]
    linhas = [[rgba, _silhueta(q)]]
    if vizinhas:
        linhas.append([todas[i][3] for i in vizinhas])
        linhas.append([_silhueta(todas[i][2]) for i in vizinhas])
    alvo = acervo / "criticas" / f"{build.name}.png"
    salvar_png(alvo, grade(linhas, amplia_para(max(i.shape[0] for linha in linhas for i in linha), 300)))
    achados = flora.achados(m, comp.categoria in ARVORES, perto)
    return _gravar(build, {
        "build_id": ler_manifesto(build)["build_id"], "prancha": str(alvo), "medidas": m.numeros(),
        "irmas": {i: {"categoria": perto[i][0], "semelhanca": round(perto[i][1], 3)} for i in vizinhas},
        "parecida_a_partir_de": flora.PARECIDA, "achados": achados, "ficha": comp.reference,
        "perguntas": PERGUNTAS if vizinhas else {**PERGUNTAS, "irmas": SEM_IRMA}, "parecer": None,
        "veredito": "pendente"})


def _respostas(arquivo: Path) -> dict[str, dict[str, Any]]:
    try:
        dado = json.loads(arquivo.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        dado = None
    r = dado.get("respostas") if isinstance(dado, dict) else None
    ok = isinstance(r, dict) and set(r) == set(PERGUNTAS) and all(
        isinstance(v, dict) and isinstance(v.get("ok"), bool) and isinstance(v.get("nota"), str)
        and len(v["nota"].strip()) >= NOTA_MINIMA for v in r.values())
    if not ok or not isinstance(r, dict):
        raise Recusa("PARECER", f"O parecer em {arquivo} não responde às perguntas da crítica.",
                     'O arquivo é {"respostas": {"<pergunta>": {"ok": true ou false, "nota": "o que se viu"}}}, com '
                     f"todas as perguntas ({', '.join(PERGUNTAS)}) e a nota de cada uma com {NOTA_MINIMA} "
                     "caracteres ou mais.")
    return {k: {"ok": v["ok"], "nota": v["nota"].strip()} for k, v in r.items()}


def registrar_parecer(build: Path, arquivo: Path, por: str) -> dict[str, Any]:
    """O parecer de quem revisou sobre a última crítica do build: passa sem defeito medido e com todas as respostas
    boas; senão, é para corrigir (a revisão seguinte, com `pfe atualizar`)."""
    feitos = registros(build)
    if not feitos or not por.strip():
        raise Recusa("CRITICA", f"O parecer pede a crítica do build {build.name} e quem revisou.",
                     "Rode `pfe critica <build>` e depois `pfe critica <build> --parecer <arquivo> --por <quem "
                     "revisou>`; quem revisa não é quem compôs.")
    respostas = _respostas(arquivo)
    defeitos = [a["codigo"] for a in feitos[-1]["achados"] if a["gravidade"] == "defeito"]
    ruins = [k for k, v in respostas.items() if not v["ok"]]
    veredito = "corrigir" if defeitos or ruins else "passa"
    return _gravar(build, {**feitos[-1], "parecer": {"por": por.strip(), "respostas": respostas},
                           "veredito": veredito, "a_corrigir": defeitos + ruins})


def conferir_entrega(build: Path) -> None:
    """Recusa o pacote da flora sem a crítica que passa neste build."""
    comp = _composicao(build)
    if comp is None or not e_flora(comp):
        return
    feitos = registros(build)
    if not feitos or feitos[-1]["veredito"] != "passa":
        estado = feitos[-1]["veredito"] if feitos else "sem crítica"
        raise Recusa("CRITICA_PENDENTE", f"O build {build.name} é de flora e a crítica dele está: {estado}.",
                     "Rode `pfe critica <build>`, dê a prancha e as perguntas a outro agente e registre o parecer "
                     "dele (`pfe critica <build> --parecer <arquivo> --por <quem>`); com 'corrigir', mude a "
                     "composição e siga com `pfe atualizar`.")
