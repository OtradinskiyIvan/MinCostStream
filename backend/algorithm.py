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


# backend/algorithm.py

def _dijkstra_reduced(adj, src, sink, n, h, idx_to_node, trace, step_counter):
    """Дейкстра с пошаговым трейсингом обработки вершин и релаксации рёбер."""
    INF = float('inf')
    dist = [INF] * n
    prev_v = [-1] * n
    prev_e = [None] * n
    dist[src] = 0.0
    
    heap = [(0.0, src)]
    visited = [False] * n
    
    while heap:
        d_u, u = heapq.heappop(heap)
        if visited[u]:
            continue
        visited[u] = True
        
        # 📝 Шаг: извлечение вершины из очереди
        trace.append({
            "step_index": step_counter[0],
            "type": "explore",
            "description": f"Обработка вершины {idx_to_node[u]} (dist={d_u:.2f})",
            "highlighted_nodes": [idx_to_node[u]],
            "highlighted_edges": [],
            "distances": {idx_to_node[i]: round(dist[i], 2) for i in range(n) if dist[i] < INF},
            "in_queue": sorted([idx_to_node[v] for _, v in heap if not visited[v]]),
            "potentials": {idx_to_node[i]: round(h[i], 2) for i in range(n)},
            "current_flow": None, "current_cost": None, "edge_flows": None
        })
        step_counter[0] += 1
        
        if u == sink:
            break
            
        for e in adj[u]:
            if e.cap - e.flow <= 1e-9:
                continue
            reduced_cost = e.cost + h[u] - h[e.to]
            if dist[e.to] > dist[u] + reduced_cost + 1e-9:
                dist[e.to] = dist[u] + reduced_cost
                prev_v[e.to] = u
                prev_e[e.to] = e
                heapq.heappush(heap, (dist[e.to], e.to))
                
                edge_label = e.label if e.label else f"{idx_to_node[u]}->{idx_to_node[e.to]}"
                # 📝 Шаг: успешная релаксация ребра
                trace.append({
                    "step_index": step_counter[0],
                    "type": "relax",
                    "description": f"Релаксация {idx_to_node[u]}→{idx_to_node[e.to]}: dist обновлён до {dist[e.to]:.2f}",
                    "highlighted_nodes": [idx_to_node[u], idx_to_node[e.to]],
                    "highlighted_edges": [edge_label],
                    "distances": {idx_to_node[i]: round(dist[i], 2) for i in range(n) if dist[i] < INF},
                    "in_queue": sorted([idx_to_node[v] for _, v in heap if not visited[v]]),
                    "potentials": {idx_to_node[i]: round(h[i], 2) for i in range(n)},
                    "current_flow": None, "current_cost": None, "edge_flows": None
                })
                step_counter[0] += 1
                
    return dist, prev_v, prev_e


