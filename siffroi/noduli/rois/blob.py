from typing import Any, Optional, TYPE_CHECKING

from ...roi import ROI, subROI, ViewDirection

if TYPE_CHECKING:
    from ...utils.types import MaskLike, PolygonLike, ImageShapeLike


class Blobs(ROI):
    """
    Blob-shaped ROIs used for the noduli or bulb.
    Blobs are boring, and their main feature
    is their pair of polygons. They do not have a midline!
    """

    SAVE_ATTRS = [
        "view_direction",
        "orientation",
    ]

    def __init__(
            self,
            mask: 'MaskLike' = None,
            polygon: 'PolygonLike' = None,
            image_shape: 'ImageShapeLike' = None,
            slice_idx: Optional[int] = None,
            orientation : Optional[float] = 0.0,
            view_direction : 'ViewDirection' = ViewDirection.POSTERIOR,
            hemispheres : Optional[list['Hemisphere']] = None,
            **kwargs
        ):

        view_direction = ViewDirection(view_direction)

        if not "name" in kwargs:
            kwargs["name"] = "Fan"
        super().__init__(
            mask=mask,
            polygon=polygon,
            image_shape=image_shape,
            slice_idx=slice_idx,
            **kwargs
        )
        self.orientation = orientation
        self.view_direction = view_direction
        self.hemispheres = hemispheres

        # Left hemisphere first
        if self.hemispheres is not None:
            centers = [h.center() for h in self.hemispheres]

            
            # Left depends on whether you're viewing from anterior
            # or posterior
            if view_direction == ViewDirection.ANTERIOR:
                def sort_func(x : Blobs.Hemisphere)->float:
                    raise ValueError()

            else :
                def sort_func(x : Blobs.Hemisphere)->float:
                    raise ValueError()

            self.hemispheres.sort(
                key = sort_func
            )

    def segment(
            self,
            viewed_from : ViewDirection = ViewDirection.POSTERIOR,
            **kwargs
        ) -> None:
        """ n_segments is not a true keyword param, always produces two """
        if not hasattr(self, 'hemispheres'):
            raise ValueError("Haven't implemented segmentation from a single source mask")
        # self.hemispheres = [
        #     Blobs.Hemisphere(pgon) for pgon in self.polygon.split()
        # ]

        # self.hemispheres.sort(
        #     key=lambda x: x.polygon.centroid[0]
        # )

    def find_midline(self):
        """ No midline! """
        raise ValueError("Blob type ROIs do not have a midline!")

    def __getattr__(self, attr)->Any:
        """
        Custom subROI call to return hemispheres
        as the subROI
        """
        if attr == '_subROIs':
            if hasattr(self,'hemispheres'):
                return self.hemispheres
            else:
                raise AttributeError(f"No hemispheres attribute assigned for Blobs")
        else:
            return object.__getattribute__(self, attr)

class Hemisphere(subROI):
    """ A vanilla ROI, except it's classed as a subROI. Has just a polygon. """
    def __init__(self,
            mask: 'MaskLike' = None,
            polygon: 'PolygonLike' = None,
            image_shape: 'ImageShapeLike' = None,
            slice_idx: Optional[int] = None,
            phase : Optional[float] = None,
            **kwargs
        ):
        self.phase = phase
        super().__init__(
            mask = mask,
            polygon = polygon,
            image_shape = image_shape,
            slice_idx = slice_idx,
            name = "Hemisphere",
        )