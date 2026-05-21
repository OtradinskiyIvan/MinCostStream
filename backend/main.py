from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models import AlgorithmRequest

app = FastAPI(title="MCMF Solver API", version="0.1.0")

# Разрешение CORS для локальной разработки
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
async def healthcheck():
    return {
        "status": "ok"
    }

@app.post("/api/solve")
async def solve_graph(request: AlgorithmRequest):
    # На данном этапе реализуется только приём и валидация данных
    return {
        "status": "validated",
        "nodes_count": len(request.nodes),
        "edges_count": len(request.edges),
        "message": "Контракт данных успешно валидирован. Алгоритм будет реализован на следующем этапе."
    }