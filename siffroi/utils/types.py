from typing import Union, Optional, Any, Tuple
from pathlib import Path

import numpy as np

import sys

# >=3.8-safe type-hints
if sys.version_info >= (3, 8):
    MaskLike = Optional[np.ndarray[Any, np.dtype[np.bool_]]]
    PolygonLike = Optional[np.ndarray[Any, np.dtype[np.int_]]]
else:
    MaskLike = Optional[np.ndarray]
    PolygonLike = Optional[np.ndarray]
ImageShapeLike = Optional[Tuple[int]]
PathLike = Union[str, Path]
FrameData = np.ndarray
ReferenceFrames = np.ndarray
AnatomyReference = np.ndarray