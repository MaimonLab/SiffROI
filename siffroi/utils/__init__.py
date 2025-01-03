"""
Convenience functions for rois. Should only depend on geometry, so will not
likely require any local imports other than pairwise. A lot of this is a little gratuitous, but
I went with clarity of code over performance by a long shot.

These geometries are all (x,y) not (y,x) the way images are.

SCT Dec 29 2021
"""
from typing import Iterable, Optional, TYPE_CHECKING

from matplotlib.path import Path as mplPath
from matplotlib.pyplot import get_cmap
import numpy as np

if TYPE_CHECKING:
    from matplotlib.colors import Colormap

def polygon_area(vertices : np.ndarray) -> float:
    """
    Computes area of a 2d polygon in n dimensions. Presumes
    the only dimension that matters is the last two.
    """
    x = vertices[..., -1]
    y = vertices[..., -2]
    return 0.5*np.abs(np.dot(x,np.roll(y,1))-np.dot(y,np.roll(x,1)))

def masks_to_rgba(labeled_image_mask : np.ndarray, cmap_str : str = 'hsv')->np.ndarray:
    """
    Converts a labeled mask to an RGBA image with hsv cmap.
    """

    cmap = get_cmap(cmap_str)

    rgba = cmap(
        (labeled_image_mask.astype(float)/labeled_image_mask.max()) ,
        alpha = labeled_image_mask > 0,
    )
    return rgba

def masks_to_cmap(labeled_image_mask : np.ndarray, cmap : 'Colormap')->np.ndarray:
    """
    Converts a labeled mask to an RGBA image with hsv cmap.
    """

    rgba = cmap(
        (labeled_image_mask.astype(float)/labeled_image_mask.max()) ,
        alpha = labeled_image_mask > 0,
    )
    return rgba

def nth_largest_shape_in_list(
        shapes : list[np.ndarray],
        n : int = 1,
        slice_idx : Optional[int] = None,
        image_shape : Optional[tuple[int]] = None,
    )->np.ndarray:
    """
    Selects the nth largest shape in the provided list. Accepts either a list of
    masks (arrays of type bool) or a list of vertices (arrays of points of type float or int)
    """

    FROM_MASK = False
    slice_idx = None if (slice_idx is None) or (slice_idx < 0) else slice_idx
    if len(shapes) == 0:
        raise ValueError("No suitable shapes provided")
    if (n > len(shapes)) or (n < 1):
        raise ValueError(
            "n must be between 1 and the number of shapes provided." + 
            f"Requested {n}-largest of {len(shapes)} shapes"
        )
    
    if all([shape.dtype == bool for shape in shapes]):
        # If we have a boolean mask, we can just use that as the
        # and bypass the hullabaloo below
        FROM_MASK = True

    if slice_idx is None:
        # Get the biggest for all planes
        if FROM_MASK:
            shapes_by_slice = [
                [shape for shape in shapes if np.any(shape[slice_idx])]
                for slice_idx in range(image_shape[0])
            ]

            slicewise_idx = [
                np.argsort([np.sum(shape) for shape in slicewise_shapes])
                if len(slicewise_shapes) > 0
                else None
                for slicewise_shapes in shapes_by_slice
            ]

            slicewise_biggest_shape = [
                slicewise_shapes[sorted_slicewise[-n]]
                if sorted_slicewise is not None
                else np.zeros(image_shape, dtype=bool)
                for slicewise_shapes, sorted_slicewise in zip(shapes_by_slice, slicewise_idx)
            ]

            main_shape = np.logical_or.reduce(slicewise_biggest_shape)
            
        else:
            raise NotImplementedError("ROI functionality only supports masks for now")

    else:
        size_sorted_idx = np.argsort(
            [
                np.sum(shape)
                for shape in shapes
                if np.round(shape[0][0]) == slice_idx
            ]
        ) if FROM_MASK else np.argsort(
            [
                polygon_area(shape)
                for shape in shapes
                if np.round(shape[0][0]) == slice_idx
            ]
        )

        main_shape = shapes[size_sorted_idx[-n]]
    return main_shape

