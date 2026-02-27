from fastapi import APIRouter

from backend.app.config import settings

router = APIRouter()


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "healthy", "app_name": settings.APP_NAME}
