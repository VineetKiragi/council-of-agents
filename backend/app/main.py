from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.routes.health import router as health_router
from backend.app.api.routes.sessions import router as sessions_router

app = FastAPI(title="Council of Agents API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api")
app.include_router(sessions_router, prefix="/api")


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Council of Agents API", "docs": "/docs"}
