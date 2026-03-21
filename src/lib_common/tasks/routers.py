from fastapi import APIRouter, Depends, status

from ..app.schemas import Response, PageData
from ..app.dependencies import ConditionParams
from .schemas import JobConfigAdd, JobConfigSet, JobConfigGet, JobConfigFilter
from .services import JobConfigService
from .dependencies import job_config_service


router = APIRouter(prefix="/task", tags=["task"])


@router.get(
    "/job_configs",
    response_model=Response[PageData[JobConfigGet]],
    status_code=status.HTTP_200_OK,
)
async def list_job_configs(
    conditions: dict = Depends(ConditionParams(JobConfigFilter)),
    service: JobConfigService = Depends(job_config_service),
):
    data = await service.list(**conditions)
    return {"code": 200, "data": data}


@router.get(
    "/job_configs/{job_config_id}",
    response_model=Response[JobConfigGet],
    status_code=status.HTTP_200_OK,
)
async def get_job_config(job_config_id: str, service: JobConfigService = Depends(job_config_service)):
    data = await service.get(job_config_id)
    return {"code": 200, "data": data}


@router.post(
    "/job_configs",
    response_model=Response[JobConfigGet],
    status_code=status.HTTP_201_CREATED,
)
async def add_job_config(job_config: JobConfigAdd, service: JobConfigService = Depends(job_config_service)):
    data = await service.add(job_config)
    return {"code": 200, "data": data}


@router.put(
    "/job_configs/{job_config_id}",
    response_model=Response[JobConfigGet],
    status_code=status.HTTP_200_OK,
)
async def set_job_config(
    job_config_id: str, job_config: JobConfigSet, service: JobConfigService = Depends(job_config_service)
):
    data = await service.set(job_config_id, job_config)
    return {"code": 200, "data": data}


@router.delete(
    "/job_configs/{job_config_id}",
    response_model=Response[str],
    status_code=status.HTTP_200_OK,
)
async def del_job_config(job_config_id: str, service: JobConfigService = Depends(job_config_service)):
    await service.delete(job_config_id)
    return {"code": 200, "data": "success"}
