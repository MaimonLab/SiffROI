""" ROI PROTOCOL MIXINS """



class UsesFrameDataMixin():

    @property
    def frame_data_arg_num(self)->int:
        """ Returns the position of the frame_data argument in the extraction function """
        return list(self.extraction_args.keys()).index("frame_data")

class UsesReferenceFramesMixin():
    """
    UsesReferenceFrames means it uses the reference frames layer,
    possibly in addition to the raw data layer
    """
    
    @property
    def reference_frames_arg_num(self)->int:
        """ Returns the position of the reference_frames argument in the extraction function """
        return list(self.extraction_args.keys()).index("reference_frames")

class UsesAnatomyReferenceMixin():

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

    SHAPE_TYPE : str = "any"
    @property
    def shape_arg_num(self)->int:
        """ Returns the position of the shapes argument in the extraction function """
        return list(self.extraction_args.keys()).index("shapes")
    