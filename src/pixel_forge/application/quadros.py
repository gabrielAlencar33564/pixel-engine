"""Os quadros de um asset: a pose (o repouso ou o instante de um clipe), a projeção na vista e o render."""

from __future__ import annotations

from ..contracts.base import Direcao
from ..contracts.ir import AssetIR
from ..raster.estilo import EstiloRender
from ..raster.renderer import Quadro, render
from ..rig.fk import Skeleton
from ..rig.pose import Pose, rest_pose
from ..views.projetor import project_view


def quadro_da_pose(asset: AssetIR, est: EstiloRender, pose: Pose, direcao: Direcao) -> Quadro:
    return render(project_view(asset, pose, direcao), est, asset.canvas.width, asset.canvas.height)


def quadro_de_repouso(asset: AssetIR, est: EstiloRender, direcao: Direcao) -> Quadro:
    return quadro_da_pose(asset, est, rest_pose(Skeleton(asset.bones)), direcao)
