from typing import Dict, List, Any
from collections import defaultdict

class ResidualEdge:
    __slots__ = ('to', 'rev', 'cap', 'flow', 'cost', 'label')
    def __init__(self, to: int, rev: int, cap: float, flow: float, cost: float, label: str = ""):
        self.to = to
        self.rev = rev
        self.cap = cap
        self.flow = flow
        self.cost = cost
        self.label = label  # Уникальный ключ вида "A->B" для отображения

def _build_graph(nodes: List[Dict], edges: List[Dict]) -> tuple:
    node_to_idx = {n["id"]: i for i, n in enumerate(nodes)}
    idx_to_node = {i: n["id"] for i, n in enumerate(nodes)}
    adj = defaultdict(list)

    for e in edges:
        u, v = node_to_idx[e["source"]], node_to_idx[e["target"]]
        label = f"{e['source']}->{e['target']}"
        fwd = ResidualEdge(v, len(adj[v]), e["capacity"], 0.0, e["cost"], label)
        bwd = ResidualEdge(u, len(adj[u]), 0.0, 0.0, -e["cost"], "")
        adj[u].append(fwd)
        adj[v].append(bwd)
    return adj, idx_to_node

def solve_mcmf(req_data: Dict[str, Any]) -> Dict[str, Any]:
    adj, idx_to_node = _build_graph(req_data["nodes"], req_data["edges"])
    src_idx = next(i for i, n in enumerate(req_data["nodes"]) if n["id"] == req_data["source_node"])
    sink_idx = next(i for i, n in enumerate(req_data["nodes"]) if n["id"] == req_data["sink_node"])
    target_flow = req_data["required_flow"]

    total_flow = 0.0
    total_cost = 0.0
    steps = []
    edge_flows = {}

    # Шаг 0: Инициализация
    steps.append({
        "step_index": 0,
        "description": "Инициализация остаточной сети. Нулевой поток, нулевая стоимость.",
        "current_flow": 0.0,
        "current_cost": 0.0,
        "edge_flows": {},
        "highlighted_nodes": [idx_to_node[src_idx], idx_to_node[sink_idx]],
        "highlighted_edges": []
    })

    step_count = 1
    while total_flow < target_flow - 1e-9:
        # Поиск кратчайшего пути в остаточной сети (SPFA/Bellman-Ford)
        dist = [float('inf')] * len(adj)
        parent_node = [-1] * len(adj)
        parent_edge = [None] * len(adj)
        dist[src_idx] = 0.0
        in_queue = [False] * len(adj)
        queue = [src_idx]
        in_queue[src_idx] = True
        q_ptr = 0

        while q_ptr < len(queue):
            u = queue[q_ptr]
            q_ptr += 1
            in_queue[u] = False
            for e in adj[u]:
                if e.cap - e.flow > 1e-9 and dist[e.to] > dist[u] + e.cost + 1e-9:
                    dist[e.to] = dist[u] + e.cost
                    parent_node[e.to] = u
                    parent_edge[e.to] = e
                    if not in_queue[e.to]:
                        queue.append(e.to)
                        in_queue[e.to] = True

        if dist[sink_idx] == float('inf'):
            steps.append({
                "step_index": step_count,
                "description": "Увеличивающий путь не найден. Требуемый поток не может быть достигнут.",
                "current_flow": total_flow,
                "current_cost": total_cost,
                "edge_flows": dict(edge_flows),
                "highlighted_nodes": [],
                "highlighted_edges": []
            })
            break

        # Определение проталкиваемого объёма
        push = target_flow - total_flow
        curr = sink_idx
        while curr != src_idx:
            push = min(push, parent_edge[curr].cap - parent_edge[curr].flow)
            curr = parent_node[curr]

        # Обновление потоков
        curr = sink_idx
        path_nodes = [idx_to_node[src_idx]]
        path_edges = []
        while curr != src_idx:
            e = parent_edge[curr]
            e.flow += push
            adj[e.to][e.rev].flow -= push
            if e.label:
                edge_flows[e.label] = edge_flows.get(e.label, 0.0) + push
                path_edges.append(e.label)
            path_nodes.append(idx_to_node[curr])
            curr = parent_node[curr]

        total_flow += push
        total_cost += push * dist[sink_idx]

        steps.append({
            "step_index": step_count,
            "description": f"Найден увеличивающий путь. Проталкивание потока: {push:.2f}. Инкремент стоимости: {push * dist[sink_idx]:.2f}",
            "current_flow": total_flow,
            "current_cost": total_cost,
            "edge_flows": dict(edge_flows),
            "highlighted_nodes": list(set(path_nodes)),
            "highlighted_edges": path_edges
        })
        step_count += 1

    return {
        "status": "success",
        "min_cost": total_cost,
        "total_flow": total_flow,
        "steps": steps
    }