def n_largest_shapes_in_list(
        shapes : list[np.ndarray],
        n : int = 1,
        slice_idx : Optional[int] = None,
        image_shape : Optional[tuple[int]] = None,
    )->list[np.ndarray]:
    """
    Returns the n largest shapes in the provided list, in descending
    order of size
    """

    return [
        nth_largest_shape_in_list(
            shapes,
            n=i,
            slice_idx=slice_idx,
            image_shape=image_shape,
        )
        for i in range(1,n+1)
    ]


def polygon_to_mask(polygon, image_shape : tuple[int,int]) -> np.ndarray:
    """
    polygon : a holoviews.element.Polygons object
    image_shape : a tuple of (height, width)
    """
    raise NotImplementedError()
    # mask = np.zeros(image_shape, dtype=bool)
    # if isinstance(polygon, Polygons):
    #     for edges in polygon.data:
    #         path = mplPath(list(zip(edges['x'], edges['y'])),closed=True)
    #         mask = mask | path_to_mask(path, image_shape)

    # elif isinstance(polygon, Path):
    #     path = mplPath(polygon.data[0], closed = True)
    #     mask = mask | path_to_mask(path, image_shape)

    # elif isinstance(polygon, np.ndarray):
    #     # From Napari.
    #     # presumes the _last two_ dimensions are y and x
    #     if polygon.shape[-1] != 2:
    #         # Ignore the z dimension, or any others
    #         polygon = polygon[..., -2:]

    #     polygon = polygon[..., 1::-1]  # flip y, x to x, y

    #     path = mplPath(polygon, closed = False)
    #     mask = mask | path_to_mask(path, image_shape)

    # return mask

def path_to_mask(path : mplPath, image_shape : tuple[int,int]) -> np.ndarray:
    """
    path : a holoviews.element.Path object
    image_shape : a tuple of (height, width)
    """
    xx, yy = np.meshgrid(*[np.arange(0,dimlen,1) for dimlen in image_shape[::-1]])
    x, y = xx.flatten(), yy.flatten()
    points = np.vstack((x,y)).T
    mask = path.contains_points(points)
    mask = mask.reshape(image_shape)
    return mask

def point_inside_rays(ray1 : np.ndarray, ray2 : np.ndarray, point : tuple[float,float], origin : tuple[float,float]) -> bool:
    """
    Whether or not a point is inside the region bounded by two rays
    """
    angle_between_main_rays = angle_between(ray1, ray2)
    angles_between_probe = [angle_between(np.array(point) - np.array(origin), ray) for ray in [ray1,ray2]]
    if all(map(lambda x: x < angle_between_main_rays, angles_between_probe)):
        return True
    return False

def intersection_of_line_and_ray(line : Iterable, ray : np.ndarray, origin : np.ndarray) -> tuple[float,float]:
    """
    line : either a hv.element.Path or a pair of endpoints in an Iterable
    
    ray : an ndarray corresponding to (dy,dx)

    origin : an array corresponding to the ray's point of origin

    Returns point at which a ray intersects a line segment (if at all). The line
    should be a hv.Path while the ray is an array describing the vector as a (dx,dy),
    plus a tuple corresponding to the origin of the ray.
    
    Will return None if:
        
        1) the line and ray do not intersect within the confines of the line

        OR

        2) the line and ray intersect in the opposite direction from which the
        ray emanates from the point of origin. 
    """

    ## Outline
    #
    # 1) Convert both the line and the ray into the equations of a line
    # 2) Find the point of intersection of the two lines projecting to infinity
    # 3) Test above conditions: whether in the scope of the line or behind the point of origin.

    # Find equations of infinite line from the hv.element.Path

    try:
        # derives a line from its endpoints
        bounded_line = InfiniteLine.from_points(*line)
        endpts = line
    except SyntaxError:
        raise ValueError(f"Argument line is of type {type(line)}, not an Iterable or a hv.element.Path")

    ray_line = InfiniteLine.from_ray(ray, origin)

    intersection = ray_line.intersect(bounded_line)

    if not between_points(intersection, endpts):
        return None

    # To test if it's along the ray line or behind it, 
    # dot the ray with the intersection - the origin.
    # If it's positive, agree
    vector_to_intersection = np.array(intersection) - np.array(origin)

    if np.dot(ray, vector_to_intersection) <= 0:
        return None

    return intersection

