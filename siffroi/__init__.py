from pathlib import Path
from typing import TYPE_CHECKING, Optional
import re

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
        ['generic', 'Generic'],
        generic,
        'Generic ROI',
        RegionEnum.GENERIC
    )
]

def load_rois(path : 'PathLike', pattern : Optional[str] = None)->list['ROI']:
    """
    If `pattern` is None, just loads all ROIs in subdirectories of `path`.
    Otherwise, loads all ROIs in subdirectories of `path` whose name matches
    `pattern`. `pattern` must be a valid regex pattern!

    Parameters
    ----------
    path : PathLike
        Path to directory containing ROIs.

    pattern : Optional[str], optional
        Regex pattern to match against ROI names, by default None. Must
        be a valid regex pattern.
    """
    path = Path(path)
    if pattern is None:
        return [ROI.load(roipath) for roipath in path.rglob('*.h5roi')]
    else:
        pattern_regex = re.compile(pattern)
        return [
            ROI.load(roipath) for roipath in path.rglob('*.h5roi')
            if pattern_regex.search(roipath.name)
        ]

