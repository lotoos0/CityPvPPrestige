from fastapi import FastAPI

from app.routes import auth

app = FastAPI(title="CityPvPPrestige API")

app.include_router(auth.router)


@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/health")
def health():
    return {"status": "ok"}