def intersection_of_two_lines(path1, path2)->tuple[float, float]:
    """
    For two BOUNDED lines defined by their endpoints!

    Uses the same shorthand as
    https://en.wikipedia.org/wiki/Line%E2%80%93line_intersection#Given_two_points_on_each_line
    to find intersection from two points on each BOUNDED line
    """
    raise NotImplementedError()
    # # x coords of points on paths
    # x1, x2 = path1.data[0]['x']
    # x3, x4 = path2.data[0]['x']

    # # y coords of points on paths
    # y1, y2 = path1.data[0]['y']
    # y3, y4 = path2.data[0]['y']

    # # x coord of intercept
    # px = (x1*y2 - y1*x2)*(x3-x4) - (x1-x2)*(x3*y4 - y3*x4)
    # py = (x1*y2 - y1*x2)*(y3-y4) - (y1-y2)*(x3*y4 - y3*x4)

    # # common denominator for below
    # D = (x1-x2)*(y3-y4) - (y1-y2)*(x3-x4)
    # px /= D
    # py /= D

    # return (px, py)

def intersections_of_polygon_and_ray(poly, ray : np.ndarray, origin : np.ndarray, include_line_idx : bool = False) -> list:
    """
    Returns a list of the points of intersection between a ray and a polygon.

    If include_line_idx is set to true, it returns a list of tuples: the intersection
    point and the index of the line segment of the polygon
    """
    raise NotImplementedError()

    # line_segments = list(pairwise(zip(poly.data[0]['x'], poly.data[0]['y']))) # zip the coordinates into points, then pair them up
    
    # # add the wrapped-around endpoints (last point -> first)
    # line_segments += [((poly.data[0]['x'][-1], poly.data[0]['y'][-1]), (poly.data[0]['x'][0], poly.data[0]['y'][0]))]

    # # Now line_segments is of the form [(point1, point2), (point2, point3), ... (pointn,point1)]
    # if not include_line_idx:
    #     linewise_intersections = [intersection_of_line_and_ray(line_segment, ray, origin) for line_segment in line_segments]
    #     return [intersect for intersect in linewise_intersections if not intersect is None]
    # else:
    #     linewise_intersections = [(intersection_of_line_and_ray(line_segments[idx], ray, origin), idx) for idx in range(len(line_segments))]
    #     return [intersect for intersect in linewise_intersections if not intersect[0] is None] 

def walk_along_polygon(
        polygon_points : list[tuple[float,float]],
        start_idx : int,
        direction : float,
        intersections : list
    ) -> list:
    """
    Walks along the points of polygon_points from the start_idx along the direction specified until
    it hits one of the intersections. Then it pops that intersection out of the list

    Returns a list of all points encountered
    """
    encountered_points = []
    npoints = len(polygon_points)
    direction = (-1)**(direction > 0) # 1 if direction positive, -1 if direction negative
    curr_idx = int(start_idx)
    end_vector_idxs = [intersection[1] for intersection in intersections] # get the index of the segments intersecting the end ray
    
    # walk until you hit one of the end rays. If you started on one of the end rays, great
    # that means you skip this part and you just grab the end ray
    while curr_idx not in end_vector_idxs:
        # if direction is positive, then curr_idx+1 is the point to add to the list
        # if direction is negative, then curr_idx is the point to add
        encountered_points += [polygon_points[(curr_idx +(direction>0))%npoints]]
        curr_idx = (curr_idx + direction) % npoints
    hit_index = end_vector_idxs.index(curr_idx)

    # also want to remove this point from the intersections list!
    hit_point, hit_segment = intersections.pop(hit_index)

    encountered_points += [hit_point]
    return encountered_points

