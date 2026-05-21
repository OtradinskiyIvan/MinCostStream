from pydantic import BaseModel, Field
from typing import List

class NodeSchema(BaseModel):
    id: str = Field(..., min_length=1, description="Уникальный идентификатор вершины")
    x: int = Field(..., ge=0, description="Координата X на canvas")
    y: int = Field(..., ge=0, description="Координата Y на canvas")

class EdgeSchema(BaseModel):
    source: str = Field(..., description="ID исходной вершины")
    target: str = Field(..., description="ID целевой вершины")
    cost: float = Field(..., description="Стоимость прохождения ребра")
    capacity: float = Field(..., gt=0, description="Пропускная способность ребра")

class AlgorithmRequest(BaseModel):
    nodes: List[NodeSchema]
    edges: List[EdgeSchema]
    source_node: str
    sink_node: str
    required_flow: float = Field(..., gt=0, description="Требуемый поток")