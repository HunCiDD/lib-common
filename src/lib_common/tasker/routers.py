from fastapi import APIRouter, Depends, status

from ..app.schemas import Response
from .schemas import TaskCronJobGet
from .services import TaskCronJobService
from .dependencies import task_cron_job_service

router = APIRouter(prefix="/tasker", tags=["tasker"])


# @router.get(
#     "/cron_jobs",
#     response_model=Response[PageData[TaskCronJobGet]],
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(PermissionChecker("auth:menu_resources:list"))],
# )
# async def list_cron_jobs():
#     return {"code": 200, "data": []}


@router.get(
    "/cron_jobs/{cron_job_id}",
    response_model=Response[TaskCronJobGet],
    status_code=status.HTTP_200_OK,
)
async def get_cron_job(cron_job_id: str, service: TaskCronJobService = Depends(task_cron_job_service)):
    data = await service.get(cron_job_id)
    return {"code": 200, "data": data}
