from typing import Any
import numpy as np
from scipy.stats import circmean

from ...roi import ROI, subROI, ViewDirection

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
    ]

    def __init__(
            self,
            mask : np.ndarray = None,
            polygon : np.ndarray = None,
            image_shape : tuple[int] = None,
            slice_idx : int = None,
            orientation : float = 0.0,
            center_poly : np.ndarray = None,
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
        side of the ellipse and is in radians.
        """
        super().__init__(
            mask = mask,
            polygon = polygon,
            image_shape = image_shape,
            name = 'Ellipse',
            slice_idx = slice_idx,
            **kwargs
        )
        self.orientation = orientation
        self.center_poly = center_poly

    @property
    def wedges(self)->list['subROI']:
        """ Returns the list of wedge ROIs """
        return self.subROIs

    @property
    def mask(self)->np.ndarray:
        """ Returns the mask of the Ellipse """
        if not self._mask is None:
            return self._mask
        

        grid = np.zeros(self._shape, dtype=bool)
        raise NotImplementedError("Mask not yet implemented for Ellipse")

        if self.center_poly is None:
            return grid
        if image is None and hasattr(self,'image'):
            image = self.image

        from matplotlib.path import Path as mplPath
        
        # if isinstance(self.center_poly,hv.element.Polygons):
        #     poly_as_path = mplPath(list(zip(self.center_poly.data[0]['x'],self.center_poly.data[0]['y'])), closed=True)
        poly_as_path = mplPath(self.center_poly.data[0], closed = True) # these are usually stored as arrays
       
        xx, yy = np.meshgrid(*[np.arange(0,dimlen,1) for dimlen in image.T.shape])
        x, y = xx.flatten(), yy.flatten()

        rasterpoints = np.vstack((x,y)).T

        inner_grid = poly_as_path.contains_points(rasterpoints)
        inner_grid = inner_grid.reshape(image.shape)
        grid[inner_grid] = False

        return grid

    def segment(self, n_segments : int = 16, viewed_from : ViewDirection = ViewDirection.ANTERIOR)->None:
        """
        Creates an attribute wedges, a list of WedgeROIs corresponding to segments
        
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

        cx, cy = self.center()
        ell = self.polygon

        if (viewed_from == ViewDirection.ANTERIOR) or (viewed_from == ViewDirection.ANTERIOR.value):
            angles = np.linspace(EB_OFFSET, EB_OFFSET - 2*np.pi, n_segments+1)
        elif (viewed_from == ViewDirection.POSTERIOR) or (viewed_from == ViewDirection.POSTERIOR.value):
            angles = np.linspace(EB_OFFSET , EB_OFFSET + 2*np.pi, n_segments+1)
        else:
            raise ValueError(f"Argument 'viewed_from' is {viewed_from}, must be in {[x.value for x in ViewDirection]}")
        angles += self.orientation 
        self.perspective = viewed_from
        # eek, bad terminology with my orientation variable from the class itself
        offset = ell.orientation

        # Go 360/n_segments degrees around the ellipse
        # And draw a dividing line at the end
        # The WedgeROI will build an ROI out of the sector
        # of the ellipse between its input line boundaries
        # dividing_lines = [
        #     hv.Path(
        #         {
        #             'x':[cx, ell.x + (ell.width/2)*np.cos(offset)*np.cos(angle) - (ell.height/2)*np.sin(offset)*np.sin(angle)] ,
        #             'y':[cy, ell.y + (ell.width/2)*np.sin(offset)*np.cos(angle) + (ell.height/2)*np.cos(offset)*np.sin(angle)]
        #         }
        #     )
        #     for angle in angles
        # ]
        #
        # image = None
        # if hasattr(self,'image'):
        #     image = self.image
        # self.wedges = [
        #     Ellipse.WedgeROI(
        #         boundaries[0],
        #         boundaries[1],
        #         ell,
        #         image=image,
        #         slice_idx = self.slice_idx
        #     )
        #     for boundaries in zip(tuple(pairwise(dividing_lines)),tuple(pairwise(angles)))
        # ]

        #colorwheel = colorcet.colorwheel

        idx = 0
        # for wedge in self.wedges:
        #     wedge.plotting_opts['fill_color'] = colorwheel[idx * int(len(colorwheel)/len(self.wedges))]
        #     wedge.plotting_opts['fill_alpha'] = 0.3
        #     idx += 1

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
        def __init__(self,
                bounding_paths : tuple[Any],
                bounding_angles : tuple[float],
                ellipse : 'Ellipse',
                slice_idx : int = None,
                **kwargs
            ):
            super().__init__(self, **kwargs)

            self.bounding_paths = bounding_paths
            self.bounding_angles = bounding_angles
            self.slice_idx = slice_idx

            sector_range = np.linspace(bounding_angles[0], bounding_angles[1], 60)
            offset = ellipse.orientation

            # Define the wedge polygon
            # self.polygon = hv.Polygons(
            #     {
            #         'x' : bounding_paths[0].data[0]['x'].tolist() +
            #             [
            #                 ellipse.x + (ellipse.width/2)*np.cos(offset)*np.cos(point) - (ellipse.height/2)*np.sin(offset)*np.sin(point)
            #                 for point in sector_range
            #             ] +
            #             list(reversed(bounding_paths[-1].data[0]['x'])),

            #         'y' : bounding_paths[0].data[0]['y'].tolist() +
            #             [
            #                 ellipse.y + (ellipse.width/2)*np.sin(offset)*np.cos(point) + (ellipse.height/2)*np.cos(offset)*np.sin(point)
            #                 for point in sector_range
            #             ] +
            #             list(reversed(bounding_paths[-1].data[0]['y']))
            #     }
            # )
        
        def visualize(self):
            return self.polygon.opts(**self.plotting_opts)

        @property
        def angle(self):
            return circmean(self.bounding_angles)

        def __repr__(self):
            """
            An ellipse's wedge.
            """
            ret_str = "ROI of class Wedge of an Ellipse\n\n"
            ret_str += f"\tCentered at {self.center()}\n"
            ret_str += f"\tOccupies angles in range {self.bounding_angles}\n"
            ret_str += f"Custom plotting options: {self.plotting_opts}\n"

            return ret_str