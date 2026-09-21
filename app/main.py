from fastapi import FastAPI

from app.api.work_orders import router as work_orders_router

app = FastAPI(title="CFP+ Backend Foundation", version="0.1.0-P0")
app.include_router(work_orders_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "technical_integration_verified": "NO",
        "automation_verified": "NO",
    }
