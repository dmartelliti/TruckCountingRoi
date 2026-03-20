from core.utils.tracking_detector import TrackingDetector
from core.utils.track_manager import TrackManager
from core.dtos.track_data_frame_dto import TrackDataFrameDto
from core.dtos.detections_dto import DetectionsDto
from core.dtos.event_dto import EventDto
from core.dtos.roi_dto import RoiDTO
from core.utils.flow_event_detector import FlowEventDetector
from core.utils.roi_manager import RoiManager
from typing import List, Optional
import logging


class TruckCounterPipeline:
    name = "truck_counter"

    def __init__(self, model_name: str = "yolov8n.pt"):
        # Logger
        self.logger = logging.getLogger("TruckCounterPipeline")

        # Core components
        self.tracking_detector = TrackingDetector(model_name=model_name)
        self.track_manager = TrackManager()
        self.roi_manager = RoiManager()
        self.flow_event_detector = FlowEventDetector()

        # Internal state
        self.frame_id = 0

        self.logger.info(f"Pipeline initialized | model={model_name}")

    # ==========================================
    # PUBLIC
    # ==========================================
    def process(self, frame, rois: List[RoiDTO]) -> List[EventDto]:
        for roi in rois:
            if roi.image_size is None:
                roi.image_size = frame.shape[:2]

        detections: DetectionsDto = self.tracking_detector.process(
            frame,
            frame_id=self.frame_id
        )

        if len(detections.detections) != 0:
            # self.logger.info(
            #     f"Detections obtained | frame={self.frame_id} - detections={len(detections.detections)}" +
            #     f" - {[(det.track_id, det.bbox.center_cartesian) for det in detections.detections]}"
            # )
            pass

        track_data_frame: TrackDataFrameDto = self.track_manager.add(detections)

        rois: List[RoiDTO] = self.roi_manager.process(rois)

        events: List[EventDto] = self.flow_event_detector.detect(track_data_frame, rois)

        if len(events) != 0:
            self.logger.info(
                f"Event detected | frame={self.frame_id} - Amount={len(events)}"
            )

        self.frame_id += 1

        return events

    def update_config(self, configs: dict) -> None:

        self.tracking_detector.update_config(configs)
        #self.track_manager.update_config(configs)
        #self.roi_manager.update_config(configs)
        #self.flow_event_detector.update_config(configs)
