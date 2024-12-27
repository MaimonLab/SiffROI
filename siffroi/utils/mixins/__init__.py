""" ROI PROTOCOL MIXINS """
from typing import Any


class UsesFrameDataMixin():

    extraction_args : dict[str, Any]

    @property
    def frame_data_arg_num(self)->int:
        """ Returns the position of the frame_data argument in the extraction function """
        return list(self.extraction_args.keys()).index("frame_data")

class UsesReferenceFramesMixin():
    """
    UsesReferenceFrames means it uses the reference frames layer,
    possibly in addition to the raw data layer
    """
    extraction_args : dict[str, Any]
 
    @property
    def reference_frames_arg_num(self)->int:
        """ Returns the position of the reference_frames argument in the extraction function """
        return list(self.extraction_args.keys()).index("reference_frames")

class UsesAnatomyReferenceMixin():

    extraction_args : dict[str, Any]
    ANATOMY_REFERENCE_SHAPE_TYPE : str = "any"

    @property
    def anatomy_reference_arg_num(self)->int:
        """ Returns the position of the anatomy_reference argument in the extraction function """
        return list(self.extraction_args.keys()).index("anatomy_reference")
    
class ExpectsShapesMixin():
    """
    ExpectsShapes means it expects data like the data of a `Shapes` layer.

    SHAPE_TYPE class attribute can specify the type used. Should be a
    `napari` style string
    """
    extraction_args : dict[str, Any]
    SHAPE_TYPE : str = "any"
    @property
    def shape_arg_num(self)->int:
        """ Returns the position of the shapes argument in the extraction function """
        return list(self.extraction_args.keys()).index("shapes")

class AllowsExclusionsMixin():
    """
    `AllowsExclusions` means that the mask can be intersected with the negation of
    an "exclusion mask" before extraction to ensure those pixels are ignored.
    """ 

    extraction_args : dict[str, Any]
    ANATOMY_REFERENCE_SHAPE_TYPE : str = "any"
    LAYER_NAME : str = "exclusion_layer"

    @property
    def exclusion_mask_arg_num(self)->int:
        """ Returns the position of the exclusion_mask argument in the extraction function """
        return list(self.extraction_args.keys()).index("exclusion_mask")