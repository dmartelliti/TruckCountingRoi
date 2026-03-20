from dataclasses import dataclass, field
from core.dtos.roi_dto import RoiDTO


@dataclass
class JobConfigDto:
    camera_id: str
    pipeline: object
    rois: list[RoiDTO] = field(default_factory=list)
    job_id: str | None = None

    def __post_init__(self):
        if self.job_id is None:
            pipeline_name = getattr(self.pipeline, "name", self.pipeline.__class__.__name__)
            self.job_id = f"{self.camera_id}_{pipeline_name}"