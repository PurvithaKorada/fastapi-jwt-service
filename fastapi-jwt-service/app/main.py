from contextlib import asynccontextmanager

from fastapi import FastAPI

from . import models  # noqa: F401  (registers tables)
from .database import Base, engine
from .routers_auth import router as auth_router
from .routers_items import router as items_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="JWT Auth Microservice",
    description="FastAPI service with bcrypt password hashing, JWT Bearer auth, and CRUD.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(auth_router)
app.include_router(items_router)


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}
