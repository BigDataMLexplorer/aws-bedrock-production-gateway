from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router

app = FastAPI(title="AWS Bedrock Production AI Gateway", version="0.1.0")
app.include_router(router)
WEB = Path(__file__).resolve().parent / "web"
app.mount("/static", StaticFiles(directory=WEB / "static"), name="static")


@app.get("/demo", response_class=HTMLResponse, include_in_schema=False)
def demo() -> HTMLResponse:
    return HTMLResponse((WEB / "index.html").read_text(encoding="utf-8"))


@app.get("/architecture", response_class=HTMLResponse, include_in_schema=False)
def architecture() -> HTMLResponse:
    return HTMLResponse((WEB / "architecture.html").read_text(encoding="utf-8"))
