# backend/algorithm.py
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
import heapq

class ResidualEdge:
    """Ребро остаточной сети с обратным указателем для быстрого обновления потока."""
    __slots__ = ('to', 'rev', 'cap', 'flow', 'cost', 'label', 'orig_label')
    def __init__(self, to: int, rev: int, cap: float, flow: float, cost: float, label: str = "", orig_label: str = ""):
        self.to = to                  # Индекс целевой вершины
        self.rev = rev                # Индекс обратного ребра в adj[to]
        self.cap = cap                # Пропускная способность
        self.flow = flow              # Текущий поток
        self.cost = cost              # Стоимость прохождения (может быть отрицательной)
        self.label = label            # Уникальный ключ для отображения "A->B"
        self.orig_label = orig_label  # Оригинальная метка (для обратных рёбер)


def _build_graph(nodes: List[Dict], edges: List[Dict]) -> Tuple[dict, dict, dict]:
    """
    Построение остаточной сети из входных данных.
    Возвращает: (adjacency_list, idx_to_node, node_to_idx)
    """
    node_to_idx = {n["id"]: i for i, n in enumerate(nodes)}
    idx_to_node = {i: n["id"] for i, n in enumerate(nodes)}
    adj = defaultdict(list)

    for e in edges:
        u = node_to_idx[e["source"]]
        v = node_to_idx[e["target"]]
        label = f"{e['source']}->{e['target']}"
        
        # Прямое ребро (используется в решении)
        fwd = ResidualEdge(
            to=v, rev=len(adj[v]), 
            cap=float(e["capacity"]), flow=0.0, 
            cost=float(e["cost"]), 
            label=label, orig_label=label
        )
        # Обратное ребро (для остаточной сети, не отображается)
        bwd = ResidualEdge(
            to=u, rev=len(adj[u]), 
            cap=0.0, flow=0.0, 
            cost=-float(e["cost"]), 
            label="", orig_label=label
        )
        adj[u].append(fwd)
        adj[v].append(bwd)
    
    return dict(adj), idx_to_node, node_to_idx


def _bellman_ford_init(adj: dict, src: int, n: int) -> Optional[List[float]]:
    """
    Инициализация потенциалов через Беллмана-Форда.
    Возвращает массив потенциалов h[] или None, если обнаружен отрицательный цикл.
    """
    h = [0.0] * n  # Начальные потенциалы
    # Релаксация всех рёбер (V-1) раз
    for _ in range(n - 1):
        updated = False
        for u in adj:
            for e in adj[u]:
                if e.cap - e.flow > 1e-9 and h[e.to] > h[u] + e.cost + 1e-9:
                    h[e.to] = h[u] + e.cost
                    updated = True
        if not updated:
            break
    
    # Проверка на отрицательный цикл: если ещё возможна релаксация — цикл есть
    for u in adj:
        for e in adj[u]:
            if e.cap - e.flow > 1e-9 and h[e.to] > h[u] + e.cost + 1e-6:
                return None  # Отрицательный цикл обнаружен
    return h


