"""
Implements an identical protocol to the
Protocerebral Bridge one but returns an Ellipse
"""

# Code for ROI extraction from the protocerebral bridge after manual input

# Feels like I use too much interfacing with the CorrelationWindow class,
# which seems like it should do as much as possible without interacting with
# this stuff...
from typing import Any

import numpy as np
from fourcorr import FourCorrAnalysis

from ...utils.mixins import UsesReferenceFramesMixin
from ...roi_protocol import ROIProtocol
from ..rois.ellipse import Ellipse

class FitVonMisesEB(UsesReferenceFramesMixin, ROIProtocol):

    name = "Fit von Mises"
    base_roi_text = "View correlation map"
        
    def extract(
        self,
        reference_frames : np.ndarray,
    )->Ellipse:
        fca = FourCorrAnalysis(
            frames = reference_frames,
            annotation_images=reference_frames
        )

        raise NotImplementedError("Sorry bub!")