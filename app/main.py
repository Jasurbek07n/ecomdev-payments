from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api import debtors, payments, students
from app.core.config import settings

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title=settings.app_title)

app.include_router(students.router)
app.include_router(payments.router)
app.include_router(debtors.router)

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {"title": settings.app_title})


@app.get("/students-page", response_class=HTMLResponse, include_in_schema=False)
def students_page(request: Request):
    return templates.TemplateResponse(request, "students.html", {"title": settings.app_title})


@app.get("/healthz", include_in_schema=False)
def healthz():
    return {"ok": True}
