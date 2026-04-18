from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.app.api.main import api_router

app = FastAPI(title="SimHPC API")

origins = [
    "https://simhpc-70zmkqotk-nexusbayareas-projects.vercel.app",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def root():
    return {"message": "SimHPC A40 API is online", "status": "secure"}
