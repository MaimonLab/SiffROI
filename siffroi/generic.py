# Code for ROI extraction from a generic polygon

from typing import TYPE_CHECKING, Optional

import numpy as np

from .roi_protocol import ROIProtocol
from .utils.mixins import UsesReferenceFramesMixin, ExpectsShapesMixin
from .utils import nth_largest_shape_in_list
from .roi import ROI

if TYPE_CHECKING:
    from .utils.types import ReferenceFrames

class GenericRoi(
    UsesReferenceFramesMixin,
    ExpectsShapesMixin,
    ROIProtocol
    ):
    name = "Generic ROI"
    base_roi_text = "Extract ROI"
    
    SHAPE_TYPE = 'polygon'

    def extract(
        self,
        reference_frames : 'ReferenceFrames',
        shapes : list[np.ndarray],
        roi_name : str = 'ROI',
        slice_idx : Optional[int] = None,
    )->ROI:
        """ Returns a single ROI from a polygon or set of polygons drawn by the user """
        
        FROM_MASK = False

        slice_idx = None if (slice_idx is None) or (slice_idx < 0) else slice_idx
        
        if len(shapes) == 0:
            raise ValueError("No suitable polygons provided")
        
        if all([polygon.dtype == bool for polygon in shapes]):
            FROM_MASK = True

        main_roi = nth_largest_shape_in_list(
            shapes,
            n = 1,
            slice_idx = slice_idx,
            image_shape = reference_frames.shape,
        )

        return ROI(
            mask = main_roi if FROM_MASK else None,
            polygon = None if FROM_MASK else main_roi,
            image_shape = reference_frames.shape,
            slice_idx = slice_idx,
            name = roi_name,
        )

