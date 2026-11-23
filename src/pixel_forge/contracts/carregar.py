"""A leitura de um documento JSON num modelo, com a recusa que diz onde e como corrigir."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ValidationError

from ..core.recusa import Recusa


def validar[M: BaseModel](dado: Any, modelo: type[M], nome: str) -> M:
    try:
        return modelo.model_validate(dado)
    except ValidationError as exc:
        erro = exc.errors()[0]
        onde = "/" + "/".join(str(p) for p in erro["loc"])
        recebido = repr(erro.get("input"))
        recebido = recebido if len(recebido) <= 80 else recebido[:77] + "..."
        raise Recusa("DOC_INVALIDO", f"{nome}: {erro['msg']} em {onde} (recebido: {recebido}).",
                     f"Em {onde}: {erro['msg']}. Os campos e os limites estão na seção 4 da skill.", onde) from None


def ler[M: BaseModel](caminho: Path, modelo: type[M]) -> M:
    try:
        dado = json.loads(caminho.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise Recusa("ARQUIVO_AUSENTE", f"O arquivo {caminho} não existe.", "Confira o caminho.") from None
    except json.JSONDecodeError as exc:
        raise Recusa("JSON_INVALIDO", f"{caminho.name}: {exc.msg} na linha {exc.lineno}.",
                     "Corrija a sintaxe do JSON.") from None
    return validar(dado, modelo, caminho.name)