def polygon_bounded_by_rays(poly, rays : list[np.ndarray], origin : np.ndarray):
    """
    Takes a pair of rays, intersects them with a polygon, and then returns a polygon corresponding to the
    segment of the polygon bounded between those rays. If only one intersects the polygon, returns the portion
    inside the two. Returns None if no part of the polygon is within the scope of the rays.
    """
    raise NotImplementedError()
    ## Outline:
            #
            # 1) Find where each ray intersects the Fan polygon
            # by checking each edge for intersection with the ray.
            #
            # 2a) If both rays intersect twice, grab the points
            # of intersect, trace them along the polygon and
            # rays, and then you have your polygon!
            # 
            # 2b) If one ray intersects twice and one intersects
            # once or zero times, it is on or past a polygon edge.
            # Then the polygon is actually just tracing the
            # polygon along its edges between the two points of
            # intersection of the one ray. But pick the series of
            # edges that lies within the two rays!
            # 
            # 2c) If neither ray intersects more than once, then the
            # entire polygon is the mask or no part of the polygon is the
            # mask. Figure out which is inside the two rays and decide.
            # 
            # 2d) At least one ray intersects MORE than twice. For now
            # I'm just going to make this one raise an error. This is a
            # legitimate use case typically and I will correct it, but
            # for now it presumes the polygon and rays do not allow this.

    # # Get all intersections between the polygon and the bounding rays
    # vector_poly_intersections = [intersections_of_polygon_and_ray(poly, ray, origin, include_line_idx=True) for ray in rays]

    # if any(map(lambda x: len(x) > 2, vector_poly_intersections)):
    #     raise ValueError(
    #         "At least one provided ray intersects the source polygon more than twice! "
    #         "I haven't yet enabled this functionality. I really should. If you encounter "
    #         "this error, please get mad at me. It's not your fault the ROI is bendy (SCT)."
    #     )

    # # Now we need to find the points to constitute the final polygon

    # # It will be made of a subset of the source polygon's points, so
    # # let's get those from the outset.
    # polygon_points = list(zip(poly.data[0]['x'], poly.data[0]['y']))

    # # Now let's figure out which points to take (and the intersection points).
    # points = []

    # # Standard case, two intersections for both vectors:
    # # Marches along edge of polygon (in direction that starts
    # # by going inside the two vectors) until you reach a line intersected
    # # by the other vector. Then take the intersect point with the other vector,
    # # climb along the vector, and do the process in the opposite direction
    # if all(map(lambda x: len(x) == 2, vector_poly_intersections)):
        
    #     # vector_idx is the start ray, 1-vector_idx is the end ray
    #     vector_idx = 0
    #     while len(vector_poly_intersections) > 0:
    #         start_point, start_idx = vector_poly_intersections[vector_idx].pop(0)
    #         points += [start_point]

    #         # check if the polygon point is inside or outside of the region subtended
    #         # by the rays (to check direction). If the angle between the probe_ray and
    #         # both edge rays is < 0 the angle between the two, then the probe_ray is between
    #         # the two rays.
    #         probe_point = polygon_points[start_idx]
    #         direction = -1
    #         if point_inside_rays(*rays, probe_point, origin):
    #             direction = 1

    #         points += walk_along_polygon(
    #             polygon_points,
    #             start_idx,
    #             direction,
    #             vector_poly_intersections[1-vector_idx]
    #         )
    #         # There's a cute way to do this with map, I thought this was more readable though
    #         while [] in vector_poly_intersections: # get rid of empties
    #             vector_poly_intersections.remove([]) 

    #         vector_idx = 1-vector_idx

    # # Probably happens a few times per polygon: at least one ray doesn't pass through the polygon
    
    # # Edgiest-case, neither passes through the polygon. It's either INSIDE the rays (return the whole polygon)
    # # or OUTSIDE the rays (return None)
    # elif not any(map(lambda x: len(x) >= 2, vector_poly_intersections)):
    #     # just check if at least one point is inside the bounding rays
    #     if point_inside_rays(*rays, polygon_points[0], origin):
    #         return poly
    #     else:
    #         return None
    
    # # One passes through the polygon, one does not.
    # # you can just walk along the polygon until you self intersect
    # else:
    #     # which one does pass through?
    #     intersections = next(intersections for intersections in vector_poly_intersections if len(intersections) == 2)
    #     probe_point, start_idx = intersections.pop(0)
    #     points += [probe_point]
    #     direction = 1
    #     if point_inside_rays(*rays, probe_point, origin):
    #         direction = -1
    #     points += walk_along_polygon(polygon_points, start_idx, direction,intersections)
    
    # return hv.Polygons(
    #     {
    #         'x' : [point[0] for point in points],
    #         'y' : [point[1] for point in points]
    #     }
    # )

