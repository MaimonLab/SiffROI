from enum import Enum
from typing import Any, TYPE_CHECKING, Optional

import numpy as np
from scipy.ndimage import center_of_mass

from ...roi import ROI, subROI, ViewDirection

if TYPE_CHECKING:
    from ...utils.types import MaskLike, PolygonLike, ImageShapeLike

class FanSegmentationMethod(Enum):
    TRIANGLES = "triangles"
    MIDLINE = "midline"

class Fan(ROI):
    """
    Fan-shaped ROI.

    Orientation refers to how the fan must be
    rotated in order for the posterior fan-shaped
    body to point DOWN (in IMAGE coordinates not x,y).
    """

    SAVE_ATTRS = [
        'view_direction',
        'orientation',
        'mirrored',
    ]

    def __init__(
            self,
            mask: 'MaskLike' = None,
            polygon: 'PolygonLike' = None,
            image_shape: 'ImageShapeLike' = None,
            slice_idx: Optional[int] = None,
            orientation : Optional[float] = 0.0,
            view_direction : 'ViewDirection' = ViewDirection.ANTERIOR,
            mirrored : bool = True,
            **kwargs
        ):
        if not "name" in kwargs:
            kwargs["name"] = "Fan"
        super().__init__(
            mask=mask,
            polygon=polygon,
            image_shape=image_shape,
            slice_idx=slice_idx,
            **kwargs
        )
        self.mirrored = mirrored
        self.orientation = orientation
        self.view_direction = view_direction

    @property
    def columns(self)->list['Column']:
        """
        Returns the columns of the Fan as a list of Column objects.
        """
        return self.subROIs
    
    @property
    def mask(self)->np.ndarray:
        """
        Returns the mask of the Fan as a numpy array.
        """
        if not (self._mask is None):
            return self._mask
        raise NotImplementedError("Fan mask from polygon not yet implemented")
    
    def segment(
        self,
        n_segments : int = 8,
        method : FanSegmentationMethod = FanSegmentationMethod.TRIANGLES,
        viewed_from : ViewDirection = ViewDirection.ANTERIOR
        )->None:
        """
        Divides the fan in to n_segments of 'equal width', 
        defined according to the segmentation method.

        n_segments : int

            Number of columns to divide the Fan into.

        method : str (optional, default is 'triangles')

            Which method to use for segmentation. Available options:

                - triangles :

                    Requires at least two lines in the 'bounding_paths' attribute.
                    Uses the two with the largest angular span that is still less than
                    180 degrees to define the breadth of the fan. Then divides space outward
                    in evenly-spaced angular rays from the point at which the two lines intersect.
                    Looks like:  _\|/_ Columns are defined as the space between each line.

                - midline :

                    Not yet implemented, but constructs a midline through the Fan object, and divides
                    its length into chunks of equal path length. Each pixel in the Fan is assigned to
                    its nearest chunk of the midline.

        viewed_from : str (optional)

            Whether we're viewing from the anterior perspective (roi indexing should rotate counterclockwise)
            or posterior perspective (roi indixing should rotate clockwise) to match standard lab perspective.

            Options:
                
                'anterior'
                'posterior'

        Stores segments as .columns, which are a subROI class
        TODO: implement
        """
        method = FanSegmentationMethod(method)

        if method == FanSegmentationMethod.TRIANGLES:
            self.subROIs = fit_triangles(
                self.mask,
                self.orientation,
                n_segments,
                viewed_from,
                mirrored = self.mirrored
            )
            return
            
        if method == FanSegmentationMethod.MIDLINE:
            raise NotImplementedError("Haven't implemented the midline method of segmenting into columns.")
            

        raise ValueError(f"Keyword argument {method} provided for method is not a valid method name.")

        

    def __str__(self)->str:
        return self.__repr__()

    def __repr__(self)->str:
        """
        A few summary values
        """
        ret_str = "ROI of class Fan\n\n"
        ret_str += f"\tCentered at {self.center()}\n"
        ret_str += f"\tRestricted to slice(s) {self.slice_idx}\n"
        if hasattr(self, 'columns'):
            ret_str += f"\tSegmented into {len(self.columns)} columns\n"
        if hasattr(self,'perspective'):
            ret_str += f"\tViewed from {self.view_direction.value} direction\n"
        if hasattr(self,'midline'):
            ret_str += f"Midline defined as\n"

        return ret_str

