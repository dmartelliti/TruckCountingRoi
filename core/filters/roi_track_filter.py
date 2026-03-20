import numpy as np
import pandas as pd
from matplotlib.path import Path

from core.dtos.track_data_frame_dto import TrackDataFrameDto
from core.dtos.roi_dto import RoiDTO


class RoiTrackFilter:

    def __init__(self):
        # cache simple para evitar reconstruir Path
        self._last_polygon = None
        self._path = None

    # -------------------------------------------------

    def filter(
        self,
        track_data_frame: TrackDataFrameDto,
        roi: RoiDTO
    ) -> TrackDataFrameDto:

        if roi is None or roi.polygon_cartesian is None:
            return track_data_frame

        df = track_data_frame.df

        filtered_df = self.filter_df(df, roi)

        return track_data_frame.model_copy(update={"df": filtered_df.copy()}, )

    # -------------------------------------------------

    def filter_df(self, df: pd.DataFrame, roi: RoiDTO) -> pd.DataFrame:
        if df.empty:
            return df

        path = self._get_path(roi)

        # extracción de coordenadas (único loop Python)
        cords = np.array([
            det.bbox.center_cartesian
            for det in df["detection"]
        ])

        mask = path.contains_points(cords)

        return df[mask]

    def _get_path(self, roi: RoiDTO) -> Path:

        polygon = roi.polygon_cartesian

        # cache simple (evita reconstrucción innecesaria)
        if polygon != self._last_polygon:
            self._path = Path(polygon)
            self._last_polygon = polygon

        return self._path