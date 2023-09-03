from typing import Any, Optional, TYPE_CHECKING
import numpy as np

from .extra_rois import ExtraRois
from ...roi_protocol import ROIProtocol
from ...roi import ViewDirection
from ..rois.ellipse import Ellipse
from ...utils import nth_largest_shape_in_list
from ...utils.mixins import (
    UsesAnatomyReferenceMixin, UsesReferenceFramesMixin, ExpectsShapesMixin
)

if TYPE_CHECKING:
    from ...utils.types import (
        MaskLike, PolygonLike, ImageShapeLike, AnatomyReference, ReferenceFrames
    )

class UseEllipse(
        ExpectsShapesMixin,
        UsesAnatomyReferenceMixin,
        UsesReferenceFramesMixin,
        ROIProtocol
    ):

    name = "Use ellipse"
    base_roi_text = "Extract ellipse"
    
    SHAPE_TYPE = "ellipse"
    ANATOMY_REFERENCE_SHAPE_TYPE = "line"

    extraction_arg_list = [
        "extra_rois", "view_direction"
    ]

    def extract(
        self,
        reference_frames : 'ReferenceFrames',
        anatomy_reference : 'AnatomyReference',
        shapes : list[np.ndarray],
        roi_name : str = "Ellipse",
        slice_idx : Optional[int] = None,
        extra_rois : 'ExtraRois' = ExtraRois.CENTER,
        view_direction : 'ViewDirection' = ViewDirection.ANTERIOR,
    )->Ellipse: 
        image_shape = reference_frames.shape
        return use_ellipse(
            shapes,
            anatomy_reference,
            image_shape,
            roi_name = roi_name,
            view_direction=view_direction,
            slice_idx=slice_idx,
            extra_rois=extra_rois,
        )

def use_ellipse(
    ellipses : list[np.ndarray],
    anatomy_reference : 'AnatomyReference',
    image_shape : tuple[int],
    roi_name = "Ellipse",
    view_direction : 'ViewDirection' = ViewDirection.ANTERIOR,
    slice_idx : Optional[int] = -1,
    extra_rois : 'ExtraRois' = ExtraRois.CENTER,
    **kwargs) -> 'Ellipse':
    """
    Simply takes the largest ellipse type shape in a viewer
    and uses it as the bound! Ellipses go TOP LEFT, TOP RIGHT,
    BOTTOM RIGHT, BOTTOM LEFT.

    Keyword args
    ------------

    slice_idx : int

        Takes the largest polygon only from within
        the slice index labeled 'slice_idx', rather
        than the largest polygon across all slices.

    extra_rois : str | ExtraRois

        A string that explains what any ROIs other than
        the largest might be useful for. Current options:

            - Center : Finds the extra ROI "most likely" to 
            be the center of the ellipse, and uses it to reshape the
            fit polygon. Currently, that ROI is just the smallest 
            other one... Not even constrained to be fully contained.

    Additional kwargs are passed to the Ellipse's opts function

    """
    main_ellip = nth_largest_shape_in_list(
        ellipses,
        n = 1,
        slice_idx=slice_idx,
        image_shape=image_shape
    )
    FROM_MASK = False
    slice_idx = None if (slice_idx is None) or (slice_idx < 0) else slice_idx
    if len(ellipses) == 0:
        raise ValueError("No suitable ellipses provided")
    
    if all([ellipse.dtype == bool for ellipse in ellipses]):
        # If we have a boolean mask, we can just use that as the
        # and bypass the hullabaloo below
        FROM_MASK = True

    center = None

    if (ExtraRois(extra_rois) == ExtraRois.CENTER):
        
        if len(ellipses) < 2:
            raise ValueError("Did not provide a second ROI for the extra ROI field")

        center = nth_largest_shape_in_list(
            ellipses,
            n = 2,
            slice_idx=slice_idx,
            image_shape=image_shape
        ) 
        if FROM_MASK:
            main_ellip = np.logical_and(
                main_ellip,
                np.logical_not(center)
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

    return Ellipse(
        mask = main_ellip if FROM_MASK else None,
        polygon = None if FROM_MASK else main_ellip,
        image_shape = image_shape,
        slice_idx = slice_idx,
        name = roi_name,
        orientation = orientation,
        center_poly = center,
        view_direction = view_direction,
    )