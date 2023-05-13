from typing import Any, Optional, TYPE_CHECKING
import numpy as np

from .extra_rois import ExtraRois
from ...roi_protocol import ROIProtocol
from ...roi import ViewDirection
from ..rois.ellipse import Ellipse
from ...utils import polygon_area
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
        slice_idx : int = None,
        extra_rois : 'ExtraRois' = ExtraRois.CENTER,
        view_direction : 'ViewDirection' = ViewDirection.ANTERIOR,
    )->Ellipse: 
        image_shape = reference_frames.shape
        return use_ellipse(
            shapes,
            anatomy_reference,
            image_shape,
            view_direction=view_direction,
            slice_idx=slice_idx,
            extra_rois=extra_rois,
        )

def use_ellipse(
    ellipses : list[np.ndarray],
    anatomy_reference : 'AnatomyReference',
    image_shape : tuple[int],
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
    FROM_MASK = False
    slice_idx = None if (slice_idx is None) or (slice_idx < 0) else slice_idx
    if len(ellipses) == 0:
        raise ValueError("No suitable ellipses provided")
    
    if all([ellipse.dtype == bool for ellipse in ellipses]):
        # If we have a boolean mask, we can just use that as the
        # and bypass the hullabaloo below
        FROM_MASK = True

    if slice_idx is None:
        # Get the biggest for all planes
        if FROM_MASK:
            ellipses_by_slice = [
                [ellipse for ellipse in ellipses if np.any(ellipse[slice_idx])]
                for slice_idx in range(image_shape[0])
            ]
            slicewise_idx = [
                np.argsort([np.sum(ellipse) for ellipse in slicewise_ellipses])
                if len(slicewise_ellipses) > 0
                else None
                for slicewise_ellipses in ellipses_by_slice
            ]

            slicewise_biggest_ellipse = [
                slicewise_ellipses[sorted_slicewise[-1]]
                if sorted_slicewise is not None
                else np.zeros(image_shape, dtype=bool)
                for slicewise_ellipses, sorted_slicewise in zip(ellipses_by_slice, slicewise_idx)
            ]

            main_ellip = np.logical_or.reduce(slicewise_biggest_ellipse)
            
        else:
            raise NotImplementedError("Use ellipse only supports masks for now")

    else:
        size_sorted_idx = np.argsort(
            [
                np.sum(ellipse)
                for ellipse in ellipses
                if np.round(ellipse[0][0]) == slice_idx
            ]
        ) if FROM_MASK else np.argsort(
            [
                polygon_area(ellipse)
                for ellipse in ellipses
                if np.round(ellipse[0][0]) == slice_idx
            ]
        )

        main_ellip = ellipses[size_sorted_idx[-1]]

    center = None

    if (ExtraRois(extra_rois) == ExtraRois.CENTER):
        
        if len(ellipses) < 2:
            raise ValueError("Did not provide a second ROI for the extra ROI field")
        
        if slice_idx is None:
            if FROM_MASK:
                slicewise_next_biggest_ellipse = [
                    slicewise_ellipses[sorted_slicewise[-2]]
                    if (
                        (sorted_slicewise is not None)
                        and (len(sorted_slicewise) > 1)
                        and np.logical_and( # intersects with main_ellip
                            slicewise_ellipses[sorted_slicewise[-2]],
                            main_ellip
                        ).any()
                    )
                    else np.zeros(image_shape, dtype=bool)
                    for slicewise_ellipses, sorted_slicewise in zip(ellipses_by_slice, slicewise_idx)
                ]

                center = np.logical_or.reduce(slicewise_next_biggest_ellipse)
                main_ellip = np.logical_and(
                    main_ellip,
                    np.logical_not(center)
                )
        else:
            center = ellipses[size_sorted_idx[-2]]
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
        orientation = orientation,
        center_poly = center,
        view_direction = view_direction,
    )