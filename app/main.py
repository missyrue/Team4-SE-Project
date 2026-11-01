"""Application entry point: wires every router together.

Run:  uvicorn app.main:app --reload
Docs: http://127.0.0.1:8000/docs   (interactive API explorer)
"""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app import models  # noqa: F401  (makes sure every table is registered)
from app.database import Base, engine
from app.routers import admin, auth, cart, catalogue, mock_gateway, orders


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)  # create tables on first start
    yield


app = FastAPI(title="Online Bookstore System", version="1.0", lifespan=lifespan)


# ---- standard error format (SAD 4.4): {code, message} ----------------------
@app.exception_handler(HTTPException)
async def http_error(_: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": f"HTTP_{exc.status_code}", "message": str(exc.detail)},
    )


@app.exception_handler(RequestValidationError)
async def validation_error(_: Request, exc: RequestValidationError):
    errors = [
        {"field": ".".join(str(p) for p in e["loc"][1:]), "message": e["msg"]} for e in exc.errors()
    ]
    first = errors[0] if errors else {"field": "", "message": "Invalid request"}
    return JSONResponse(
        status_code=400,  # SAD uses 400 for missing/invalid input
        content={
            "code": "VALIDATION_ERROR",
            "message": f"{first['field']}: {first['message']}".strip(": "),
            "errors": errors,
        },
    )


@app.get("/api/health", tags=["system"])
def health():
    return {"status": "ok"}


for module in (auth, catalogue, cart, orders, admin, mock_gateway):
    app.include_router(module.router)

# The web UI (plain HTML/JS, no build step). Must be mounted last.
app.mount("/", StaticFiles(directory=Path(__file__).parent / "static", html=True), name="static")
