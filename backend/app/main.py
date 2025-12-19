from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import auth, city, stats, pvp

app = FastAPI(title="CityPvPPrestige API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(city.router)
app.include_router(stats.router)
app.include_router(pvp.router)


@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/health")
def health():
    return {"status": "ok"}
