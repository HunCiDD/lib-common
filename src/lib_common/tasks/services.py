from ..app.services import BaseService
from .models import JobConfig
from .schemas import JobConfigAdd, JobConfigSet, JobConfigGet
from .repositories import job_config_repo


class JobConfigService(BaseService[JobConfig, JobConfigAdd, JobConfigSet, JobConfigGet]):
    def __init__(self):
        super().__init__(repo=job_config_repo, schema_cls=TaskCronJobGet)