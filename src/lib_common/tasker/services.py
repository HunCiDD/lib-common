from ..app.services import BaseService
from .models import TaskCronJob
from .schemas import TaskCronJobAdd, TaskCronJobSet, TaskCronJobGet


class TaskCronJobService(BaseService[TaskCronJob, TaskCronJobAdd, TaskCronJobSet, TaskCronJobGet]):
    def __init__(self):
        super().__init__(model_cls=TaskCronJob, schema_cls=TaskCronJobGet)
