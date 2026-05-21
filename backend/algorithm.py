# backend/algorithm.py
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
import heapq

class ResidualEdge:
    __slots__ = ('to', 'rev', 'cap', 'flow', 'cost', 'label', 'orig_label')
    def __init__(self, to: int, rev: int, cap: float, flow: float, cost: float, label: str = "", orig_label: str = ""):
        self.to = to
        self.rev = rev
        self.cap = cap
        self.flow = flow
        self.cost = cost
        self.label = label
        self.orig_label = orig_label


def _build_graph(nodes: List[Dict], edges: List[Dict]) -> Tuple[dict, dict, dict]:
    node_to_idx = {n["id"]: i for i, n in enumerate(nodes)}
    idx_to_node = {i: n["id"] for i, n in enumerate(nodes)}
    adj = defaultdict(list)

    for e in edges:
        u = node_to_idx[e["source"]]
        v = node_to_idx[e["target"]]
        label = f"{e['source']}->{e['target']}"
        
        fwd = ResidualEdge(v, len(adj[v]), float(e["capacity"]), 0.0, float(e["cost"]), label, label)
        bwd = ResidualEdge(u, len(adj[u]), 0.0, 0.0, -float(e["cost"]), "", label)
        adj[u].append(fwd)
        adj[v].append(bwd)
    
    return dict(adj), idx_to_node, node_to_idx


def _bellman_ford_init(adj: dict, src: int, n: int) -> Optional[List[float]]:
    h = [float('inf')] * n
    h[src] = 0.0
    
    for _ in range(n - 1):
        updated = False
        for u in range(n):
            if h[u] == float('inf') or u not in adj:
                continue
            for e in adj[u]:
                if e.cap - e.flow > 1e-9 and h[e.to] > h[u] + e.cost + 1e-9:
                    h[e.to] = h[u] + e.cost
                    updated = True
        if not updated:
            break
    
    # Детекция циклов ТОЛЬКО в достижимой компоненте
    for u in range(n):
        if h[u] == float('inf') or u not in adj:
            continue
        for e in adj[u]:
            if e.cap - e.flow > 1e-9 and h[e.to] > h[u] + e.cost + 1e-6:
                return None
    
    for i in range(n):
        if h[i] == float('inf'):
            h[i] = 0.0
    return h


def _dijkstra_reduced(adj: dict, src: int, sink: int, n: int, h: List[float]) -> Optional[Tuple[List[float], List[int], List[Any]]]:
    dist = [float('inf')] * n
    parent_node = [-1] * n
    parent_edge = [None] * n
    dist[src] = 0.0
    
    heap = [(0.0, src)]
    visited = [False] * n
    
    while heap:
        d_u, u = heapq.heappop(heap)
        if visited[u]:
            continue
        visited[u] = True
        if u == sink:
            break
        if u not in adj:
            continue
        for e in adj[u]:
            if e.cap - e.flow <= 1e-9:
                continue
            reduced_cost = e.cost + h[u] - h[e.to]
            if dist[e.to] > dist[u] + reduced_cost + 1e-9:
                dist[e.to] = dist[u] + reduced_cost
                parent_node[e.to] = u
                parent_edge[e.to] = e
                heapq.heappush(heap, (dist[e.to], e.to))
    
    if dist[sink] == float('inf'):
        return None
    return dist, parent_node, parent_edge


