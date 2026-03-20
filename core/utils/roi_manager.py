from typing import Dict, Tuple, Optional, List
from core.dtos.roi_dto import RoiDTO


class RoiManager:

    def __init__(self):
        self._roi_cache: Dict[str, RoiDTO] = {}

    def process(self, rois: List[RoiDTO]) -> List[RoiDTO]:

        new_rois = []
        for roi in rois:
            cached_roi = self._roi_cache.get(roi.roi_id)

            # If the ROI was already processed and the polygon did not change,
            # return the cached version to avoid recomputation
            if cached_roi is not None and cached_roi.polygon == roi.polygon:
                new_rois.append(cached_roi)
                continue

            polygon = roi.polygon

            # Compute the vertical bounds of the polygon
            ys = [p[1] for p in polygon]
            y_mid = (min(ys) + max(ys)) / 2

            intersections = []

            # Iterate over each polygon edge
            for i in range(len(polygon)):

                x1, y1 = polygon[i]
                x2, y2 = polygon[(i + 1) % len(polygon)]

                # Check if the horizontal mid-line intersects this segment
                if (y1 <= y_mid <= y2) or (y2 <= y_mid <= y1):

                    if y1 == y2:
                        # Horizontal segment case
                        intersections.append((x1, y_mid))
                        intersections.append((x2, y_mid))
                    else:
                        # Linear interpolation to find the intersection point
                        t = (y_mid - y1) / (y2 - y1)
                        x = x1 + t * (x2 - x1)
                        intersections.append((x, y_mid))

            # Select the leftmost and rightmost intersection points
            reference_line: Optional[
                Tuple[Tuple[float, float], Tuple[float, float]]
            ] = None

            if len(intersections) >= 2:
                intersections.sort(key=lambda p: p[0])
                reference_line = (intersections[0], intersections[-1])

            # Store the computed reference line inside the ROI
            roi.reference_line = reference_line

            # Cache the processed ROI
            self._roi_cache[roi.roi_id] = roi

            new_rois.append(roi)

        return new_rois
