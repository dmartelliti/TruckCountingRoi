from core.dtos.track_data_frame_dto import TrackDataFrameDto
from ..dtos.event_dto import EventDto
from ..constants import FlowDirectionCode
from .line_2d import Line2D
from core.dtos.roi_dto import RoiDTO
from core.filters.roi_track_filter import RoiTrackFilter
from typing import List


class FlowEventDetector:

    def __init__(self, window: int = 10, roi_filter=None):
        self.line_2d = None
        self._line_points = None

        self.window = window
        self._event_id = 0

        # tracks que ya dispararon evento
        self._processed_tracks: set[int] = set()

        self.roi_filter = roi_filter or RoiTrackFilter()

    # -------------------------------------------------

    def detect(self, track_data_frame: TrackDataFrameDto, rois: List[RoiDTO]) -> list[EventDto]:
        events = []
        for roi in rois:
            if not self._update_line(roi):
                continue

            df = track_data_frame.df

            if df.empty:
                continue

            # ---- keep last N frame_ids ----
            last_frames = sorted(df.frame_id.unique())[-self.window:]
            df = df[df.frame_id.isin(last_frames)]

            # ---- ignore processed tracks ----
            df = df[~df.track_id.isin(self._processed_tracks)]

            # ---- filter by roi ----
            df = self.roi_filter.filter_df(df, roi)
            if df.empty:
                continue

            df = df.sort_values(["track_id", "frame_id"])

            # events: list[EventDto] = []

            # ---- process per track ----
            for track_id, group in df.groupby("track_id"):

                detections = group["detection"].tolist()

                prev_status = None

                for i, det in enumerate(detections):

                    status = self.line_2d.half_plane(
                        det.bbox.center_cartesian
                    )

                    if status == 0:
                        continue

                    if prev_status is not None and status != prev_status:

                        direction = self._resolve_direction(prev_status, status)

                        if direction is not None:

                            context = self._get_window(detections, i)

                            event = EventDto(
                                id=self._next_id(),
                                detections=context,
                                event_frame=det.frame_id,
                                status=direction,
                                roi=roi
                            )

                            events.append(event)

                            # marcar track como procesado
                            self._processed_tracks.add(track_id)

                            break

                    prev_status = status

        return events

    # -------------------------------------------------

    @staticmethod
    def _resolve_direction(prev, curr):

        if prev == -1 and curr == 1:
            return FlowDirectionCode.ENTRY

        if prev == 1 and curr == -1:
            return FlowDirectionCode.EXIT

        return None

    # -------------------------------------------------

    def _get_window(self, detections, index):

        start = max(0, index - self.window)
        end = min(len(detections), index + self.window + 1)

        return detections[start:end]

    # -------------------------------------------------

    def _next_id(self):

        eid = self._event_id
        self._event_id += 1
        return eid

    def _update_line(self, roi: RoiDTO):

        if roi is None or roi.reference_line_cartesian is None:
            return False

        p1, p2 = roi.reference_line_cartesian
        current_points = (p1, p2)

        if self._line_points != current_points:
            self.line_2d = Line2D(p1=p1, p2=p2)
            self._line_points = current_points

        return True