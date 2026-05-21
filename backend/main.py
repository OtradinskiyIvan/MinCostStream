# backend/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .models import AlgorithmRequest
from .algorithm import solve_mcmf

app = FastAPI(title="MCMF Solver API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/solve")
async def solve_graph(req: AlgorithmRequest):
    try:
        result = solve_mcmf(req.model_dump())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка выполнения алгоритма: {str(e)}")

@app.get("/api/health")
async def healthcheck():
    return {
        "status": "ok"
    }

