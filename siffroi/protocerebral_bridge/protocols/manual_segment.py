# Code for ROI extraction from the protocerebral bridge after manual input

# Relies on my separate fourcorr module
from typing import Any, TYPE_CHECKING

import numpy as np

from ..rois.mustache import GlobularMustache
from ...roi_protocol import ROIProtocol
from ...roi import ViewDirection
from ...utils.mixins import (
    UsesReferenceFramesMixin, ExpectsShapesMixin
)

from ...utils.types import ReferenceFrames

class ManualSegmentation(
    UsesReferenceFramesMixin,
    ROIProtocol,
    ):

    name = "Manual segmentation"
    base_roi_text = "Use segments to create ROI"

    def extract(
        self,
        reference_frames : 'ReferenceFrames',
        shapes : list[np.ndarray],
        view_direction : ViewDirection = ViewDirection.POSTERIOR,
        roi_name : str = "Protocerebral bridge",
    )->GlobularMustache:
        """
        Returns a GlobularMustache ROI made up of the individual
        masks extracted by correlating every pixel to the source ROIs
        """
        view_direction = ViewDirection(view_direction)
        return use_individual_compartments(
            shapes,
            reference_frames,
            view_direction,
            roi_name=roi_name
        )


def use_individual_compartments(
    polygons : list[np.ndarray[Any,np.dtype[np.bool_]]],

)->GlobularMustache:
    pass