def vector_pointing_along_path(path, point : tuple[float,float]) -> np.ndarray:
    """
    Returns a vector pointing from the point along the path.

    Vector is of form <x,y>

    Point must be of form (x,y)!
    """
    raise NotImplementedError()
    x_val = path.data[0]['x'][0] # take any point, first for simplicity
    y_val = path.data[0]['y'][0]

    return np.array([x_val - point[0], y_val - point[1]])

def rotation_matrix(theta : float) -> np.ndarray:
    """ Returns a 2x2 array corresponding to rotation by the angle theta """
    return np.array([
        (np.cos(theta), -np.sin(theta)),
        (np.sin(theta), np.cos(theta))
    ])

def angle_between(vector1 : np.ndarray, vector2 : np.ndarray) -> float:
    """ The angle between two vectors """
    return np.arccos( np.dot(vector1, vector2) / (np.linalg.norm(vector1) * np.linalg.norm(vector2)) )

def between_points(point : tuple[float,float], points : list)->bool:
    """ Whether a point is between a set of points' x and y bounds """
    x_vals = [point[0] for point in points]
    y_vals = [point[1] for point in points]
    if not (min(x_vals) <= point[0] <= max(x_vals)):
        return False
    if not (min(y_vals) <= point[1] <= max(y_vals)):
        return False
    return True

class InfiniteLine():
    """
    Convenience class for interacting with infinite lines.
    """

    def __init__(self, slope : float, intercept : float):
        """
        Requires a slope (dy / dx) and an intercept (single float value)
        """

        self.slope = float(slope)
        self.intercept = float(intercept)

    def intersect(self, other_line : 'InfiniteLine')->tuple[float,float]:
        """ All non-parallel lines will intersect """
        if other_line.slope == self.slope:
            return None
        x_coord = (other_line.intercept - self.intercept) / (self.slope - other_line.slope)
        y_coord = self.slope * x_coord + self.intercept
        return (x_coord, y_coord)

    def from_path(path) -> 'InfiniteLine':
        """ Derives a line from a holoviews Path's first two elements """
        points = tuple(zip(path.data[0]['x'], path.data[0]['y']))
        return InfiniteLine.from_points(points[0], points[1])

    def from_points(point1 : tuple[float,float], point2 : tuple[float,float]) -> 'InfiniteLine':
        """ Derives a line from two points on the line """
        dx = point2[0] - point1[0]
        dy = point2[1] - point1[1]
        slope = dy/dx
        intercept = point1[1] - slope*point1[0] # b = y - mx
        return InfiniteLine(slope, intercept)

    def from_ray(ray : np.ndarray, origin : np.ndarray) -> 'InfiniteLine':
        """ Derives a line from a ray and an origin """
        slope = ray[1]/ray[0]
        intercept = origin[1] - slope*origin[0]
        return InfiniteLine(slope, intercept)


