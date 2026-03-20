from pydantic import BaseModel
from typing import List, Tuple, Optional
from functools import cached_property
from shapely.geometry import Polygon
from matplotlib.path import Path


class RoiDTO(BaseModel):

    roi_id: str
    roi_name: str

    polygon: List[Tuple[int, int]]

    reference_line: Optional[Tuple[Tuple[int, int], Tuple[int, int]]] = None

    image_size: Optional[Tuple[int, int]] = None

    @cached_property
    def polygon_cartesian(self) -> Optional[List[Tuple[int, int]]]:

        if self.image_size is None:
            return None

        h, _ = self.image_size

        return [(x, h - y) for x, y in self.polygon]

    @cached_property
    def reference_line_cartesian(self) -> Optional[Tuple[Tuple[int, int], Tuple[int, int]]]:

        if self.image_size is None or self.reference_line is None:
            return None

        h, _ = self.image_size

        (x1, y1), (x2, y2) = self.reference_line

        return (x1, h - y1), (x2, h - y2)

    @cached_property
    def shapely_polygon(self):

        if self.polygon_cartesian is None:
            return None

        return Polygon(self.polygon_cartesian)

    @cached_property
    def path(self):

        if self.polygon_cartesian is None:
            return None

        return Path(self.polygon_cartesian)