def _dijkstra_reduced(adj: dict, src: int, sink: int, n: int, h: List[float]) -> Optional[Tuple[List[float], List[int], List[Any]]]:
    """
    Дейкстра на редуцированных весах: cost'(u,v) = cost(u,v) + h[u] - h[v].
    Возвращает (dist, parent_node, parent_edge) или None, если путь не найден.
    """
    dist = [float('inf')] * n
    parent_node = [-1] * n
    parent_edge = [None] * n
    dist[src] = 0.0
    
    # Куча: (distance, node_index)
    heap = [(0.0, src)]
    visited = [False] * n
    
    while heap:
        d_u, u = heapq.heappop(heap)
        if visited[u]:
            continue
        visited[u] = True
        
        if u == sink:
            break
            
        for e in adj[u]:
            if e.cap - e.flow <= 1e-9:
                continue
            # Редуцированная стоимость (всегда неотрицательна при корректных h)
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
    """
    Основной алгоритм: поток минимальной стоимости с потенциалами.
    Возвращает структуру с шагами для визуализации или ошибку при обнаружении цикла.
    """
    adj, idx_to_node, node_to_idx = _build_graph(req_data["nodes"], req_data["edges"])
    
    src_idx = node_to_idx[req_data["source_node"]]
    sink_idx = node_to_idx[req_data["sink_node"]]
    target_flow = float(req_data["required_flow"])
    n_nodes = len(req_data["nodes"])

    # === Инициализация потенциалов ===
    potentials = _bellman_ford_init(adj, src_idx, n_nodes)
    if potentials is None:
        return {
            "status": "error",
            "error_type": "negative_cycle_in_input",
            "message": "Граф содержит достижимый цикл отрицательной стоимости. Задача не имеет конечного минимума.",
            "steps": [],
            "min_cost": None,
            "total_flow": None
        }

    total_flow = 0.0
    total_cost = 0.0
    steps = []
    edge_flows = {}  # { "A->B": flow_value }

    # Шаг 0: Инициализация
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
                "message": "Превышено максимальное число итераций. Возможна численная нестабильность.",
                "steps": steps,
                "min_cost": total_cost,
                "total_flow": total_flow
            }

        # Поиск кратчайшего пути с редуцированными весами
        path_result = _dijkstra_reduced(adj, src_idx, sink_idx, n_nodes, potentials)
        
        if path_result is None:
            # Путь не найден: проверяем достижимость стока
            visited = set()
            stack = [src_idx]
            while stack:
                u = stack.pop()
                if u in visited:
                    continue
                visited.add(u)
                for e in adj[u]:
                    if e.cap - e.flow > 1e-9 and e.to not in visited:
                        stack.append(e.to)
            
            if sink_idx not in visited:
                steps.append({
                    "step_index": step_count,
                    "description": "Увеличивающий путь не найден. Требуемый поток недостижим.",
                    "current_flow": total_flow,
                    "current_cost": total_cost,
                    "edge_flows": dict(edge_flows),
                    "highlighted_nodes": [],
                    "highlighted_edges": []
                })
                break
            else:
                # Сток достижим, но Дейкстра не нашла путь → ошибка в потенциалах (не должно произойти)
                return {
                    "status": "error",
                    "error_type": "algorithm_internal_error",
                    "message": "Внутренняя ошибка: сток достижим, но путь не найден при неотрицательных редуцированных весах.",
                    "steps": steps,
                    "min_cost": total_cost,
                    "total_flow": total_flow
                }
        
        dist, parent_node, parent_edge = path_result

        # === Обновление потенциалов: h[v] += dist[v] ===
        for i in range(n_nodes):
            if dist[i] < float('inf'):
                potentials[i] += dist[i]

        # === Определение объёма проталкиваемого потока ===
        push = target_flow - total_flow
        curr = sink_idx
        while curr != src_idx:
            e = parent_edge[curr]
            residual = e.cap - e.flow
            push = min(push, residual)
            curr = parent_node[curr]
        
        if push < 1e-9:
            break  # Нечего проталкивать

        # === Проталкивание потока и обновление остаточной сети ===
        curr = sink_idx
        path_nodes = [idx_to_node[src_idx]]
        path_edges = []
        
        while curr != src_idx:
            e = parent_edge[curr]
            # Обновление прямого ребра
            e.flow += push
            # Обновление обратного ребра
            rev_e = adj[e.to][e.rev]
            rev_e.flow -= push
            
            # Запись потока только для оригинальных рёбер
            if e.label:
                edge_flows[e.label] = edge_flows.get(e.label, 0.0) + push
                path_edges.append(e.label)
            elif e.orig_label and rev_e.label:
                # Обратное ребро: уменьшаем поток в оригинальном направлении
                edge_flows[e.orig_label] = edge_flows.get(e.orig_label, 0.0) - push
                path_edges.append(e.orig_label)
                
            path_nodes.append(idx_to_node[curr])
            curr = parent_node[curr]

        # === Обновление агрегированных метрик ===
        # Реальная стоимость = сумма (поток * исходная стоимость) по пути
        path_real_cost = 0.0
        curr = sink_idx
        while curr != src_idx:
            e = parent_edge[curr]
            if e.label:  # Только оригинальные рёбра
                path_real_cost += e.cost
            curr = parent_node[curr]
        
        total_flow += push
        total_cost += push * path_real_cost

        steps.append({
            "step_index": step_count,
            "description": f"Путь найден. Проталкивание: {push:.2f}. Стоимость шага: {push * path_real_cost:.2f}",
            "current_flow": total_flow,
            "current_cost": total_cost,
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