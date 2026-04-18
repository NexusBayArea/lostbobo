from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from backend.app.api.main import api_router
import time

app = FastAPI(title="SimHPC API")

ACTIVITY_FILE = "/tmp/last_active.txt"


@app.middleware("http")
async def update_last_activity(request: Request, call_next):
    with open(ACTIVITY_FILE, "w") as f:
        f.write(str(time.time()))
    response = await call_next(request)
    return response


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
