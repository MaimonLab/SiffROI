from typing import Union, Optional, Any
from pathlib import Path

import numpy as np

PathLike = Union[str, Path]
MaskLike = Optional[np.ndarray[Any, np.dtype[np.bool_]]]
PolygonLike = Optional[np.ndarray[Any, np.dtype[np.int64]]]
ImageShapeLike = Optional[tuple[int]]
FrameData = np.ndarray
ReferenceFrames = np.ndarray
AnatomyReference = np.ndarray