from ..dtos.track_data_frame_dto import TrackDataFrameDto


class TrackWindowManager:

    def __init__(self, window: int):
        self.window = window

    def update(self, tracks: TrackDataFrameDto) -> TrackDataFrameDto:
        """
        Returns a new TrackDataFrameDto containing only the last
        `window` detections per track.
        """

        df = tracks.df

        if df.empty:
            return tracks

        buffered_df = (
            df
            .sort_values("frame_id")
            .groupby("track_id")
            .tail(self.window)
            .reset_index(drop=True)
        )

        return TrackDataFrameDto(df=buffered_df)