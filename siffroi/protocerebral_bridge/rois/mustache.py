from typing import Optional, List

import numpy as np

from ...roi import ROI, subROI
from ...utils.types import MaskLike, PolygonLike, ImageShapeLike
from ...roi import ViewDirection

class GlobularMustache(ROI):
    """
    A mustache-shaped ROI for individually circuled glomeruli.

    Parameters
    ----------
    mask : MaskLike, optional
        A mask of the mustache, must use one of mask or polygon

    polygon : PolygonLike, optional
        A polygon outlining the mustache, must use one of mask or polygon

    image_shape : ImageShapeLike, optional
        The shape of the image the ROI is in

    name : str, optional
        A name for the ROI

    slice_idx : int, optional
        The slice index the ROI is in. -1 for 3d ROIs

    globular_glomeruli_masks : list[np.ndarray], optional
        A list of masks of the individual glomeruli

    phases : list[Optional[float]], optional
        A list of pseudophases of the individual glomeruli

    view_direction : ViewDirection, optional
        The view direction of the ROI

    mirrored : bool, optional
        Whether the image is mirrored from reality
    """

    SAVE_ATTRS = [
        'view_direction',
        'mirrored'
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
        mirrored : bool = True,
        **kwargs,
    ):

        # Dumb of me to use an alias like this in this specific method
        # when I already have a subROIs initialization in the superclass..
        if (globular_glomeruli_masks is None) and 'subROIs' in kwargs:
            globular_glomeruli_masks = kwargs.pop('subROIs')

        if phases is None:
            phases = [None for _ in globular_glomeruli_masks]
        if mirrored:
            phases = phases[::-1]
        self.mirrored = mirrored

        if all(isinstance(x, subROI) for x in globular_glomeruli_masks):
            self.subROIs = globular_glomeruli_masks
        else:
            self.subROIs = [
                GlomerulusROI(
                    mask = glom,
                    polygon=None,
                    image_shape=image_shape,
                    name=name,
                    slice_idx=slice_idx,
                    pseudophase=phase,
                ) for glom, phase in zip( globular_glomeruli_masks , phases)
            ]

        if mask is None:
            mask = np.array(globular_glomeruli_masks).any(axis=0)

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
    
    @property
    def phases(self)->List[float]:
        return [
            x.pseudophase
            for x in self.subROIs
        ]

    def sort_glomeruli_by_phase(self):
        """
        Sorts glomeruli by pseudophase
        """
        self.subROIs.sort(
            key = lambda x: x.pseudophase
        )

    def sort_glomeruli_by_center(self, axis : int = -1, increasing : bool = True):
        """
        Sorts glomeruli by center
        """
        self.subROIs.sort(
            key = lambda x: x.center()[axis],
            reverse = not increasing,
        )

    def sort_glomeruli_by_snake(self):
        """
        Uses the shortest-path algorithm to sort glomeruli into a snake.
        
        May start at either end of the mustache, so use some analysis to
        identify which end should go first (e.g. might need to use the direction
        you're imaging from or whether the ROI is mirrored...)
        """
        try:
           from python_tsp.exact import solve_tsp_dynamic_programming 
        except ImportError:
            print("Please install python-tsp to use this function"
            " (pip install python-tsp)"
            )
            return
        
        # Get the centers of the glomeruli
        centers = [glom.center() for glom in self.subROIs]

        # Get the distance matrix
        dists = np.linalg.norm(
            np.array(centers)[:, None] - np.array(centers)[None],
            axis = -1
        )

        # Add a "depot" that is distance 0 to all other points
        dists = np.vstack([dists, np.zeros(len(dists))])
        dists = np.hstack([dists, np.zeros((len(dists), 1))])

        # solve the traveling salesman problem!

        path, _ = solve_tsp_dynamic_programming(dists)

        # Reorder to start at the depot

        start_idx = np.argmax(path)
        path = path[start_idx:] + path[:start_idx]

        # now remove the deport

        path = [p for p in path if p != len(self.subROIs)]

        # Reorder the glomeruli
        self.subROIs = [self.subROIs[p] for p in path]


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
        **kwargs
    ):
        super().__init__(
            mask = mask,
            polygon=polygon,
            image_shape=image_shape,
            name=name,
            slice_idx=slice_idx,
        )
        self.pseudophase = pseudophase

    @property
    def phase(self):
        """
        Alias for pseudophase -- not sure it should be called true phase
        if it's estimated from fourcorr
        """
        return self.pseudophase

