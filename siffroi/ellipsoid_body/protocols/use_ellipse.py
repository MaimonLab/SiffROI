from typing import Any
import numpy as np
import logging

#import holoviews as hv

from .extra_rois import ExtraRois
from ...roi_protocol import ROIProtocol
from ..rois.ellipse import Ellipse
from ...utils import polygon_area
from ...utils.types import ReferenceFrames, AnatomyReference
from ...utils.mixins import (
    UsesAnatomyReferenceMixin, UsesReferenceFramesMixin, ExpectsShapesMixin
)

class UseEllipse(ExpectsShapesMixin, UsesAnatomyReferenceMixin, UsesReferenceFramesMixin, ROIProtocol):

    name = "Use ellipse"
    base_roi_text = "Extract ellipse"
    SHAPE_TYPE = "ellipse"

    def extract(
            self,
            reference_frames : ReferenceFrames,
            anatomy_reference : AnatomyReference,
            ellipses : list[np.ndarray] = [],
            slice_idx : int = None,
            extra_rois : ExtraRois = ExtraRois.CENTER,
    )->Ellipse:
        image_shape = reference_frames.shape
        return use_ellipse(
            ellipses,
            anatomy_reference,
            image_shape,
            slice_idx=slice_idx,
            extra_rois=extra_rois,
        )

    def segment(self):
        raise NotImplementedError()

def use_ellipse(
    ellipses : list[np.ndarray],
    anatomy_reference : AnatomyReference,
    image_shape : tuple[int],
    *args,
    slice_idx : int = None,
    extra_rois : ExtraRois = ExtraRois.CENTER,
    **kwargs) -> Ellipse:
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

    size_sorted_idx = np.argsort([polygon_area(ellipse) for ellipse in ellipses])
    ellip = ellipses[size_sorted_idx[-1]]

    center_x, center_y = ellip.x, ellip.y
    center_poly = None

    if (ExtraRois(extra_rois) == ExtraRois.CENTER):
        
        if len(ellipses) < 2:
            raise ValueError("Did not provide a second ROI for the extra ROI field")
        
        center = ellipses[size_sorted_idx[-2]] 

    orientation = 0.0

    if any(anatomy_reference):
        pass

    return Ellipse(
        mask = None,
        polygon = ellip,
        image_shape = image_shape,
        slice_idx = slice_idx,
        orientation = orientation,
        center_poly = center_poly,
    )