"""Os quadros de um asset: a pose, a projeção na vista e o render."""

from __future__ import annotations

from ..contracts.base import Direcao
from ..contracts.ir import AssetIR
from ..raster.estilo import EstiloRender
from ..raster.renderer import Quadro, render
from ..rig.fk import Skeleton
from ..rig.pose import rest_pose
from ..views.projetor import project_view


def quadro_de_repouso(asset: AssetIR, est: EstiloRender, direcao: Direcao) -> Quadro:
    scene = project_view(asset, rest_pose(Skeleton(asset.bones)), direcao)
    return render(scene, est, asset.canvas.width, asset.canvas.height)
