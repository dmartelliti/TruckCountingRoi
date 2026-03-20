from core.dtos.track_data_frame_dto import TrackDataFrameDto
from core.dtos.detections_dto import DetectionsDto
from .track_window_manager import TrackWindowManager

import pandas as pd
from typing import Optional


class TrackManager(TrackWindowManager):

    def __init__(self, window: int = 30, model_version: str | None = None):
        super().__init__(window)
        self.model_version = model_version
        self.tracks = TrackDataFrameDto()

    def add(self, detections: Optional[DetectionsDto]) -> TrackDataFrameDto:

        if detections is None or len(detections.detections) == 0:
            return self.tracks

        rows = []

        for det in detections.detections:
            rows.append({
                "frame_id": detections.frame_id,
                "timestamp": getattr(det, "timestamp", None),
                "track_id": det.track_id,
                "detection": det
            })

        if rows:
            new_df = pd.DataFrame(rows)
            self.tracks.df = pd.concat([self.tracks.df, new_df], ignore_index=True)

        # aplicar ventana
        self.tracks = self.update(self.tracks)

        return self.tracks

    def get_tracks(self) -> TrackDataFrameDto:
        return self.tracks