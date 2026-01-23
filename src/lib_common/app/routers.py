from fastapi import APIRouter, status

from libs.common.configs import LOGGERS

router = APIRouter(tags=["app_base"])
run_logger = LOGGERS.get_logger("run")


@router.get("/home", status_code=status.HTTP_200_OK)
async def home():
    run_logger.info("home")
    return {"message": "Hello World"}
