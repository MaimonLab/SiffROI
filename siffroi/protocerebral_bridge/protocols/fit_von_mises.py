# Code for ROI extraction from the protocerebral bridge after manual input

# Relies on my separate fourcorr module
from typing import Any, TYPE_CHECKING

import fourcorr

from ..rois.mustache import GlobularMustache
from ...roi_protocol import ROIProtocol
from ...roi import ViewDirection
from ...utils.mixins import (
    UsesReferenceFramesMixin, UsesFrameDataMixin
)
from ...utils.mixins.napari import ExtractionWithCallback

from ...utils.types import (
    ReferenceFrames, FrameData
)

if TYPE_CHECKING:
    from fourcorr import FourCorrAnalysis

class FitVonMises(
    UsesFrameDataMixin,
    UsesReferenceFramesMixin,
    ExtractionWithCallback,
    ROIProtocol,
    ):

    name = "Fit von Mises"
    base_roi_text = "View correlation map"

    def extract(
            self,
            frame_data : 'FrameData',
            reference_frames : 'ReferenceFrames',
            view_direction : ViewDirection = ViewDirection.POSTERIOR,
            roi_name : str = "Protocerebral bridge",
    )->GlobularMustache:
        """
        Returns a GlobularMustache ROI made up of the individual
        masks extracted by correlating every pixel to the source ROIs
        """
        view_direction = ViewDirection(view_direction)
        fca = fourcorr.FourCorrAnalysis(
            frames = frame_data,
            annotation_images = reference_frames,
        )

        fca.done_clicked.connect(
            lambda x: self.fca_to_pb(
                    x, view_direction, roi_name=roi_name
                )
            )

    def fca_to_pb(
            self,
            event : Any,
            view_direction : ViewDirection,
            roi_name : str = "Protocerebral bridge",
        ):
        corr_window : 'FourCorrAnalysis' = event.source
        glomeruli = corr_window.masks

        #TODO: figure out the right phases!
        self.roi = GlobularMustache(
            globular_glomeruli_masks = glomeruli,
            view_direction=view_direction,
            name = roi_name,
        )
        self.events.extracted()