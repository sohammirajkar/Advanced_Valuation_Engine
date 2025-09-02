from fastapi import FastAPI
from app.routers import valuation, tasks

app = FastAPI(title="Valuation Engine API")

app.include_router(valuation.router, prefix="/valuation", tags=["valuation"])
app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])

@app.get("/")
def root():
    return {"message": "Valuation Engine API Running"}

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "valuation-engine-api",
        "version": "1.0.0"
    }
