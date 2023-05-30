# ROI PROTOCOLS

This section contains code pertaining to annotation of, segmentation of,
and general analysis of ROIs in image data. All code in this section is
actually independent of any `siffpy` functionality, and so can be used
on any `numpy` or `numpy`-like data, in principle. These methods produce
objects that subclass the `ROI` class. The `ROI` superclass contains methods
that are common to all `ROI` tools (e.g. `mask` to return a `numpy.ndarray`),
while each subclass carries implementation specific details.

`ROI` classes are created using `ROIProtocol` subclasses. The `ROIProtocol`
class is intended to create a shared interface for all types of `ROI`
segmentation procedures so that downstream code can stay agnostic to
the details of every class or method.

## ROIProtocol

This contains the basic interface for segmenting out ROIs of interest.
An `ROIProtocol` implements at least one method `extract(self, *args, **kwargs)->ROI`. It has additional parameters that can often shape how this extraction
is done, and the `inspect` module is used to parse those parameters and
make them accessible via GUI. Each individual `ROIProtocol` subclass is
defined within its respective modules (e.g. `ellipsoid_body`).

## ROI

## ROI Subclasses

### Ellipse

The `Ellipse` `ROI` is initialized with a polygon, corresponding to an approximation of its outline. This single polygon will be fit with
an ellipse, or if the argument `center_polygon` is provided (as is an option in the `ellipsoid_body` module's fitting method `fit_ellipse`),
a separate polygon will be fit to the center and the two together will help define the outer ellipse.

An ellipse can be segmented with the method `ellipse.segment(n_segments)`, creating `n_segment` `Wedge` `ROI` objects, stored as a list
in the attribute name `wedges` of the `Ellipse`.

### Fan

## SubROIs

The `subROI` is implemented for each `ROI` subclass, and corresponds to a special type of `ROI` used to segment larger `ROI`
objects into smaller chunks. The method of segmentation is customized for each `subROI` class and `ROI` subclass, but they
share some common attributes. For one, they themselves are `ROI`s and so they have every method an `ROI` in general does.
TODO finish!