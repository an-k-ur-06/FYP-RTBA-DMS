import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.app.core.config import settings
from backend.app.core.redis_client import init_redis
from backend.app.websocket.manager import ws_manager

from backend.app.api.hospitals import router as hospitals_router
from backend.app.api.doctors import router as doctors_router
from backend.app.api.patients import router as patients_router
from backend.app.api.donors import router as donors_router
from backend.app.api.inventory import router as inventory_router
from backend.app.api.blood_requests import router as blood_requests_router
from backend.app.api.donations import router as donations_router
from backend.app.api.matching import router as matching_router
from backend.app.api.dashboard import router as dashboard_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    await init_redis()
    yield
    # Shutdown actions

app = FastAPI(
    title="Real-Time Blood Availability and Intelligent Donor Matching System",
    description="Enterprise Healthcare Operations Platform with Random Forest & Mamdani Fuzzy Logic Prioritization",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(hospitals_router)
app.include_router(doctors_router)
app.include_router(patients_router)
app.include_router(donors_router)
app.include_router(inventory_router)
app.include_router(blood_requests_router)
app.include_router(donations_router)
app.include_router(matching_router)
app.include_router(dashboard_router)

# WebSocket Real-Time Event Stream Endpoint
@app.websocket("/ws/events")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and listen for client messages if any
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        ws_manager.disconnect(websocket)

# mount frontend staticts
frontend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

@app.get("/")
async def serve_index():
    index_file = os.path.join(frontend_path, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Real-Time Blood Availability System API operational"}
