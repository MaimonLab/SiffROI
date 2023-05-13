from typing import Any, TYPE_CHECKING, Optional
import numpy as np
from scipy.ndimage import center_of_mass

from ...roi import ROI, subROI, ViewDirection

if TYPE_CHECKING:
    from ...utils.types import MaskLike, PolygonLike, ImageShapeLike

EB_OFFSET = (1/2) * np.pi # EPG going to left of each PB (when viewed from posterior) is the first ROI

class Ellipse(ROI):
    """
    Ellipse-shaped ROI

    ........

    Attributes
    ----------

    mask : np.ndarray

        Not needed for initialization, but can be used instead of
        other options.

    polygon : np.ndarrays

        The bounding box of the ellipse, in rectangular
        coordinates (TOP_LEFT, TOP_RIGHT, BOTTOM_RIGHT, BOTTOM_LEFT).

    image_shape : tuple[int]

        Shape of the image in which the polygon is embedded

    slice_idx      : int | None

        Integer reference to the z-slice that the source polygon was drawn on.
        None means any plane.

    orientation    : float = 0.0

        The orientation of the ellipse, in radians. Indicates
        the angle by which the image must be rotated to put the
        ventralmost side of the ellipse at the bottom of the image.

    """

    SAVE_ATTRS = [
        'orientation',
        'center_poly',
        'view_direction',
    ]

    def __init__(
            self,
            mask : 'MaskLike' = None,
            polygon : 'PolygonLike' = None,
            image_shape : 'ImageShapeLike' = None,
            slice_idx : int = None,
            orientation : float = 0.0,
            center_poly : Optional[np.ndarray] = None,
            view_direction : ViewDirection = ViewDirection.ANTERIOR,
            **kwargs
        ):
        """
        Polygon is the bounding box of the ellipse, in rectangular
        coordinates (TOP_LEFT, TOP_RIGHT, BOTTOM_RIGHT, BOTTOM_LEFT).

        orientation kwarg allows the 'bottom' of the ellipse to be
        rotated to a different angle. This is useful for the ellipsoid
        body, where the ventral side is at the bottom of the image in some
        configurations but some image preps have the ventral side in a 
        different direction. Presumes 'orientation' at 0 is the ventral
        side of the ellipse and is in radians. Orientation is how much
        the line from posterodorsal to anteroventral is rotated clockwise
        IN THE IMAGE. So ventral at the bottom = orientation = 3/2 * pi
        """
        if not "name" in kwargs:
            kwargs["name"] = "Ellipse"
        super().__init__(
            mask = mask,
            polygon = polygon,
            image_shape = image_shape,
            slice_idx = slice_idx,
            **kwargs
        )
        self.orientation = orientation
        self.center_poly = center_poly
        self.view_direction = ViewDirection(view_direction)

    @property
    def wedges(self)->list['WedgeROI']:
        """ Returns the list of wedge ROIs """
        return self.subROIs

    @property
    def mask(self)->np.ndarray:
        """ Returns the mask of the Ellipse """
        if not (self._mask is None):
            return self._mask
        
        raise NotImplementedError("Mask from polygon not yet implemented for Ellipse")

    @property
    def center_mask(self)->np.ndarray:
        """
        Returns the mask of the center polygon
        """
        if self.center_poly is None:
            return None
        if isinstance(self.center_poly, np.ndarray) and (self.center_poly.dtype == bool):
            return self.center_poly
        else:
            raise NotImplementedError("Center mask not yet implemented for non-boolean center polygons")


    def segment(self, n_segments : int = 16, viewed_from : ViewDirection = ViewDirection.ANTERIOR)->None:
        """
        Creates an attribute wedges, a list of WedgeROIs corresponding to segments.
        If slice_idx is None, the wedges span all planes. If slice_idx is an integer,
        the wedges span only that plane.
        
        PARAMETERS
        ----------

        n_segments : int
        
            Number of wedges to produce

        viewed_from : str (optional)

            Whether we're viewing from the anterior perspective (roi indexing should rotate counterclockwise)
            or posterior perspective (roi indixing should rotate clockwise) to match standard lab perspective.

            Options:
                
                'anterior'
                'posterior'
        
        """
        if isinstance(self.center_poly, np.ndarray) and (self.center_poly.dtype != bool):
            raise TypeError("Center poly must be a boolean array in current implementation")
        
        if self.slice_idx is None:
            slicewise_segments = [
                segment_ellipse(
                    slice_mask,
                    self.center(plane=slice_num) if self.center_poly is None else center_of_mass(self.center_mask[slice_num]),
                    self.orientation,
                    n_segments = n_segments,
                    view_direction= self.view_direction
                )
                for slice_num, slice_mask in enumerate(self.mask)
            ]
            masks = np.swapaxes(
                np.array(slicewise_segments), # z, mask, y, x
                0,
                1
            )
        else:
            masks = segment_ellipse(
                self.mask,
                self.center() if self.center_poly is None else center_of_mass(self.center_mask),
                self.orientation,
                n_segments = n_segments,
                view_direction= self.view_direction
            )
        self.subROIs = [
            WedgeROI(
                mask = wedge_mask,
                image_shape = self.shape,
                slice_idx = self.slice_idx,
                view_direction = self.view_direction,
                name = f"Wedge {i}",
                phase = angle,
            )
            for i, (wedge_mask, angle) in enumerate(zip(masks, np.linspace(-np.pi, np.pi, n_segments, endpoint=False)))
        ]

    def __str__(self)->str:
        return self.__repr__()

    def __repr__(self)->str:
        """
        A few summary values
        """
        ret_str = "ROI of class Ellipse\n\n"
        ret_str += f"\tCentered at {self.center()}\n"
        ret_str += f"\tRestricted to slice(s) {self.slice_idx}\n"
        if len(self.wedges) > 0:
            ret_str += f"\tSegmented into {len(self.wedges)} wedges\n"
        if hasattr(self,'perspective'):
            ret_str += f"\tViewed from {self.perspective} direction\n"
        ret_str += f"\tOrientation {self.orientation}\n"

        return ret_str
        
