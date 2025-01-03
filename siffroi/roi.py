from enum import Enum
from pathlib import Path
import importlib
from logging import warning
from typing import TYPE_CHECKING, Optional, Callable, Union

from h5py import File as h5File
from h5py import Empty, Group
import numpy as np
from scipy.ndimage import center_of_mass

from .utils.exceptions import NoROIError
from .utils import masks_to_rgba

if TYPE_CHECKING:
    from .utils.types import PathLike, MaskLike, PolygonLike, ImageShapeLike
    from matplotlib.colors import Colormap

def safe_load_attr(f : Union[h5File, Group], attr : str):
    """ Returns empty if None """
    return None if isinstance(att:= f.attrs.get(attr, None), Empty) else att

def safe_load_ds(f : Union[h5File, Group], attr : str):
    """ Returns empty if None """
    return None if isinstance(att:= f[attr][()], Empty) else att

# Between these sets of enums,
# can uniquely define the orientation
# of the ROI in the brain

class ViewDirection(Enum):
    ANTERIOR = "anterior"
    POSTERIOR = "posterior"
    UNDEFINED = "undefined"

class Orientation(Enum):
    LEFT = "left"
    RIGHT = "right"
    UP = "up"
    DOWN = "down"
    UNDEFINED = "undefined"

class ROI():
    """
    Class for an ROI. Contains information about bounding box, brain region to which
    this ROI belongs, method produced to extract this ROI, and probably information about
    how to use it for computations. May be extended by future use cases.
    """

    SAVE_ATTRS : list[str] = []
    FILE_EXTENSION : str = "h5roi"

    def __init__(self,
            mask        : 'MaskLike'                = None,
            polygon     : 'PolygonLike'             = None,
            image_shape : 'ImageShapeLike'          = None,
            name        : Optional[str]             = None,
            slice_idx   : Optional[int]             = None,
            subROIs     : list['subROI']            = [],
            info_string : Optional[str]             = None,
        ):
        """
        Can be defined either with a mask or a polygon with a source image. If a mask
        is provided, it is _always_ preferred when generating a mask, even if there is a polygon.

        Arguments
        ---------
        mask : np.ndarray

            A mask of the ROI, True inside and False outside

        polygon : np.ndarray

            A polygon representing the vertices of the ROI (if that is an appropriate descriptor)

        source_image : np.ndarray

            An image that provides the bounds of the field of view for the polygon
        """
        self._mask = mask
        self._polygon = polygon
        self._shape = image_shape

        if all([x is None for x in [mask, polygon, image_shape]]):
            raise NoROIError("ROI must be defined with either a mask or a polygon and image")
        
        if name is not None:
            self._name = name
        
        self.slice_idx = slice_idx
        if len(subROIs) > 0:
            self.subROIs = subROIs

        if info_string is not None:
            self.info_string = info_string

        if not hasattr(self, 'subROIs'):
            self.subROIs : list[subROI] = []

    def center(self, plane : Optional[int] = None)->np.ndarray:
        """
        If plane is None, returns the center of mass of the mask
        across all planes. If plane is specified, returns only
        the center of mass of the mask in that plane.
        
        If slice_idx is an int, then plane is ignored.
        """
        mask = self.mask
        if self.slice_idx is not None:
            plane = None
        if plane is None:
            return center_of_mass(mask)
        else:
            return center_of_mass(mask[plane])
    
    def fuse(self, other : 'ROI')->np.ndarray:
        """ Fuses mask in place, but also returns it """
        curr_mask = self.mask
        other_mask = other.mask
        self._mask = np.logical_or(curr_mask, other_mask)
        return self._mask

    @classmethod
    def from_rois(cls, rois : list['ROI'], **kwargs)->'ROI':
        """
        Creates a new ROI from a list of ROIs.
        The new ROI is a union of all the ROIs in the list.
        But the only attribute passed is `mask` so you need to
        populate the rest on your own, or they can be passed
        as kwargs to this function.
        """
        if len(rois) == 0:
            raise NoROIError("No ROIs provided to fuse")
        if len(rois) == 1:
            return rois[0]

        new_roi = rois[0]
        for roi in rois[1:]:
            new_roi.fuse(roi)
        return cls(mask = new_roi.mask, **kwargs)

    def segment(self)->None:
        """ Default ROIs are not segmentable """
        raise NoROIError("This ROI has no segment method")

    @property
    def mask(self)->np.ndarray:
        """
        Returns a mask of the polygon, True inside and False outside.
        Needs an image to define the bounds, if one hasn't been provided to the ROI before
        """
        if self._mask is not None:
            return self._mask.astype(bool)

        raise NotImplementedError("Mask from polygon not yet implemented")
        return np.zeros(self._shape, dtype=bool)

    @property
    def shape(self)->tuple[int]:
        """ Returns the shape of the ROI mask """
        if self._mask is not None:
            return self._mask.shape
        
        return self._shape
    
    @property
    def polygon(self)->np.ndarray:
        """ Returns the polygon of the ROI """
        if self._polygon is not None:
            return self._polygon

        raise NotImplementedError("Generating a polygon from mask not yet implemented") 

    @property
    def subroi_masks(self) -> np.ndarray:
        """
        Returns an arrayof the numpy masks of
        all subROIs of this ROI.
        """
        if len(self.subROIs) == 0:
            raise NoROIError("No subROIs assigned to this ROI")
        return np.array([subroi.mask for subroi in self.subROIs])

    @property
    def labeled_subrois(self) -> np.ndarray:
        """
        Returns a single array consisting of the overlaid subROI
        masks, with an identifying number for each of them from
        1 - n for all the subROIs. 0 is background.
        """
        
        return np.array(
            [
                (i+1)*subroi
                for i, subroi in enumerate(self.subroi_masks)
            ]
        ).sum(axis=0)

    @property
    def rgba_subrois(self) -> np.ndarray:
        """
        Labeled_subrois as an RGBA image with the background
        as transparent using the heatmap 'turbo'
        """
        return masks_to_rgba(self.labeled_subrois)
    
    def rgba_subrois_cmap(self, cmap : 'Colormap') -> np.ndarray:
        """
        Labeled_subrois as an RGBA image with the background
        as transparent using the specified colormap
        """
        return masks_to_rgba(self.labeled_subrois, cmap = cmap)


    def save(self, save_path : 'PathLike')->None:
        """
        Saves the ROIs as .h5roi files. These files are just a pickled
        version of the actual ROI object. ROI name is mangled with 
        unique attributes about the ROI so that no two will overlap
        by using the same name.

        Arguments
        ---------

        save_path : PathLike

            The parent directory to save the file to.

        """
        save_path = Path(save_path)
        save_path = save_path / f"{self.__class__.__name__}_{self.hashname}.{self.__class__.FILE_EXTENSION}"
        save_path.parent.mkdir(parents = True, exist_ok=True)

        def safe_save_attr(f : h5File, attr : str, typestr : str):
            """ Saves as empty if None """
            if getattr(self, attr) is None:
                f.attrs[attr] = Empty(typestr)
            else:
                f.attrs[attr] = getattr(self, attr)

        def safe_save_ds(f : h5File, attr : str, data : np.ndarray, dtype = None):
            """ Saves as an empty dataset if None """
            if data is None:
                f.create_dataset(attr, dtype=dtype)
            else:
                f.create_dataset(attr, data = data, dtype=dtype)

        with h5File(save_path, 'w') as f:
            safe_save_attr(f, 'name', 's')
            safe_save_attr(f, 'slice_idx', 'i')

            f.attrs['class'] = self.__class__.__name__
            f.attrs['module'] = self.__class__.__module__

            if hasattr(self, 'info_string'):
                safe_save_attr(f, 'info_string', 's')

            for attr in self.__class__.SAVE_ATTRS:
                if isinstance(getattr(self,attr), np.ndarray):
                    safe_save_ds(f, attr, getattr(self, attr), getattr(self, attr).dtype)
                else:
                    this_attr = getattr(self, attr)
                    if this_attr is None:
                        attr_out = Empty("s")
                    if isinstance(this_attr,Enum):
                        attr_out = this_attr.value
                    else:
                        attr_out = this_attr 
                    f.attrs[attr] = attr_out

            safe_save_ds(f, 'mask', self.mask, bool)
            safe_save_ds(f, 'shape', self.shape, int)
            safe_save_ds(f, 'polygon', self._polygon, np.float32)

            if hasattr(self, 'subROIs') and len(self.subROIs) > 0:
                subrois_group = f.create_group('subROIs', track_order=True)

                for i, subroi in enumerate(self.subROIs):
                    subroi.save_to_group(subrois_group)

    @classmethod
    def load(
            cls,
            load_path : 'PathLike',
            filter_condition : Optional[Callable[['ROI'], bool]] = None
        )->'ROI':
        """
        Subclasses may want to overload this to import additional attributes.

        If `filter_condition` is provided, it is a function that takes a ROI
        and returns True if it should be loaded and False if it should not.
        Allows 
        
        Currently only loads the mask, image, polygon, name, and slice_idx.
        """
        load_path = Path(load_path)
        if filter_condition is None:
            filter_condition = lambda x: True

        with h5File(load_path.with_suffix(f'.{cls.FILE_EXTENSION}'), 'r') as f:
            # Try to import the class from the module it claims
            # it came from. If that fails, import as the generic
            # ROI class.
            try:
                mod = importlib.import_module(f.attrs['module'])
                cls = getattr(mod, f.attrs['class'])
            except ModuleNotFoundError:
                warning(f"Module {f.attrs['module']} not found. Attempting to import as a generic siffroi.ROI")
                cls = ROI

            mask = safe_load_ds(f, 'mask')
            polygon = safe_load_ds(f, 'polygon')
            image_shape = safe_load_ds(f, 'shape')
            name = safe_load_attr(f, 'name')
            slice_idx = safe_load_attr(f, 'slice_idx')
            info_string = f.attrs.get('info_string', None)

            subrois : list['subROI'] = []
            if 'subROIs' in f and len(f['subROIs']) > 0:
                for subroi_group in f['subROIs'].values():
                    try:
                        sr_mod = importlib.import_module(subroi_group.attrs['module'])
                        sr_cls : type['subROI'] = getattr(sr_mod, subroi_group.attrs['class'])
                    except ModuleNotFoundError:
                        warning(f"Module {subroi_group.attrs['module']} not found. Attempting to import as a generic siffroi.subROI")
                        sr_cls = subROI

                    subrois.append(
                        sr_cls.load_from_group(
                            subroi_group,
                        )
                    )

            roi = cls(
                mask = mask,
                polygon = polygon,
                image_shape = image_shape,
                name = name,
                slice_idx = slice_idx,
                subROIs = subrois,
                info_string = info_string,
            )

            for attr in cls.SAVE_ATTRS:
                if attr in f.attrs.keys():
                    if isinstance(f.attrs[attr], Empty):
                        setattr(roi, attr, None)
                    else:
                        setattr(roi, attr, f.attrs[attr])
                if attr in f.keys():
                    setattr(roi, attr, f[attr][()])

            if not(filter_condition(roi)):
                raise NoROIError("ROI did not pass filter condition, was not loaded")
        return roi
        
    def __hash__(self)->float:
        if hasattr(self, 'image'):
            return hash((self.center(), self.__class__.__name__, self.mask.tobytes()))
        else:
            return hash((self.center(), self.__class__.name))

    @property
    def name(self)->str:
        if hasattr(self,'_name'):
            return str(self._name)
        else:
            return ""

    @property
    def hashname(self)->str:
        if hasattr(self,'_name'):
            return str(self._name) + str(self.__hash__())
        else:
            return str(self.__hash__())

    def __str__(self)->str:
        return self.__repr__()

    def __repr__(self)->str:
        """
        Pretty summary of an ROI... if I write it.
        """
        return f"ROI of class {self.__class__.__name__} with name {self.name}"

    def __getitem__(self, key):
        """
        This is for when ROIs are treated
        like lists even if they aren't one.
        This is to make all code able to handle
        either the case where it assumes there's
        only one ROI referenced by a SiffPlotter
        or the case where it assumes
        there are several.
        """
        if key == 0:
            return self
        else:
            raise TypeError("'ROI' object is not subscriptable (except with 0 to return itself)")

    def __iter__(self) :
        """ List-like behavior on a single ROI """
        return iter([self])

    def __len__(self):
        return 1
    
    def __iadd__(self, other : 'ROI'):
        """
        Combines another ROI's mask into this one's.

        Is this the most intuitive behavior? Should there be
        some condition checks?

        """
        if not isinstance(other, ROI):
            raise TypeError(f"Can only add two ROIs, not {type(other)}")
        self.fuse(other)
    
    def segment(self) -> None:
        """ Abstract method, to be implemented by individual ROIs """
        raise NoROIError("This ROI has no segment method")

