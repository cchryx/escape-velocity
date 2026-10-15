"""Matching API. For now it only has a health check."""

from fastapi import FastAPI

app = FastAPI(title="Escape Velocity API")


@app.get("/health")
def health():
    return {"ok": True}
