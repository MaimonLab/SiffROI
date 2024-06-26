from abc import ABC, abstractmethod
from inspect import Parameter, signature
from typing import TYPE_CHECKING

from .utils.types import ReferenceFrames, AnatomyReference, FrameData
from .utils.mixins import (
    UsesFrameDataMixin, UsesReferenceFramesMixin, UsesAnatomyReferenceMixin, 
)

if TYPE_CHECKING:
    from .roi import ROI

class ROIProtocol(ABC):
    """
    Superclass of all ROI protocols.
    
    Provides a single common interface so that
    the ROIVisualizer can call any ROI protocol
    without knowing much about it. Eliminates the
    clumsy `inspect` module usage that was
    previously required to get the arguments
    of a protocol and limited how things
    could be formatted. But these get more complicated
    and you basically have to do the type-hinting yourself...
    """

    name : str = "ROI Protocol superclass"
    base_roi_text : str = "Extract base ROI"
    extraction_arg_list: list[str] = []

    @abstractmethod
    def extract(self, *args, **kwargs)->'ROI':
        """
        The main method of the ROI protocol.
        """
        raise NotImplementedError()

    @property
    def extraction_args(self):
        """ For GUI widgets """
        return {
            key : kw
            for key, kw in signature(self.extract).parameters.items()
            if kw.kind is Parameter.POSITIONAL_OR_KEYWORD
        }
    
    @property
    def segmentation_args(self):
        """ For GUI widgets """
        return {
            key : kw
            for key, kw in signature(self.return_class.segment).parameters.items()
            if kw.kind is Parameter.POSITIONAL_OR_KEYWORD
        }

    @property
    def return_class(self)->type['ROI']:
        return self.extract.__annotations__["return"]
    
    @property
    def uses_frame_data(self)->bool:
        """ Reflects whether the protocol uses the raw frame data"""
        return (
            "frame_data" in self.extraction_args.keys()
            and self.extraction_args["frame_data"].annotation is FrameData
        ) or isinstance(self, UsesFrameDataMixin)

    @property
    def uses_reference_frames(self)->bool:
        """ Relies on extraction function having a parameter named `reference_frames`"""
        return (
            "reference_frames" in self.extraction_args.keys()
            and self.extraction_args["reference_frames"].annotation is ReferenceFrames
        ) or isinstance(self, UsesReferenceFramesMixin)
    
    @property
    def uses_anatomy_reference(self)->bool:
        """ Relies on extraction function having a parameter named `anatomy_reference`"""
        return (
            "anatomy_reference" in self.extraction_args.keys()
            and self.extraction_args["anatomy_reference"].annotation is AnatomyReference
        ) or isinstance(self, UsesAnatomyReferenceMixin)