class subROI(ROI):
    """
    A subclass of the ROI designed solely to indicate
    to analysis functions that this type of ROI is a segment
    or cluster of a larger ROI, e.g. for HeatMap type
    plotting outputs.

    So far, no custom functionality other than it being
    a subclass identifiable with isinstance.
    """

    def save_to_group(self, subROI_group : Group)->None:
        """ SubROIs save to the same file as their parent ROI, and so demand the h5file group """
        this_subroi = subROI_group.create_group(
            self.hashname,
            track_order=True,
        )

        this_subroi.attrs['name'] = self.name if self.name is not None else Empty("s")
        this_subroi.attrs['slice_idx'] = self.slice_idx if self.slice_idx is not None else Empty("i")
        this_subroi.attrs['class'] = self.__class__.__name__
        this_subroi.attrs['module'] = self.__class__.__module__

        for attr in self.__class__.SAVE_ATTRS:
            if isinstance(getattr(self,attr), np.ndarray):
                this_subroi.create_dataset(
                    attr,
                    data = getattr(self, attr),
                    dtype = getattr(self, attr).dtype,
                )
            else:
                this_subroi.attrs[attr] = getattr(self, attr)

        this_subroi.create_dataset(
            'mask',
            data = self.mask,
            dtype = bool,
        )

        this_subroi.create_dataset(
            'shape',
            data = self.shape,
            dtype = np.int32,
        )

        this_subroi.create_dataset(
            'polygon',
            data = self._polygon,
            dtype = np.float32,
        )

    @classmethod
    def load_from_group(cls, subroi_group : Group)->'subROI':
        """
        Subclasses may want to overload this to import additional attributes.
        SubROIs load from the same file as their parent ROI, and so demand the h5file group.
        
        Currently only loads the mask, image, polygon, name, and slice_idx.
        """

        mask = safe_load_ds(subroi_group, 'mask')
        polygon = safe_load_ds(subroi_group, 'polygon')
        image_shape = safe_load_ds(subroi_group, 'shape')
        name = safe_load_attr(subroi_group, 'name')
        slice_idx = safe_load_attr(subroi_group, 'slice_idx')

        subroi = cls(
            mask = mask,
            polygon = polygon,
            image_shape = image_shape,
            name = name,
            slice_idx = slice_idx,
        )
        
        for attr in cls.SAVE_ATTRS:
            if attr in subroi_group.attrs.keys():
                if isinstance(subroi_group.attrs[attr], Empty):
                    setattr(subroi, attr, None)
                else:
                    setattr(subroi, attr, subroi_group.attrs[attr])
            if attr in subroi_group.keys():
                setattr(subroi, attr, subroi_group[attr][()])
        return subroi