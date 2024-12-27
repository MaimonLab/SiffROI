# Code for ROI extraction from the noduli after manual input

from typing import Optional

import numpy as np

from ..rois.blob import Blobs
from ...roi import ViewDirection
from ...roi_protocol import ROIProtocol
from ...utils import n_largest_shapes_in_list
from ...utils.mixins import (
    UsesFrameDataMixin, ExpectsShapesMixin, UsesAnatomyReferenceMixin,
    UsesReferenceFramesMixin, AllowsExclusionsMixin
)
from ...utils.types import (
    FrameData, ReferenceFrames, AnatomyReference,
)

class DrawROI(
    ExpectsShapesMixin,
    UsesAnatomyReferenceMixin,
    UsesReferenceFramesMixin,
    AllowsExclusionsMixin,
    ROIProtocol
    ):

    name = "Draw ROI"
    base_roi_text = "Draw ROIs manually"

    extraction_arg_list = [
        "view_direction"
    ]

    def extract(
        self,
        reference_frames : 'ReferenceFrames',
        anatomy_reference : 'AnatomyReference',
        shapes : list[np.ndarray],
        roi_name : str = "Noduli",
        slice_idx : Optional[int] = None,
        view_direction : ViewDirection = ViewDirection.POSTERIOR,
        exclusion_layer : np.ndarray = None,
    )-> Blobs:
        
        image_shape = reference_frames.shape
        slice_idx = None if (slice_idx is None) or (slice_idx < 0) else int(slice_idx)

        blobs = n_largest_shapes_in_list(
            shapes,
            n = 2,
            image_shape= image_shape,
            slice_idx=slice_idx,
        )

        FROM_MASK = all(polygon.dtype == bool for polygon in shapes)
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

        if exclusion_layer is not None:
            blobs = np.logical_and(
                blobs,
                np.logical_not(exclusion_layer)
            )

        return Blobs(
            mask = blobs if FROM_MASK else None,
            polygons = None if FROM_MASK else blobs,
            image_shape = image_shape,
            slice_idx = slice_idx,
            name = roi_name,
            orientation = orientation,
            view_direction = view_direction,
        )



class ICA(
    UsesFrameDataMixin,
    ROIProtocol,
    ):
    
    name = 'ICA (independent component analysis)'
    base_roi_text = 'Extract noduli with ICA'

    extraction_arg_list = [
        "view_direction",
    ]

    def extract(
        self,
        frame_data : 'FrameData',
        roi_name : str = "Noduli",
        slice_idx : Optional[int] = None,
        view_direction : ViewDirection = ViewDirection.POSTERIOR
    ):
        return ica(
            frame_data = frame_data,
            roi_name=roi_name,
            slice_idx=slice_idx,
            view_direction=view_direction,
        )


def ica(
    frame_data,
    roi_name,
    slice_idx,
    view_direction,    
):
    """ Implemented ICA on frame_data here"""
    raise NotImplementedError()


def hemispheres(
        reference_frames : list,
        polygon_source : dict,
        *args,
        slice_idx : int = None,
        **kwargs
    ) -> Blobs:
    """
    Just takes the ROIs in the left and right hemispheres. Returns them as a Blobs ROI which is basically
    the same as two polygons. For now, it just takes the two largest ones! TODO: At least check left vs. right,
    and order them consistently
    # """

    raise NotImplementedError()

    # return Blobs(polygons_combined, slice_idx)

def dummy_method(*args, **kwargs):
    print("I'm just a placeholder!")