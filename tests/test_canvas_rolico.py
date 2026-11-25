"""O canvas do prop cabe o traço roliço grosso (o tronco deitado): conta o raio de cada ponto no que ele passa da
margem. O controle: contando só a meia espessura do traço fino (o jeito antigo), o quadro sai cortado."""

from __future__ import annotations

import pytest

from pixel_forge.application.build import renderizar
from pixel_forge.contracts.carregar import validar
from pixel_forge.contracts.composicao import Composicao
from pixel_forge.core.recusa import Recusa
from pixel_forge.design import canvas


def _tronco_deitado() -> Composicao:
    return validar({
        "id": "tronco_deitado", "revision": 1, "description": "Fixture sintética: um tronco grosso deitado",
        "reference": "fixture sintética mínima", "tipo": "prop", "categoria": "objeto", "semente": 5,
        "nos": [{"id": "tronco", "peca": "traco", "args": {
            "pontos": [["-1.3m", "-10cm", "18cm"], ["0", "0", "19cm"], ["1.3m", "12cm", "16cm"]],
            "material": "casca", "raio": "18cm"}}],
        "vistas": {"S": {}}, "movimento": ["static"], "tracos": []}, Composicao, "tronco")


def test_o_tronco_grosso_deitado_cabe_no_quadro() -> None:
    r = renderizar(_tronco_deitado())
    assert all(q.clipping_px == 0 for s in r.sequencias for q in s.quadros)


def test_controle_so_a_meia_espessura_corta_o_tronco(monkeypatch: pytest.MonkeyPatch) -> None:
    original = canvas._Caixa.__init__

    def sem_raio(self: canvas._Caixa, folga: int) -> None:
        original(self, folga)
        self.folga = 10_000  # nenhum raio passa da margem: só a meia espessura conta

    monkeypatch.setattr(canvas._Caixa, "__init__", sem_raio)
    with pytest.raises(Recusa) as e:
        renderizar(_tronco_deitado())
    assert e.value.codigo == "QUADRO_CORTADO"