def solve_mcmf(req_data: Dict[str, Any]) -> Dict[str, Any]:
    adj, idx_to_node, node_to_idx = _build_graph(req_data["nodes"], req_data["edges"])
    
    try:
        src_idx = node_to_idx[req_data["source_node"]]
        sink_idx = node_to_idx[req_data["sink_node"]]
    except KeyError as e:
        return {
            "status": "error",
            "error_type": "invalid_node_reference",
            "message": f"Узел {e} не найден в списке вершин",
            "steps": [],
            "min_cost": None,
            "total_flow": None
        }
    
    target_flow = float(req_data["required_flow"])
    n_nodes = len(req_data["nodes"])

    # Вырожденные случаи
    if target_flow <= 1e-9:
        return {
            "status": "success",
            "min_cost": 0.0,
            "total_flow": 0.0,
            "steps": [{
                "step_index": 0,
                "description": "Требуемый поток равен нулю. Решение тривиально.",
                "current_flow": 0.0,
                "current_cost": 0.0,
                "edge_flows": {},
                "highlighted_nodes": [idx_to_node.get(src_idx, ""), idx_to_node.get(sink_idx, "")],
                "highlighted_edges": []
            }]
        }
    
    if src_idx == sink_idx:
        return {
            "status": "success",
            "min_cost": 0.0,
            "total_flow": target_flow,
            "steps": [{
                "step_index": 0,
                "description": f"Исток и сток совпадают ({idx_to_node[src_idx]}). Поток доставлен с нулевой стоимостью.",
                "current_flow": target_flow,
                "current_cost": 0.0,
                "edge_flows": {},
                "highlighted_nodes": [idx_to_node[src_idx]],
                "highlighted_edges": []
            }]
        }

    potentials = _bellman_ford_init(adj, src_idx, n_nodes)
    if potentials is None:
        return {
            "status": "error",
            "error_type": "negative_cycle_in_input",
            "message": "Граф содержит достижимый из истока цикл отрицательной стоимости. Задача не имеет конечного минимума.",
            "steps": [],
            "min_cost": None,
            "total_flow": None
        }

    total_flow = 0.0
    total_cost = 0.0
    steps = []
    edge_flows = {}

    steps.append({
        "step_index": 0,
        "description": "Инициализация: вычислены начальные потенциалы. Нулевой поток, нулевая стоимость.",
        "current_flow": 0.0,
        "current_cost": 0.0,
        "edge_flows": {},
        "highlighted_nodes": [idx_to_node[src_idx], idx_to_node[sink_idx]],
        "highlighted_edges": [],
        "potentials": {idx_to_node[i]: round(p, 2) for i, p in enumerate(potentials)}
    })

    step_count = 1
    MAX_ITERATIONS = len(req_data["edges"]) * max(1, int(target_flow)) + n_nodes + 5

    while total_flow < target_flow - 1e-9:
        if step_count > MAX_ITERATIONS:
            return {
                "status": "error",
                "error_type": "iteration_limit_exceeded",
                "message": "Превышено максимальное число итераций.",
                "steps": steps,
                "min_cost": round(total_cost, 2),
                "total_flow": round(total_flow, 2)
            }

        path_result = _dijkstra_reduced(adj, src_idx, sink_idx, n_nodes, potentials)
        
        if path_result is None:
            # Проверка достижимости стока
            visited = set()
            stack = [src_idx]
            while stack:
                u = stack.pop()
                if u in visited or u not in adj:
                    continue
                visited.add(u)
                for e in adj[u]:
                    if e.cap - e.flow > 1e-9 and e.to not in visited:
                        stack.append(e.to)
            
            if sink_idx not in visited:
                status_msg = "Увеличивающий путь не найден. Требуемый поток недостижим."
                if total_flow > 1e-9:
                    status_msg += f" Доставлено {total_flow:.2f} из {target_flow:.2f}."
                
                steps.append({
                    "step_index": step_count,
                    "description": status_msg,
                    "current_flow": total_flow,
                    "current_cost": total_cost,
                    "edge_flows": dict(edge_flows),
                    "highlighted_nodes": [],
                    "highlighted_edges": []
                })
                return {
                    "status": "success",
                    "min_cost": round(total_cost, 2),
                    "total_flow": round(total_flow, 2),
                    "steps": steps,
                    "warning": "Требуемый поток недостижим при заданных ограничениях"
                }
            else:
                return {
                    "status": "error",
                    "error_type": "algorithm_internal_error",
                    "message": "Внутренняя ошибка: сток достижим, но путь не найден.",
                    "steps": steps,
                    "min_cost": round(total_cost, 2),
                    "total_flow": round(total_flow, 2)
                }
        
        dist, parent_node, parent_edge = path_result

        for i in range(n_nodes):
            if dist[i] < float('inf'):
                potentials[i] += dist[i]

        push = target_flow - total_flow
        curr = sink_idx
        while curr != src_idx:
            e = parent_edge[curr]
            push = min(push, e.cap - e.flow)
            curr = parent_node[curr]
        
        if push < 1e-9:
            break

        curr = sink_idx
        path_nodes = [idx_to_node[src_idx]]
        path_edges = []
        path_real_cost = 0.0
        
        while curr != src_idx:
            e = parent_edge[curr]
            e.flow += push
            rev_e = adj[e.to][e.rev]
            rev_e.flow -= push
            
            if e.label:
                edge_flows[e.label] = edge_flows.get(e.label, 0.0) + push
                path_edges.append(e.label)
                path_real_cost += e.cost
            elif e.orig_label:
                edge_flows[e.orig_label] = edge_flows.get(e.orig_label, 0.0) - push
                path_edges.append(e.orig_label)
                path_real_cost += e.cost
                
            path_nodes.append(idx_to_node[curr])
            curr = parent_node[curr]

        total_flow += push
        total_cost += push * path_real_cost

        steps.append({
            "step_index": step_count,
            "description": f"Путь найден. Проталкивание: {push:.2f}. Стоимость шага: {push * path_real_cost:.2f}",
            "current_flow": round(total_flow, 2),
            "current_cost": round(total_cost, 2),
            "edge_flows": {k: round(v, 2) for k, v in edge_flows.items()},
            "highlighted_nodes": list(set(path_nodes)),
            "highlighted_edges": path_edges,
            "potentials": {idx_to_node[i]: round(p, 2) for i, p in enumerate(potentials)}
        })
        step_count += 1

    return {
        "status": "success",
        "min_cost": round(total_cost, 2),
        "total_flow": round(total_flow, 2),
        "steps": steps
    }