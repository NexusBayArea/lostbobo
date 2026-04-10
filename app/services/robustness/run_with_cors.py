from fastapi.middleware.cors import CORSMiddleware
import importlib
import uvicorn

# Import existing app from api.py
api_mod = importlib.import_module("api")
app = getattr(api_mod, "app", None)
if app is None:
    raise RuntimeError("`api.py` does not define an `app` FastAPI instance")

# Add CORS middleware allowing all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8888)
