"""O oráculo de pixel (I11): o `pixel-engine` exportado por `git archive HEAD` numa pasta temporária, com um ambiente
próprio, roda a mesma entrada que a engine nova. Nada é escrito no `pixel-engine` (I7): o `git archive` só lê, e a
cópia, o ambiente e a saída ficam na pasta temporária.

Uso:
    python scripts/oraculo.py --versao              # exporta (uma vez por commit) e mostra o commit e a versão antiga
    python scripts/oraculo.py tests/fixtures/oraculo/bloco.json ...   # grava o esperado de cada caso de IR
    python scripts/oraculo.py --kit                 # grava o esperado de cada variação de cada peça do kit

Um caso de IR é a IR da engine nova (`ir`), o estilo (`estilo`, relativo ao caso) e as vistas; o esperado
(`<caso>.esperado.json`) guarda, por vista, o tamanho e o sha256 do RGBA que o `pixel-engine` dá na mesma entrada,
convertida para o formato antigo (os campos que a engine nova não tem levam o valor do estilo base antigo). O kit:
cada variação da prancha vira uma composição de um nó, no formato antigo com os nomes antigos dos materiais
(`tests/fixtures/oraculo/materiais.json`), no estilo base antigo; o esperado vai em `kit.esperado.json`.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import subprocess
import sys
import tarfile
import tempfile
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from pixel_forge.application.catalogo import de_uma_peca
from pixel_forge.design.kit.registro import PECAS

REPO = Path(os.environ.get("PFE_ORACULO_REPO", r"D:\gabri\Projetos\Gabriel\pixel-engine"))
CACHE = Path(tempfile.gettempdir()) / "pfe-oraculo"
# só o que instala e roda o motor antigo (o `challenge/` e o resto do treino ficam de fora da cópia)
CAMINHOS = ["src", "presets", "schemas", "pyproject.toml", "README.md", "LICENSE"]
FIXTURES = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "oraculo"
DIRECOES = ("S", "SW", "W", "NW", "N", "NE", "E", "SE")


def commit() -> str:
    return subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"], capture_output=True, text=True,
                          check=True).stdout.strip()


def python_da_copia(destino: Path) -> Path:
    return destino / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def exportar(sha: str) -> Path:
    """A cópia do `pixel-engine` no commit ``sha``, instalada num ambiente próprio (feita uma vez por commit)."""
    destino = CACHE / sha[:12]
    if (destino / ".pronto").exists():
        return destino
    tar = subprocess.run(["git", "-C", str(REPO), "archive", "--format=tar", sha, *CAMINHOS], capture_output=True,
                         check=True).stdout
    destino.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(tar)) as arquivo:
        arquivo.extractall(destino, filter="data")
    subprocess.run(["uv", "venv", "--quiet", "--python", "3.12", str(destino / ".venv")], check=True)
    subprocess.run(["uv", "pip", "install", "--quiet", "--python", str(python_da_copia(destino)), str(destino)],
                   check=True)
    (destino / ".pronto").write_text(sha, encoding="utf-8")
    return destino


def rodar(destino: Path, script: Path, entrada: bytes) -> bytes:
    """Roda ``script`` no Python da cópia, isolado (``-I``), com ``entrada`` no stdin; devolve o stdout."""
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    feito = subprocess.run([str(python_da_copia(destino)), "-I", str(script)], input=entrada, capture_output=True,
                           cwd=destino, env=env)
    if feito.returncode:
        raise RuntimeError(f"o oráculo falhou:\n{feito.stderr.decode('utf-8', 'replace')}")
    return feito.stdout


def estilo_antigo(e: dict[str, Any]) -> dict[str, Any]:
    """O estilo novo no formato antigo: os modos que o estilo base antigo fixava viram os campos dele."""
    sh = e["shading"]
    return {"kind": "style", "schema_version": "2.0.0", "id": e["id"], "revision": e["revision"],
            "palette": e["palette"], "materials": e["materials"], "max_opaque_colors": e["max_opaque_colors"],
            "outline": {"thickness_px": 1, "external": True, "internal": "group_change", "default_index": 1},
            "clusters": {"min_cluster_px": 2, "whitelist_tags": ["detail", "pixel_detail", "eye", "accent", "spark"]},
            "shading": {"space": "camera", **{k: v for k, v in sh.items() if k != "cast_shadow_px"}},
            "quantization": {"rounding": "floor_half_up", "tie_break": "part_id_ascending", "temporal": "stateless"},
            "stylize": {"selective_outline": "light_side", "isolated_cleanup": True, "outline_placement": "inside",
                        "crease_lines": True, "pixel_perfect": True, "cast_shadow_px": sh["cast_shadow_px"],
                        "cast_flat": "plane", "ground_shadow": "projected"}}


def _vista_antiga(direcao: str, v: dict[str, Any]) -> dict[str, Any]:
    regras = [{"id": f"r{i}", "front": r["front"], "back": r["back"], "when": {}}
              for i, r in enumerate(v.get("occlusion_rules", []))]
    return {"azimuth_mdeg": DIRECOES.index(direcao) * 45_000, "elevation_mdeg": 45_000, "depth_permille": 350,
            "part_variants": {}, "visibility": v.get("visibility", {}), "depth_bias": v.get("depth_bias", {}),
            "occlusion_rules": regras, "mirror_policy": "forbidden"}


def asset_antigo(ir: dict[str, Any], estilo: dict[str, Any]) -> dict[str, Any]:
    """A IR nova no formato antigo, com a câmera do 3/4 oblíquo em cada vista."""
    return {"kind": "asset", "schema_version": "2.0.0", "id": ir["id"], "revision": ir["revision"],
            "category": "prop", "canvas": ir["canvas"], "identity_ref": None,
            "style_ref": {"id": estilo["id"], "revision": estilo["revision"], "sha256": "0" * 64},
            "rig": {"template_id": "oraculo", "bones": [{**b, "stretch_limit_ppm": 0, "control": False}
                                                        for b in ir["bones"]]},
            "parts": [{**p, "side": "center"} for p in ir["parts"]],
            "views": {d: _vista_antiga(d, v) for d, v in ir["views"].items()},
            "capabilities": {"entity_role": "prop", "motion_class": "static", "directions": list(ir["views"]),
                             "clip_presets": ["static"], "rig_kind": "prop_root"},
            "design": {"grammar": "oraculo", "grammar_version": 1, "candidate_id": "c1", "root_seed": 0,
                       "params": {}, "selected_by": {"type": "tool", "name": "oraculo"}},
            "seams": [], "extensions": {}}


def _trocar(v: Any, mapa: dict[str, str]) -> Any:
    if isinstance(v, str):
        return mapa.get(v, v)
    return [_trocar(x, mapa) for x in v] if isinstance(v, list) else v


def composicao_antiga(comp: dict[str, Any]) -> dict[str, Any]:
    """A composição nova no formato antigo: os materiais com os nomes antigos e o id que o antigo deixa montar com
    qualquer peça do kit (as que ele tirou pela regra dos dois usos)."""
    mapa = json.loads((FIXTURES / "materiais.json").read_text(encoding="utf-8"))
    nos = [{**n, "args": {k: _trocar(v, mapa) for k, v in n.get("args", {}).items()}} for n in comp["nos"]]
    base = {k: v for k, v in comp.items() if k != "categoria"}
    return {**base, "kind": "composition", "schema_version": "2.0.0", "id": "kit_peca",
            "reference": "docs/references/README.md", "nos": nos,
            "vistas": {d: {"ocultas": v.get("ocultas", [])} for d, v in comp["vistas"].items()}}


def antigo(destino: Path, casos: list[dict[str, Any]], estilo: dict[str, Any] | None) -> dict[str, Any]:
    entrada = {"casos": casos, "style": estilo}
    saida: dict[str, Any] = json.loads(rodar(destino, Path(__file__).with_name("oraculo_antigo.py"),
                                             json.dumps(entrada).encode()))
    return {nome: {v: {"tamanho": q["tamanho"], "rgba_sha256": q["rgba_sha256"]} for v, q in vistas.items()}
            for nome, vistas in saida.items()}


def _salvar(alvo: Path, dado: dict[str, Any]) -> None:
    alvo.write_text(json.dumps(dado, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def gravar(destino: Path, sha: str, caso: Path) -> None:
    dado = json.loads(caso.read_text(encoding="utf-8"))
    estilo = json.loads((caso.parent / dado["estilo"]).read_text(encoding="utf-8"))
    saida = antigo(destino, [{"nome": caso.stem, "asset": asset_antigo(dado["ir"], estilo),
                              "vistas": dado["vistas"]}], estilo_antigo(estilo))[caso.stem]
    _salvar(caso.with_name(f"{caso.stem}.esperado.json"), {"pixel_engine": sha, "vistas": saida})
    print(f"{caso.name}: " + ", ".join(f"{v} {q['rgba_sha256'][:12]}" for v, q in saida.items()))


def estilo_base_antigo() -> dict[str, Any]:
    """O estilo base novo com os nomes antigos dos materiais: o oráculo confere o porte na mesma entrada, e a troca de
    paleta (os nomes por função, os materiais de cena que saíram, os verdes de folhosa) fica na prancha."""
    mapa = json.loads((FIXTURES / "materiais.json").read_text(encoding="utf-8"))
    novo = json.loads((Path(__file__).resolve().parents[1] / "src" / "pixel_forge" / "dados" / "estilo_base.json")
                      .read_text(encoding="utf-8"))
    mats = [{**m, "id": mapa.get(m["id"], m["id"]),
             **({"cast_material": mapa[m["cast_material"]]} if m.get("cast_material") else {})}
            for m in novo["materials"]]
    return estilo_antigo({**novo, "materials": mats})


def gravar_kit(destino: Path, sha: str) -> None:
    casos = [{"nome": f"{pid}/{nome}", "composicao": composicao_antiga(de_uma_peca(pid, args).model_dump(mode="json")),
              "vistas": ["S"]} for pid, p in sorted(PECAS.items()) if p.tipo == "prop" for nome, args in p.variacoes]
    saida = antigo(destino, casos, estilo_base_antigo())
    _salvar(FIXTURES / "kit.esperado.json", {"pixel_engine": sha, "casos": saida})
    print(f"kit: {len(saida)} variações gravadas")


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--versao", action="store_true", help="exporta e mostra o commit e a versão do motor antigo")
    ap.add_argument("--kit", action="store_true", help="grava o esperado das variações do kit")
    ap.add_argument("casos", nargs="*", type=Path, help="os casos de IR para gravar o esperado")
    args = ap.parse_args(argv)
    sha = commit()
    destino = exportar(sha)
    if args.versao:
        sonda = destino / "versao.py"
        sonda.write_text("import importlib.metadata as m\nprint(m.version('pixel-forge-engine'))\n", encoding="utf-8")
        print(f"pixel-engine {sha[:12]} | motor {rodar(destino, sonda, b'').decode().strip()} | {destino}")
    for caso in args.casos:
        gravar(destino, sha, caso)
    if args.kit:
        gravar_kit(destino, sha)
    return 0


if __name__ == "__main__":
    sys.exit(main())
