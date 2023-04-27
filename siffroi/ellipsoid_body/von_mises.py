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

from ..rois import Ellipse
#from siffpy.siffroi.roi_protocols.utils import PolygonSource
from ..protocerebral_bridge.fit_von_mises import FitVonMises

class FitVonMisesEB(FitVonMises):

    name = "Fit von Mises"
    base_roi_text = "View correlation map"
        
    def extract(
            self,
            reference_frames : np.ndarray,
            polygon_source : Any,
    )->Ellipse:
        raise NotImplementedError("Sorry bub!")