// ==================== ГЛОБАЛЬНОЕ СОСТОЯНИЕ ====================
const state = {
  nodes: [],           // [{ id: string, x: number, y: number }]
  edges: [],           // [{ id: string, source: string, target: string, cost: number, capacity: number }]
  selectedNode: null,  // id узла для создания ребра
  isDrawingEdge: false,
  nextNodeId: 1        // генератор уникальных ID
};

let algoSteps = null;  // массив шагов из API
let currentStepIndex = -1;

// ==================== УТИЛИТЫ ОТРИСОВКИ ====================
const canvas = document.getElementById('graph-canvas');
const ctx = canvas.getContext('2d');

function drawNode(node, isHighlighted = false) {
  ctx.beginPath();
  ctx.arc(node.x, node.y, 20, 0, Math.PI * 2);
  ctx.fillStyle = isHighlighted ? '#ffcc00' : '#4a90e2';
  ctx.fill();
  ctx.strokeStyle = '#2c3e50';
  ctx.stroke();
  
  ctx.fillStyle = '#fff';
  ctx.font = '14px monospace';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(node.id, node.x, node.y);
}

function drawEdge(edge, flow = null, isHighlighted = false) {
  const src = state.nodes.find(n => n.id === edge.source);
  const tgt = state.nodes.find(n => n.id === edge.target);
  if (!src || !tgt) return;

  // Расчёт контрольных точек для избегания перекрытия узлов
  const dx = tgt.x - src.x, dy = tgt.y - src.y;
  const len = Math.hypot(dx, dy) || 1;
  const ux = dx / len, uy = dy / len;
  
  ctx.beginPath();
  ctx.moveTo(src.x + ux * 20, src.y + uy * 20);
  ctx.lineTo(tgt.x - ux * 20, tgt.y - uy * 20);
  
  ctx.strokeStyle = isHighlighted ? '#e74c3c' : '#95a5a6';
  ctx.lineWidth = isHighlighted ? 3 : 2;
  ctx.stroke();

  // Подпись: стоимость / поток
  ctx.fillStyle = '#2c3e50';
  ctx.font = '12px monospace';
  const midX = (src.x + tgt.x) / 2 + uy * 10;
  const midY = (src.y + tgt.y) / 2 - ux * 10;
  const label = flow !== null ? `c:${edge.cost} f:${flow.toFixed(1)}` : `c:${edge.cost}`;
  ctx.fillText(label, midX, midY);
}

function render() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  
  // Отрисовка рёбер (на заднем плане)
  state.edges.forEach(edge => {
    const stepData = algoSteps?.[currentStepIndex];
    const flow = stepData?.edge_flows?.[`${edge.source}->${edge.target}`];
    const isHigh = stepData?.highlighted_edges?.includes(`${edge.source}->${edge.target}`);
    drawEdge(edge, flow, isHigh);
  });
  
  // Отрисовка узлов (на переднем плане)
  state.nodes.forEach(node => {
    const isHigh = algoSteps?.[currentStepIndex]?.highlighted_nodes?.includes(node.id);
    drawNode(node, isHigh);
  });
}

// ==================== ОБРАБОТЧИКИ СОБЫТИЙ CANVAS ====================
// frontend/app.js — внутри обработчика canvas.addEventListener('click', ...)
canvas.addEventListener('click', (e) => {
  const rect = canvas.getBoundingClientRect();
  // Явное округление до целых пикселей
  const x = Math.round(e.clientX - rect.left);
  const y = Math.round(e.clientY - rect.top);
  
  // ... остальная логика без изменений
  const clickedNode = state.nodes.find(n => Math.hypot(n.x - x, n.y - y) < 20);
  // ...
  
  if (clickedNode) {
    if (state.isDrawingEdge && state.selectedNode) {
      if (state.selectedNode !== clickedNode.id) {
        openEdgeModal(state.selectedNode, clickedNode.id);
      }
      state.isDrawingEdge = false;
      state.selectedNode = null;
      updateControls();
    } else {
      state.selectedNode = clickedNode.id;
      state.isDrawingEdge = true;
      updateControls();
    }
  } else if (!state.isDrawingEdge) {
    // Создание нового узла
    const newNode = {
      id: `N${state.nextNodeId++}`,
      x, y
    };
    state.nodes.push(newNode);
    render();
  }
  render();
});

