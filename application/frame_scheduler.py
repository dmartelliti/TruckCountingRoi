from application.dtos.frame_job_dto import FrameJob
from typing import Optional
from core.dtos.roi_dto import RoiDTO


class FrameScheduler:

    def __init__(self):

        self.cameras = {}
        self.jobs = []
        self._job_index = 0

    # ------------------
    # Cameras
    # ------------------

    def add_camera(self, camera_id, camera_stream):

        self.cameras[camera_id] = camera_stream

    def remove_camera(self, camera_id):

        if camera_id in self.cameras:
            del self.cameras[camera_id]

        self.jobs = [
            job for job in self.jobs
            if job.camera_id != camera_id
        ]

    # ------------------
    # Jobs
    # ------------------
    def add_job(self, job_config):

        for job in self.jobs:
            if job.job_id == job_config.job_id:

                existing_roi_ids = {roi.roi_id for roi in job.rois}

                for roi in job_config.rois:
                    if roi.roi_id not in existing_roi_ids:
                        job.rois.append(roi)

                return

        self.jobs.append(job_config)

    def update_configs(self, configs, job_id):
        for job in self.jobs:
            if job.job_id == job_id:
                job.pipeline.update_config(configs)


    def update_roi(self, new_roi: RoiDTO, job_id: str):
        for job in self.jobs:
            if job.job_id == job_id:
                for i, roi in enumerate(job.rois):
                    if roi.roi_id == new_roi.roi_id:
                        job.rois[i] = new_roi
                        return True
                return False
        return False

    def remove_job(self, job_id):

        self.jobs = [
            job for job in self.jobs
            if job.job_id != job_id
        ]

    # ------------------
    # Scheduler
    # ------------------

    def get_next_job(self) -> Optional[FrameJob]:

        if not self.jobs:
            return None

        job_config = self.jobs[self._job_index]

        self._job_index = (
            (self._job_index + 1) % len(self.jobs)
        )

        camera = self.cameras.get(job_config.camera_id)

        if camera is None:
            return None

        frame = camera.read_frame()

        if frame is None:
            return None

        return FrameJob(
            job_id=job_config.job_id,
            camera_id=job_config.camera_id,
            frame=frame,
            rois=job_config.rois,
            pipeline=job_config.pipeline
        )