from pathlib import Path
from typing import TYPE_CHECKING

from .roi_protocol import ROIProtocol
from .roi import ROI
from .utils.regions import RegionEnum, Region
from . import (
    ellipsoid_body, fan_shaped_body, protocerebral_bridge,
    generic
)#, noduli, generic

from ._version import __version__, version, version_tuple, __version_tuple__

if TYPE_CHECKING:
    from .utils.types import PathLike

REGIONS = [
    Region(
        ['eb','ellipsoid body','ellipsoid', 'Ellipsoid body'],
        ellipsoid_body,
        'Use ellipse',
        RegionEnum.ELLIPSOID_BODY,
    ),
    
    Region(
        ['fb','fsb','fan-shaped body','fan shaped body','fan', 'Fan-shaped body'],
        fan_shaped_body,
        'Outline fan',
        RegionEnum.FAN_SHAPED_BODY
    ),
    
    Region(
        ['pb','pcb','protocerebral bridge','bridge', 'Protocerebral bridge'],
        protocerebral_bridge,
        'Fit von Mises',
        RegionEnum.PROTOCEREBRAL_BRIDGE
    ),
#     Region(
#         ['no','noduli','nodulus','nod', 'Noduli'],
#         noduli,
#         'dummy_method',
#         RegionEnum.NODULI
#     ),
    Region(
        ['generic'],
        generic,
        'Generic ROI',
        RegionEnum.GENERIC
    )
]

def load_rois(path : 'PathLike')->list['ROI']:
    path = Path(path)
    return [ROI.load(roipath) for roipath in path.rglob('*.h5roi')]