def solve_mcmf(req_data: Dict[str, Any]) -> Dict[str, Any]:
    adj, idx_to_node, node_to_idx = _build_graph(req_data["nodes"], req_data["edges"])
    
    try:
        src_idx = node_to_idx[req_data["source_node"]]
        sink_idx = node_to_idx[req_data["sink_node"]]
    except KeyError as e:
        return {"status": "error", "error_type": "invalid_node_reference", 
                "message": f"Узел {e} не найден в списке вершин", "steps": [], "min_cost": None, "total_flow": None}
    
    target_flow = float(req_data["required_flow"])
    n_nodes = len(req_data["nodes"])

    # Вырожденные случаи (без изменений)
    if target_flow <= 1e-9:
        return {"status": "success", "min_cost": 0.0, "total_flow": 0.0,
                "steps": [{"step_index": 0, "type": "done", "description": "Требуемый поток равен нулю.",
                           "current_flow": 0.0, "current_cost": 0.0, "edge_flows": {},
                           "highlighted_nodes": [], "highlighted_edges": [], "potentials": {}}]}
    
    if src_idx == sink_idx:
        return {"status": "success", "min_cost": 0.0, "total_flow": target_flow,
                "steps": [{"step_index": 0, "type": "done", 
                           "description": f"Исток и сток совпадают ({idx_to_node[src_idx]}).",
                           "current_flow": target_flow, "current_cost": 0.0, "edge_flows": {},
                           "highlighted_nodes": [idx_to_node[src_idx]], "highlighted_edges": [], "potentials": {}}]}

    potentials = _bellman_ford_init(adj, src_idx, n_nodes)
    if potentials is None:
        return {"status": "error", "error_type": "negative_cycle_in_input",
                "message": "Обнаружен достижимый цикл отрицательной стоимости.", "steps": [], "min_cost": None, "total_flow": None}

    trace = []
    step_counter = [0]
    total_flow = 0.0
    total_cost = 0.0
    edge_flows = {}

    # Шаг 0: Инициализация потенциалов
    trace.append({
        "step_index": step_counter[0], "type": "init",
        "description": "Инициализация: вычислены начальные потенциалы.",
        "current_flow": 0.0, "current_cost": 0.0, "edge_flows": {},
        "highlighted_nodes": [idx_to_node[src_idx], idx_to_node[sink_idx]],
        "highlighted_edges": [],
        "potentials": {idx_to_node[i]: round(p, 2) for i, p in enumerate(potentials)}
    })
    step_counter[0] += 1

    MAX_ITERATIONS = len(req_data["edges"]) * max(1, int(target_flow)) + n_nodes + 5
    iter_count = 1

    while total_flow < target_flow - 1e-9 and iter_count <= MAX_ITERATIONS:
        path_res = _dijkstra_reduced(adj, src_idx, sink_idx, n_nodes, potentials, idx_to_node, trace, step_counter)
        
        if path_res[0] is None or path_res[0][sink_idx] == float('inf'):
            trace.append({
                "step_index": step_counter[0], "type": "finish",
                "description": "Увеличивающий путь не найден. Требуемый поток недостижим.",
                "current_flow": total_flow, "current_cost": total_cost, "edge_flows": dict(edge_flows),
                "highlighted_nodes": [], "highlighted_edges": [], "potentials": {}
            })
            break
            
        dist, prev_v, prev_e = path_res
        
        # Обновление потенциалов
        for i in range(n_nodes):
            if dist[i] < float('inf'):
                potentials[i] += dist[i]
                
        # Определение объёма проталкивания
        push = target_flow - total_flow
        curr = sink_idx
        while curr != src_idx:
            push = min(push, prev_e[curr].cap - prev_e[curr].flow)
            curr = prev_v[curr]
            
        if push < 1e-9:
            break

        # Проталкивание потока
        curr = sink_idx
        path_nodes = [idx_to_node[src_idx]]
        path_edges = []
        path_real_cost = 0.0
        
        while curr != src_idx:
            e = prev_e[curr]
            e.flow += push
            adj[e.to][e.rev].flow -= push
            
            lbl = e.label if e.label else e.orig_label
            if lbl:
                edge_flows[lbl] = edge_flows.get(lbl, 0.0) + push
                path_edges.append(lbl)
                path_real_cost += e.cost
            path_nodes.append(idx_to_node[curr])
            curr = prev_v[curr]
            
        total_flow += push
        total_cost += push * path_real_cost
        
        # 📝 Шаг: завершение аугментации
        trace.append({
            "step_index": step_counter[0], "type": "augment",
            "description": f"Аугментация завершена. Проталкивание: {push:.2f}. Стоимость шага: {push * path_real_cost:.2f}",
            "current_flow": round(total_flow, 2), "current_cost": round(total_cost, 2),
            "edge_flows": {k: round(v, 2) for k, v in edge_flows.items()},
            "highlighted_nodes": list(set(path_nodes)),
            "highlighted_edges": path_edges,
            "potentials": {idx_to_node[i]: round(p, 2) for i, p in enumerate(potentials)}
        })
        step_counter[0] += 1
        iter_count += 1

    return {
        "status": "success" if total_flow >= target_flow - 1e-9 else "success_with_warning",
        "min_cost": round(total_cost, 2),
        "total_flow": round(total_flow, 2),
        "steps": trace
    }