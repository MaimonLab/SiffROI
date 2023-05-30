# Code for ROI extraction from the fan-shaped body after manual input
from typing import Any, Optional
import numpy as np

from ...roi import ViewDirection
from ..rois.fan import Fan
from ...roi_protocol import ROIProtocol
from ...utils import nth_largest_shape_in_list
from ...utils.mixins import (
    UsesReferenceFramesMixin, UsesAnatomyReferenceMixin, ExpectsShapesMixin
)
from ...utils.types import (
    MaskLike, PolygonLike, ImageShapeLike, AnatomyReference, ReferenceFrames
)


class OutlineFan(
    ExpectsShapesMixin,
    UsesAnatomyReferenceMixin,
    UsesReferenceFramesMixin,
    ROIProtocol
    ):

    name = "Outline fan"
    base_roi_text = "Extract fan"

    SHAPE_TYPE = "polygon"
    ANATOMY_REFERENCE_SHAPE_TYPE = "line"

    extraction_arg_list = [
        "view_direction"
    ]

    def extract(
        self,
        reference_frames : ReferenceFrames,
        anatomy_reference : AnatomyReference,
        shapes : list[np.ndarray],
        slice_idx : Optional[int] = None,
        view_direction : ViewDirection = ViewDirection.ANTERIOR,
    )-> Fan:
        image_shape = reference_frames.shape
        return outline_fan(
            shapes,
            anatomy_reference,
            image_shape,
            view_direction=view_direction,
            slice_idx=slice_idx,
        )

    def segment(self):
        raise NotImplementedError()

def outline_fan(
        polygons : list[np.ndarray],
        anatomy_reference : AnatomyReference,
        image_shape : tuple[int],
        view_direction : ViewDirection = ViewDirection.ANTERIOR,
        slice_idx : Optional[int] = -1,
        **kwargs
    )-> Fan:
    """
    Takes the largest ROI and assumes it's the outline of the fan-shaped body.

    """
    FROM_MASK = False
    slice_idx = None if (slice_idx is None) or (slice_idx < 0) else slice_idx
    if len(polygons) == 0:
        raise ValueError("No suitable polygons provided")
    
    if all([polygon.dtype == bool for polygon in polygons]):
        # If we have a boolean mask, we can just use that as the
        # and bypass the hullabaloo below
        FROM_MASK = True

    main_fan = nth_largest_shape_in_list(
        polygons,
        n = 1,
        slice_idx = slice_idx,
        image_shape = image_shape,
    )

    orientation = 0.0

    if not (anatomy_reference is None) and (len(anatomy_reference) > 0):
        if isinstance(anatomy_reference, (tuple,list)):
            anatomy_reference = anatomy_reference[0]
        # Goes postero-dorsal to antero-ventral
        start_pt = anatomy_reference[0][-2:] # y, x
        end_pt = anatomy_reference[1][-2:] # y, x
        # dx + i*dy in SCREEN coordinates
        start_to_end = (end_pt[-1] - start_pt[-1]) - 1j*(end_pt[0] - start_pt[0])
        orientation += np.angle(1j*start_to_end)
        # I always find geometry with complex numbers much easier than using tangents etc.

    return Fan(
        mask = main_fan if FROM_MASK else None,
        polygon = None if FROM_MASK else main_fan,
        image_shape = image_shape,
        slice_idx = slice_idx,
        orientation = orientation,
        view_direction = view_direction,
    )