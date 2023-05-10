from typing import Union
from pathlib import Path

import numpy as np

PathLike = Union[str, Path]
MaskLike = Union[None, np.ndarray]
PolygonLike = Union[None, np.ndarray]
ImageShapeLike = Union[None, tuple[int]]
FrameData = np.ndarray
ReferenceFrames = np.ndarray
AnatomyReference = np.ndarray