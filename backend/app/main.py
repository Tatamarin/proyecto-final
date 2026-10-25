from contextlib import asynccontextmanager
from fastapi import FastAPI
from .api import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(title="SDLC-AI API", version="0.1.0", lifespan=lifespan)
app.include_router(router, prefix="/api")

@app.get("/health")
def health():
    return {"status": "ok"}
