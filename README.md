# SiffRoi

Tools for `ROI` annotation, segmentation, etc.

This is meant to be `napari` agnostic without being _too_
`napari` agnostic. So it will only expect things like `np.ndarray`
types, but it will expect those arrays to be formatted _like_
`napari` outputs, e.g. `Shapes` or `Image` layers. This should make
it easy 1) to interact with data in `napari` and then pipe annotated
versions of those data into an `ROIProtocol` just by collecting attributes
and `Layer` information and 2) to make `napari` widgets to directly
interact with your data in `napari` (say, with a plugin like
`siff-napari`).

Makes use of two primary classes: `ROIProtocol` and `ROI`.

## ROI Protocols

The `ROIProtocol` superclass contains the metadata needed to figure
out what input are needed to produce an `ROI` from data and some
annotations. The general structure is that an `ROIProtocol` implements
a function `extract(self, *args, **kwargs)->'ROI'`, where often
the `ROI` class is a subclass itself. The arguments of 
`extract`, as well as the `Mixins` that the `ROIProtocol` subclasses,
can tell other tools (e.g. `siff-napari`) which types of data
the `ROIProtocol` expects without the `ROIProtocol` needing to
know the exact framework being passed in. This allows nice
automated formatting of segmentation code, for example by
providing a particular type of tweakable parameter if an `ROIProtocol`
also subclasses `UsesFrameDataMixin` or `UsesReferenceFramesMixin`,
which can be reflected by the property `uses_frame_data` or 
`uses_reference_frames`.

Please note that for `siff-napari` to work properly, the
return annotations on `extract` must be the ACTUAL class and
not a string hint. Otherwise the object's `__annotations__['return']`
will read a `str`

## ROI

The `ROI` base class has a few attributes, not all of which
are necessary to instantiate any specific `ROI`:

- `mask`, an `np.ndarray` of `bool` values that indicate
where the ROI is
- `polygon`, an `np.ndarray` of vertices that bound the
ROI
- `image_shape`, a `tuple` of `int`s that describe the
shape of the image the `ROI` is embedded in.

If `mask` is provided, `polygon` and `image_shape` are
unnecessary, and depending on the type of `ROI` can sometimes
even be generated from `mask` alone (`image_shape`, for example,
almost always can). If `mask` is not provided but `polygon` and
`image_shape` are, it is expected that a given `ROI` class is capable
of producing a useful mask with the property `mask`. A generic
`ROI` could, for example, take the convex hull of `polygon` and
fill it within an array of size `image_shape`, but this would
only be useful for the most basic `ROI` (others, like `Ellipse`
or `Fan` should produce more useful masks).

`ROI` objects can be saved with the `save(self, path : PathLike)`
method, where `PathLike = Union[str, pathlib.Path]`. This will
store the `ROI` in a `.h5roi` file, which is just an `h5` file
saved with the various datatypes.

`ROI`s can be initialized with other parameters, such as a name,
an integer with the slice index from which it was drawn, or a
pre-made list of `subROI`s.

### subROIs

Often an `ROI` will be split further (e.g. wedges of an `Ellipse`).
Most `ROI` classes will implement a `segment` function that takes
the primary `ROI` and populates its `subROIs` attribute with a list
of the `ROI` subclass `subROI`.

## Regions

The module implements many different region-specific segmentation
algorithms. To provide a common access point, a list of
objects of class `Region` is provided in `siffroi`. A `Region`
consists of:
- `alias_list` : a list of aliases (`str` that all can be used to
refer to the region)
- `module` : the `module` within `siffroi` that contains
`Region`-specific `ROIProtocol` objects and methods
- `default_fcn_str` : a  default protocol referred to by a `str`
version of its name (for readability -- it can be accessed with
`Region.default_protocol` which produces the actual `ROIProtocol`
instead of the string) 
- `region_enum`, a `RegionEnum` attribute

These are defined in `siffroi.utils.regions`