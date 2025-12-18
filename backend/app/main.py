from fastapi import FastAPI

app = FastAPI(title="CityPvPPrestige API")


@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/health")
def health():
    return {"status": "ok"}