class Column(subROI):
        """
        Local class for Fan ROI. Defines a type of subROI in which
        the Fan is divided into triangles of equal angular width
        through the Fan. Generated by the segmentation method 'triangles'.
        """

        SAVE_ATTRS = [
            'phase',
        ]

        def __init__(
                self,
                mask : 'MaskLike' = None,
                polygon : 'PolygonLike' = None,
                image_shape : 'ImageShapeLike' = None,
                phase : Optional[float] = None,
                slice_idx : Optional[int] = None,
                view_direction : ViewDirection = ViewDirection.ANTERIOR,
                **kwargs
            ):
            """
            Initialized using the host Fan ROI, a pair of bounding rays
            projecting from the shared intersect point, nominal bounding
            angles that map from 0 to 360 across all the columns,
            and the intersection point itself

            Accepts all kwargs of the subROI class.
            """

            super().__init__(
                mask=mask,
                polygon=polygon,
                image_shape=image_shape,
                slice_idx=slice_idx, 
                **kwargs
            )

            self.phase = phase,
            self.view_direction = view_direction

        def __repr__(self):
            """
            An triangle-defined column of the fan-shaped body
            """
            ret_str = "ROI of class TriangleColumn of a Fan\n\n"
            ret_str += f"\tCentered at {self.center()}\n"
            ret_str += f"With phase {'(unknown)' if self.phase is None else self.phase}\n"

            return ret_str

def fit_triangles(
    mask : 'MaskLike',
    orientation : float,
    n_segments : int,
    viewed_from : ViewDirection = ViewDirection.ANTERIOR,
    mirrored : bool = True,
    )->list[Column]:
    """
    Takes a mask and the bounding paths of a Fan and divides
    it angularly in n_segments wedges. Returns a list of Column objects.
    """

    def _single_segmentation(
        slice_mask : np.ndarray,
        orientation : float = 0.0,
        n_segments : int = 8,
        view_direction : ViewDirection = ViewDirection.ANTERIOR
    )->list[np.ndarray]:
        """
        Find the centroid of a plane's mask, move along the 'orientation' axis
        until you find the most downward point, and then divide the plane into
        n_segments wedges extending from the centroid to the most downward point.

                _________________
               /.................\ 
              /....__________ ....\ 
             /..../          \ ....\ 
            /____/      x     \_____\

            wedges emanate from x above 

        Returns a list of n_segment masks
        """
        if not np.any(slice_mask):
            return [np.zeros_like(slice_mask) for _ in range(n_segments)]
        centroid = center_of_mass(slice_mask)

        cplx_centroid = -centroid[0]*1j + centroid[1]

        grid_yy, grid_xx = np.meshgrid(*(np.arange(dim) for dim in slice_mask.shape), indexing = 'ij')
        cplx_mask = cplx_centroid - (grid_xx - 1j*grid_yy)
        cplx_mask = cplx_mask

        most_downward_along_orientation = np.unravel_index(
            np.argmax(
                np.imag(cplx_mask*np.exp(-1j*orientation))# rotate along orientation axis
                *slice_mask
            ),
            slice_mask.shape
        )

        # Translate index into point
        most_downward_point = (
            grid_xx[most_downward_along_orientation] - 
            1j*grid_yy[most_downward_along_orientation]
        )

        # Take the oriented-directed x coordinate of the centroid and the
        # orientation-directed y coordinate of the most downward point
        hub_point = (
            np.real(cplx_centroid*np.exp(-1j*orientation)) +
            np.imag(most_downward_point*np.exp(-1j*orientation))*1j
        )*np.exp(1j*orientation)

        new_grid = (grid_xx - 1j*grid_yy - hub_point)*np.exp(1j*orientation)
        angles = -np.angle(new_grid)*slice_mask
        if ViewDirection(view_direction) == ViewDirection.POSTERIOR:
            angles = -angles
        angle_range = angles.min(), angles.max()
        angle_boundaries = np.linspace(*angle_range, n_segments + 1, endpoint = True)

        masks = [
            np.logical_and(
                (angles >= lb) *
                (angles < ub),
                slice_mask
            )
            for lb, ub in zip(angle_boundaries[:-1], angle_boundaries[1:])
        ]
        return masks
    
    masks = np.array([
        _single_segmentation(
            slice_mask,
            orientation = orientation,
            n_segments = n_segments,
            view_direction = viewed_from
        )
        for slice_mask in mask
    ]).swapaxes(0,1) # segment, slice, y, x

    phases = np.linspace(
        0, 2*np.pi, n_segments, endpoint=False
    )
    if mirrored:
        phases = phases[::-1]

    return [
        Column(
            mask = mask,
            polygon = None,
            image_shape = mask.shape,
            phase = phase,
            slice_idx = None,
            view_direction = viewed_from,
        )
        for mask, phase in zip(masks, phases)
    ]
