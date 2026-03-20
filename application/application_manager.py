import time
import logging
import cv2

from application.camera_stream import CameraStream
from application.frame_scheduler import FrameScheduler
from application.pipeline_factory import PipelineFactory
from core.dtos.roi_dto import RoiDTO
from application.dtos.job_config_dto import JobConfigDto
from application.dtos.frame_stream_dto import FrameStreamDto

from application.dtos.frame_job_dto import FrameJob
from typing import Optional


class ApplicationManager:

    def __init__(self, config):

        self.config = config
        self.scheduler = FrameScheduler()

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s"
        )

        self.logger = logging.getLogger("ApplicationManager")

    # ==========================
    # MAIN LOOP
    # ==========================

    def run(self, event_queue, instruction_queue, frame_queue):

        self.logger.info("ApplicationManager started.")

        while True:

            try:

                self._consume_instructions(instruction_queue)

                frame_job: Optional[FrameJob] = self.scheduler.get_next_job()

                if frame_job is None:
                    time.sleep(0.02)
                    continue


                # enviar frame al stream siempre
                frame_queue.put(
                    FrameStreamDto(
                        camera_id=frame_job.camera_id,
                        frame=frame_job.frame,
                        rois=frame_job.rois,
                    )
                )

                # si no hay pipeline aún, solo streaming
                if frame_job.pipeline is None:
                    continue

                self._process_frame(
                    frame_job,
                    event_queue
                )

                time.sleep(0.02)

            except Exception as e:

                self.logger.exception(
                    f"Critical error in main loop: {e}"
                )

                time.sleep(0.5)

    # ==========================
    # INSTRUCTION HANDLING
    # ==========================

    def _consume_instructions(self, queue):

        if queue.empty():
            return

        command = queue.get()

        self.logger.info(f"Received command: {command}")

        self._handle_command(command)

    def _handle_command(self, command):

        if command.type == "load_camera":
            self._load_camera(command.payload)

        elif command.type == "add_pipeline":
            self._add_pipeline(command.payload)

        elif command.type == "update_roi":
            self._update_roi(command.payload)

        elif command.type == "remove_pipeline":
            self._remove_pipeline(command.payload)

        elif command.type == "update_config":
            self._update_config(command.payload)

        else:
            self.logger.warning(
                f"Unknown command: {command.type}"
            )

    # ==========================
    # COMMAND IMPLEMENTATIONS
    # ==========================

    def _update_config(self, payload):
        camera_id = payload["camera_id"]
        pipeline_name = payload["pipeline_name"]
        configs = payload["configs"]
        job_id = f"{camera_id}_{pipeline_name}"

        self.scheduler.update_configs(configs, job_id)


    def _load_camera(self, payload):

        camera_id = payload["camera_id"]
        source = payload["source"]

        camera = CameraStream(camera_id, source)

        self.scheduler.add_camera(
            camera_id,
            camera
        )

        self.logger.info(
            f"Camera loaded: {camera_id}"
        )

    def _add_pipeline(self, payload):

        camera_id = payload["camera_id"]
        pipeline_name = payload["pipeline_name"]
        rois_data = payload["rois"]


        rois = [RoiDTO(**roi_data) for roi_data in rois_data]

        pipeline = PipelineFactory.create(
            pipeline_name
        )

        job = JobConfigDto(
            camera_id=camera_id,
            pipeline=pipeline,
            rois=rois
        )

        self.scheduler.add_job(job)

        self.logger.info(
            f"Pipeline {pipeline_name} added to camera {camera_id}"
        )

    def _update_roi(self, payload):
        camera_id = payload["camera_id"]
        pipeline_name = payload["pipeline_name"]
        roi_data = payload["roi"]

        roi = RoiDTO(**roi_data)
        job_id = f"{camera_id}_{pipeline_name}"

        status = self.scheduler.update_roi(roi, job_id)
        self.logger.info(
            f"Update roi - Status: {status}"
        )



    def _remove_pipeline(self, payload):

        job_id = payload["job_id"]

        self.scheduler.remove_job(job_id)

        self.logger.info(
            f"Pipeline removed: {job_id}"
        )

    # ==========================
    # FRAME PROCESSING
    # ==========================

    @staticmethod
    def _process_frame(frame_job: FrameJob, event_queue):

        if frame_job.frame is None:
            return

        events = frame_job.pipeline.process(frame_job.frame, frame_job.rois)

        if not events:
            return

        for event in events:
            event.camera_id = frame_job.camera_id
            event.pipeline_name = getattr(frame_job.pipeline, "name", frame_job.pipeline.__class__.__name__)
            event.frame = frame_job.frame.copy()  # Guardamos copia original

            # -------- Dibujar la última detección --------
            if event.detections:
                last_det = event.detections[-1]  # Tomamos la última detección
                bbox = last_det.bbox
                label = last_det.label

                # Coordenadas enteras para dibujar
                x1, y1, x2, y2 = map(int, [bbox.x1, bbox.y1, bbox.x2, bbox.y2])

                # Dibujar rectángulo (bbox)
                cv2.rectangle(event.frame, (x1, y1), (x2, y2), color=(0, 255, 0), thickness=2)

                # Escribir label arriba del bbox
                cv2.putText(
                    event.frame,
                    label,
                    (x1, max(y1 - 10, 0)),  # arriba del bbox
                    cv2.FONT_HERSHEY_SIMPLEX,
                    fontScale=0.6,
                    color=(0, 255, 0),
                    thickness=2
                )

            # Guardar el event en la cola
            event_queue.put(event)