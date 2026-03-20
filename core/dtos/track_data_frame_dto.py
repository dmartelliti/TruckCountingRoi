from pydantic import BaseModel, Field, ConfigDict
import pandas as pd


class TrackDataFrameDto(BaseModel):

    model_config = ConfigDict(arbitrary_types_allowed=True)

    df: pd.DataFrame = Field(
        default_factory=lambda: pd.DataFrame(
            columns=["frame_id", "timestamp", "track_id", "detection"]
        )
    )

    def get_track(self, track_id: int) -> pd.DataFrame:
        return self.df[self.df.track_id == track_id]

    def get_frame(self, frame_id: int) -> pd.DataFrame:
        return self.df[self.df.frame_id == frame_id]

    def last_detection_per_track(self) -> pd.DataFrame:
        return (
            self.df
            .sort_values("frame_id")
            .groupby("track_id")
            .tail(1)
        )