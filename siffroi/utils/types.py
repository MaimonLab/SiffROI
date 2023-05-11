from typing import Union, Optional
from pathlib import Path

import numpy as np

PathLike = Union[str, Path]
MaskLike = Optional[np.ndarray]
PolygonLike = Optional[np.ndarray]
ImageShapeLike = Optional[tuple[int]]
FrameData = np.ndarray
ReferenceFrames = np.ndarray
AnatomyReference = np.ndarray