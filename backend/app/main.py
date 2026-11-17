from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from .api import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(title="SDLC-AI API", version="0.2.0", lifespan=lifespan)
app.include_router(router, prefix="/api")

@app.get("/health")
def health():
    return {"status": "ok"}

STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/demo", StaticFiles(directory=STATIC_DIR), name="demo")


@app.get("/", include_in_schema=False)
def demonstration():
    return FileResponse(STATIC_DIR / "index.html")
