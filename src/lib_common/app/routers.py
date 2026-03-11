from fastapi import APIRouter, status

from ..logger.configs import loggers

router = APIRouter(tags=["app_base"])
run_logger = loggers.get_logger("run")


@router.get("/home", status_code=status.HTTP_200_OK)
async def home():
    run_logger.info("home")
    return {"message": "Hello World"}


@router.get("/health")
async def health():
    return {"status": "alive"}
