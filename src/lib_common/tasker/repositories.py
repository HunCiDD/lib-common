from ..app.repositories import BaseRepository
from .models import JobConfig, JobRecord


class JobConfigRepository(BaseRepository[JobConfig]):
    def __init__(self):
        super().__init__(model_cls=JobConfig)


class JobRecordRepository(BaseRepository[JobRecord]):
    def __init__(self):
        super().__init__(model_cls=JobRecord)


job_config_repo = JobConfigRepository()
