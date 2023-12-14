from typing import Optional

import numpy as np

from ...roi import ROI, subROI
from ...utils.types import MaskLike, PolygonLike, ImageShapeLike
from ...roi import ViewDirection

class GlobularMustache(ROI):
    """
    A mustache-shaped ROI for individually circuled glomeruli
    """

    SAVE_ATTRS = [
        'view_direction',
    ]

    def __init__(
        self,
        mask : MaskLike = None,
        polygon: PolygonLike = None,
        image_shape : ImageShapeLike = None,
        name: Optional[str] = None,
        slice_idx: Optional[int] = None,
        globular_glomeruli_masks: Optional[list[np.ndarray]] = None,
        phases : Optional[list[Optional[float]]] = None,
        view_direction : ViewDirection = ViewDirection.POSTERIOR,
    ):
        
        if phases is None:
            phases = [None for _ in globular_glomeruli_masks]

        self.subROIs = [
            GlobularMustache.GlomerulusROI(
                mask = glom,
                polygon=None,
                image_shape=image_shape,
                name=name,
                slice_idx=slice_idx,
                pseudophase=phase,
            ) for glom, phase in zip(globular_glomeruli_masks, phases)
        ]

        if mask is None:
            mask = np.array(self.subROIs).any(axis=0)

        super().__init__(
            mask = mask,
            polygon = polygon,
            image_shape = image_shape,
            name = name,
            slice_idx = slice_idx,
        )

        self.view_direction = view_direction
    
    def segment(self) -> None:
        """
        Does nothing : this class is initialized with the glomeruli!
        """
        pass

    @property
    def glomeruli(self):
        return self.subROIs

    class GlomerulusROI(subROI):
        """
        A single glomerulus
        """

        SAVE_ATTRS = [
            'pseudophase',
        ]

        def __init__(
            self,
            mask : MaskLike = None,
            polygon: PolygonLike = None,
            image_shape : ImageShapeLike = None,
            name: Optional[str] = None,
            slice_idx: Optional[int] = None,
            pseudophase : Optional[float] = None,
        ):
            super().__init__(
                mask = mask,
                polygon=polygon,
                image_shape=image_shape,
                name=name,
                slice_idx=slice_idx,
            )
            self.pseudophase = pseudophase

