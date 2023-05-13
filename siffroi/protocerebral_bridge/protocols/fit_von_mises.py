# Code for ROI extraction from the protocerebral bridge after manual input

# Relies on my separate fourcorr module
from typing import Any, TYPE_CHECKING
import numpy as np

import fourcorr

from ..rois.mustache import GlobularMustache
from ...roi_protocol import ROIProtocol
from ...roi import ViewDirection
from ...utils.mixins import (
    UsesReferenceFramesMixin, UsesFrameDataMixin
)
from ...utils.mixins.napari import ExtractionWithCallback

if TYPE_CHECKING:
    from ...utils.types import (
        ReferenceFrames, FrameData
    )
    from fourcorr.napari.correlation import CorrelationWindow

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
            view_direction : 'ViewDirection' = ViewDirection.ANTERIOR,
    )->GlobularMustache:
        """
        Returns a GlobularMustache ROI made up of the individual
        masks extracted by correlating every pixel to the source ROIs
        """
        fca = fourcorr.FourCorrAnalysis(
            frames = frame_data,
            annotation_images = reference_frames,
        )

        fca.done_clicked.connect(lambda x: self.fca_to_pb(x, view_direction))
        return self.events.extracted

    def fca_to_pb(self, event : Any, view_direction : 'ViewDirection'):
        corr_window : CorrelationWindow = event.source
        glomeruli = corr_window.masks
        self.roi = GlobularMustache(
            globular_glomeruli_masks = glomeruli,
            view_direction=view_direction,
        )
        self.events.extracted()