function openEdgeModal(sourceId, targetId) {
  // Минимальная реализация через prompt (в продакшене — модальное окно)
  const cost = parseFloat(prompt(`Стоимость ребра ${sourceId}→${targetId}:`, '1'));
  const capacity = parseFloat(prompt(`Пропускная способность:`, '10'));
  
  if (!isNaN(cost) && !isNaN(capacity) && cost >= 0 && capacity > 0) {
    state.edges.push({
      id: `${sourceId}->${targetId}`,
      source: sourceId,
      target: targetId,
      cost,
      capacity
    });
    render();
  }
}

// ==================== УПРАВЛЕНИЕ ИНТЕРФЕЙСОМ ====================
function updateControls() {
  document.getElementById('btn-start').disabled = state.nodes.length < 2 || state.edges.length === 0;
  document.getElementById('btn-prev').disabled = currentStepIndex <= 0;
  document.getElementById('btn-next').disabled = 
    !algoSteps || currentStepIndex >= algoSteps.length - 1;
}

function renderStepInfo() {
  const info = document.getElementById('step-info');
  if (!algoSteps || currentStepIndex < 0) {
    info.textContent = 'Ожидание запуска...';
    return;
  }
  const step = algoSteps.steps[currentStepIndex];
  info.innerHTML = `
    <strong>Шаг ${step.step_index}:</strong> ${step.description}<br>
    Поток: ${step.current_flow?.toFixed(2) || 0} | 
    Стоимость: ${step.current_cost?.toFixed(2) || 0}
  `;
}

// ==================== ИНТЕГРАЦИЯ С API ====================
async function startAlgorithm() {
  // Сбор метаданных графа (источник/сток выбираются пользователем)
  const sourceNode = prompt('ID узла-источника:', state.nodes[0]?.id);
  const sinkNode = prompt('ID узла-стока:', state.nodes[state.nodes.length - 1]?.id);
  const requiredFlow = parseFloat(prompt('Требуемый поток:', '5'));
  
  if (!sourceNode || !sinkNode || isNaN(requiredFlow)) {
    alert('Некорректные параметры запуска');
    return;
  }
  
  const payload = {
    nodes: state.nodes,
    edges: state.edges,
    source_node: sourceNode,
    sink_node: sinkNode,
    required_flow: requiredFlow
  };
  
  try {
    document.getElementById('step-info').textContent = 'Вычисление...';
    updateControls();
    
    const response = await fetch('http://localhost:8000/api/solve', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error('Детали ошибки 422:', errorData);
      throw new Error(`HTTP ${response.status}: ${JSON.stringify(errorData.detail || 'Неизвестная ошибка')}`);
    }
    
    algoSteps = await response.json();
    currentStepIndex = 0;
    render();
    renderStepInfo();
    updateControls();
    
  } catch (err) {
    console.error('Ошибка API:', err);
    document.getElementById('step-info').textContent = `Ошибка: ${err.message}`;
  }
}

// ==================== ИНИЦИАЛИЗАЦИЯ ====================
document.getElementById('btn-start').onclick = startAlgorithm;
document.getElementById('btn-prev').onclick = () => {
  if (currentStepIndex > 0) {
    currentStepIndex--;
    render();
    renderStepInfo();
    updateControls();
  }
};
document.getElementById('btn-next').onclick = () => {
  if (algoSteps && currentStepIndex < algoSteps.steps.length - 1) {
    currentStepIndex++;
    render();
    renderStepInfo();
    updateControls();
  }
};

// Первичная отрисовка
render();
updateControls();