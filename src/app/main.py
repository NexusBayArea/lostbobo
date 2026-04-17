from fastapi import FastAPI
from src.app.api.main import api_router

app = FastAPI(title="SimHPC API")

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def root():
    return {"message": "SimHPC API is online"}