class WedgeROI(subROI):
        """
        Local class for ellipsoid body wedges. Very simple

        Takes two lines and an ellipse, with the lines defining
        the edges of the sector the WedgeROI occupies. Then it
        returns a subROI whose polygon is approximately the interior
        of the Ellipse in between the two dividing line segments.

        Unique attributes
        -----------------

        bounding_paths : tuple[hv.element.Path] 

            The edges of the wedge that divide the
            ellipse into segments

        bounding_angles : tuple[float]

            The angular value along the outer contour
            of the ellipse that correspond to the edge
            bounding_paths
        """

        SAVE_ATTRS = [
            'phase',
        ]
        
        def __init__(self,
                mask : 'MaskLike' = None,
                polygon : 'PolygonLike' = None,
                image_shape : 'ImageShapeLike' = None,
                phase : Optional[float] = None,
                slice_idx : Optional[int] = None,
                view_direction : ViewDirection = ViewDirection.ANTERIOR,
                **kwargs
            ):
            super().__init__(
                mask = mask,
                polygon = polygon,
                image_shape = image_shape,
                slice_idx = slice_idx,
                **kwargs
            )
            self.phase = phase
            self.slice_idx = slice_idx
            self.view_direction = ViewDirection(view_direction)

        @property
        def angle(self)->Optional[float]:
            """ Alias for phase """
            return self.phase

        def __repr__(self):
            """
            An ellipse's wedge.
            """
            ret_str = "ROI of class Wedge of an Ellipse\n\n"
            ret_str += f"\tCentered at {self.center()}\n"
            ret_str += f"\tWith phase {'(unknown)' if self.phase is None else self.phase}\n"

            return ret_str
        
def segment_ellipse(
    ellipse_mask : np.ndarray, # presumed 2D
    center_pt : np.ndarray,
    orientation : float,
    n_segments : int = 16,
    view_direction : ViewDirection = ViewDirection.ANTERIOR
)->list[np.ndarray]:
    """
    Draws spokes radiating from center_pt and
    masks ellipse_mask within each spoke. Orientation
    determines the offset from the "downward direction"
    and the order of the returned arrays.

    ellipse_mask : np.ndarray of dim 2
    """

    view_direction = ViewDirection(view_direction)

    angles = np.linspace(-np.pi, np.pi, n_segments+1, endpoint = True)

    # Draw a line from the center to the edge of the ellipse
    # at each angle
    center = center_pt[1] - 1j*center_pt[0] # x + iy in terms of SCREEN coordinates

    grid_xx, grid_yy = np.meshgrid(*(np.arange(dim) for dim in ellipse_mask.shape))
    
    cplx_mask = grid_xx - 1j*grid_yy - center

    cplx_mask *= -1j # Rotate the 0 point downward in image coordinates
    cplx_mask *= np.exp(-1j*orientation) # Rotate the ellipse to the correct orientation
    # invert the angles if the view direction is posterior
    cplx_mask = 1.0/cplx_mask if view_direction == ViewDirection.POSTERIOR else cplx_mask

    return [
        np.logical_and(
            (np.angle(cplx_mask) >= angles[i]) *
            (np.angle(cplx_mask) < angles[i+1]),
            ellipse_mask
        )
        for i in range(len(angles)-1)
    ]