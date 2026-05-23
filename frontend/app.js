// ==================== ГЛОБАЛЬНОЕ СОСТОЯНИЕ ====================
const state = {
  nodes: [],
  edges: [],
  selectedNode: null,
  isDrawingEdge: false,
  nextNodeId: 1,
  isDeleteMode: false
};

let algoSteps = null;
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
  
  // === ОПЦИОНАЛЬНО: отображение потенциалов ===
  const currentStepData = algoSteps?.steps?.[currentStepIndex];
  if (currentStepData?.potentials?.[node.id] !== undefined) {
    ctx.fillStyle = '#7f8c8d';
    ctx.font = '10px monospace';
    ctx.textAlign = 'center';
    ctx.fillText(`h=${currentStepData.potentials[node.id]}`, node.x, node.y + 18);
  }
}

function drawEdge(edge, flow = null, isHighlighted = false) {
  const src = state.nodes.find(n => n.id === edge.source);
  const tgt = state.nodes.find(n => n.id === edge.target);
  if (!src || !tgt) return;

  const dx = tgt.x - src.x;
  const dy = tgt.y - src.y;
  const len = Math.hypot(dx, dy) || 1;
  const ux = dx / len;
  const uy = dy / len;

  // Точки начала и конца линии (с отступом 20px от центра узлов)
  const x1 = src.x + ux * 20;
  const y1 = src.y + uy * 20;
  const x2 = tgt.x - ux * 20;
  const y2 = tgt.y - uy * 20;

  // Основная линия
  ctx.beginPath();
  ctx.moveTo(x1, y1);
  ctx.lineTo(x2, y2);
  ctx.strokeStyle = isHighlighted ? '#e74c3c' : '#95a5a6';
  ctx.lineWidth = isHighlighted ? 3 : 2;
  ctx.stroke();

  // Стрелка
  const angle = Math.atan2(dy, dx);
  const arrowLen = 12;
  const arrowAngle = Math.PI / 6; // 30 градусов

  ctx.beginPath();
  ctx.moveTo(x2, y2);
  ctx.lineTo(
    x2 - arrowLen * Math.cos(angle - arrowAngle),
    y2 - arrowLen * Math.sin(angle - arrowAngle)
  );
  ctx.moveTo(x2, y2);
  ctx.lineTo(
    x2 - arrowLen * Math.cos(angle + arrowAngle),
    y2 - arrowLen * Math.sin(angle + arrowAngle)
  );
  ctx.strokeStyle = isHighlighted ? '#e74c3c' : '#95a5a6';
  ctx.lineWidth = isHighlighted ? 3 : 2;
  ctx.stroke();

  // Подпись (смещена перпендикулярно линии)
  ctx.fillStyle = '#2c3e50';
  ctx.font = '12px monospace';
  const midX = (src.x + tgt.x) / 2 + uy * 10;
  const midY = (src.y + tgt.y) / 2 - ux * 10;
  const label = flow !== null ? `c:${edge.cost} f:${flow.toFixed(1)}` : `c:${edge.cost}`;
  ctx.fillText(label, midX, midY);
}

function render() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  
  const currentStepData = algoSteps?.steps?.[currentStepIndex];

  state.edges.forEach(edge => {
    const edgeKey = `${edge.source}->${edge.target}`;
    const flow = currentStepData?.edge_flows?.[edgeKey] ?? null;
    const isHigh = currentStepData?.highlighted_edges?.includes(edgeKey) ?? false;
    drawEdge(edge, flow, isHigh);
  });

  state.nodes.forEach(node => {
    const isHigh = currentStepData?.highlighted_nodes?.includes(node.id) ?? false;
    drawNode(node, isHigh);
  });
}

// ==================== ПОИСК РЕБРА ПОД КУРСОРОМ ====================
function findEdgeAtPosition(x, y, threshold = 10) {
  // Перебираем рёбра в обратном порядке — чтобы выбирать верхние (нарисованные позже)
  for (let i = state.edges.length - 1; i >= 0; i--) {
    const edge = state.edges[i];
    const src = state.nodes.find(n => n.id === edge.source);
    const tgt = state.nodes.find(n => n.id === edge.target);
    if (!src || !tgt) continue;

    // Вектор ребра
    const dx = tgt.x - src.x;
    const dy = tgt.y - src.y;
    const len = Math.hypot(dx, dy);
    if (len < 1) continue;

    // Проекция точки (x,y) на отрезок [src, tgt]
    const t = Math.max(0, Math.min(1, ((x - src.x) * dx + (y - src.y) * dy) / (len * len)));
    const projX = src.x + t * dx;
    const projY = src.y + t * dy;
    
    // Расстояние от точки до проекции
    const dist = Math.hypot(x - projX, y - projY);
    
    if (dist <= threshold) {
      return edge; // Найдено ребро под курсором
    }
  }
  return null;
}

// ==================== ФУНКЦИЯ ИНВАЛИДАЦИИ РЕЗУЛЬТАТОВ ====================
function invalidateAlgorithmResults() {
  algoSteps = null;
  currentStepIndex = -1;
  document.getElementById('step-info').textContent = 'Граф изменён. Требуется повторный запуск.';
  updateControls();
}

// ==================== ОБРАБОТЧИКИ СОБЫТИЙ CANVAS ====================
canvas.addEventListener('click', (e) => {
  const rect = canvas.getBoundingClientRect();
  const x = Math.round(e.clientX - rect.left);
  const y = Math.round(e.clientY - rect.top);
  
  // === РЕЖИМ УДАЛЕНИЯ ===
  if (state.isDeleteMode) {
    // 1. Пробуем удалить ребро (приоритет — тонкий элемент)
    const clickedEdge = findEdgeAtPosition(x, y);
    if (clickedEdge) {
      state.edges = state.edges.filter(ed => 
        !(ed.source === clickedEdge.source && ed.target === clickedEdge.target)
      );
      console.log('🗑️ Удалено ребро:', `${clickedEdge.source}->${clickedEdge.target}`);
      invalidateAlgorithmResults();
      render();
      return; // Завершаем обработку
    }
    
    // 2. Если не ребро — пробуем удалить узел
    const clickedNode = state.nodes.find(n => Math.hypot(n.x - x, n.y - y) < 20);
    if (clickedNode) {
      const deletedId = clickedNode.id;
      // Удаляем узел
      state.nodes = state.nodes.filter(n => n.id !== deletedId);
      // Каскадно удаляем все инцидентные рёбра
      const beforeCount = state.edges.length;
      state.edges = state.edges.filter(ed => 
        ed.source !== deletedId && ed.target !== deletedId
      );
      console.log(`🗑️ Удален узел ${deletedId} и ${beforeCount - state.edges.length} связанных рёбер`);
      
      // Сбрасываем выбор, если удалили выбранный узел
      if (state.selectedNode === deletedId) {
        state.selectedNode = null;
        state.isDrawingEdge = false;
      }
      
      invalidateAlgorithmResults();
      render();
      return;
    }
    
    // Клик в пустоту в режиме удаления — ничего не делаем
    return;
  }
  
  // === ОБЫЧНЫЙ РЕЖИМ (добавление) ===
  const clickedNode = state.nodes.find(n => Math.hypot(n.x - x, n.y - y) < 20);
  
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
    const newNode = {
      id: `N${state.nextNodeId++}`,
      x, y
    };
    state.nodes.push(newNode);
    invalidateAlgorithmResults();
    render();
  }
  render();
});

function openEdgeModal(sourceId, targetId) {
  // 1. Сбор данных с дефолтными значениями
  const costInput = prompt(`Стоимость ребра ${sourceId}→${targetId}:`, '1');
  const capacityInput = prompt(`Пропускная способность:`, '10');
  
  // 2. Строгая валидация
  const cost = parseFloat(costInput);
  const capacity = parseFloat(capacityInput);
  
  const isValid = !isNaN(cost) && !isNaN(capacity) && isFinite(cost) && isFinite(capacity) && capacity > 0;
  
  if (!isValid) {
    alert('Ошибка: введите корректные числовые значения. Пропускная способность должна быть > 0.');
    return; // Прерываем выполнение, если ввод некорректен
  }
  
  // 3. Создание "чистого" объекта ребра (без поля id, чтобы не конфликтовать с Pydantic)
  const newEdge = {
    source: sourceId,
    target: targetId,
    cost: cost,
    capacity: capacity
  };
  
  // 4. Отладочный лог
  console.log('➕ Добавление ребра:', newEdge);
  console.log('📊 Текущее состояние рёбер до:', state.edges.map(e => `${e.source}->${e.target}`));
  
  state.edges.push(newEdge);
  
  console.log('📊 Текущее состояние рёбер после:', state.edges.map(e => `${e.source}->${e.target}`));
  
  // 5. Инвалидация и перерисовка
  invalidateAlgorithmResults();
  render();
}

// ==================== УПРАВЛЕНИЕ ИНТЕРФЕЙСОМ ====================
const btnDeleteMode = document.getElementById('btn-delete-mode');

function updateControls() {
  const hasGraph = state.nodes.length >= 2 && state.edges.length > 0;
  
  // Кнопка Start: неактивна в режиме удаления или при пустом графе
  document.getElementById('btn-start').disabled = !hasGraph || state.isDeleteMode;
  
  // Кнопки навигации: неактивны в режиме удаления или без результатов
  document.getElementById('btn-prev').disabled = 
    state.isDeleteMode || !algoSteps || currentStepIndex <= 0;
  
  const totalSteps = algoSteps?.steps?.length || 0;
  document.getElementById('btn-next').disabled = 
    state.isDeleteMode || !algoSteps || currentStepIndex >= totalSteps - 1;
  
  // Текст кнопки удаления
  if (btnDeleteMode) {
    btnDeleteMode.textContent = state.isDeleteMode ? '✅ Выход из удаления' : '🗑️ Удаление';
  }
}

function renderStepInfo() {
  const info = document.getElementById('step-info');
  
  // Если в режиме удаления — показываем подсказку
  if (state.isDeleteMode) {
    info.innerHTML = '<div style="color:#e74c3c; font-weight:bold;">🗑️ РЕЖИМ УДАЛЕНИЯ: клик по элементу для удаления</div>';
    return;
  }
  
  if (!algoSteps || currentStepIndex < 0) {
    info.textContent = 'Ожидание запуска...';
    return;
  }

  const step = algoSteps.steps[currentStepIndex];
  const totalSteps = algoSteps.steps.length;
  const isFinal = currentStepIndex === totalSteps - 1;

  info.innerHTML = `
    <strong>Шаг ${step.step_index} / ${totalSteps - 1}:</strong> ${step.description}<br>
    <div style="margin-top:4px; color: #2c3e50;">
      Поток: ${step.current_flow?.toFixed(2) || 0} | 
      Стоимость: ${step.current_cost?.toFixed(2) || 0}
    </div>
    ${isFinal ? '<div style="margin-top:6px; color:#27ae60; font-weight:bold;">✅ Алгоритм завершён. Результат найден.</div>' : ''}
  `;
}

// ==================== ПЕРЕКЛЮЧЕНИЕ РЕЖИМА УДАЛЕНИЯ ====================
if (btnDeleteMode) {
  btnDeleteMode.onclick = () => {
    state.isDeleteMode = !state.isDeleteMode;
    
    // Визуальное переключение кнопки
    btnDeleteMode.classList.toggle('active', state.isDeleteMode);
    
    // Добавляем/убираем класс на body для смены курсора
    document.body.classList.toggle('delete-mode', state.isDeleteMode);
    
    // Сброс промежуточных состояний при входе в режим удаления
    if (state.isDeleteMode) {
      state.selectedNode = null;
      state.isDrawingEdge = false;
    } else {
      // Выход из режима удаления — обновляем информацию
      if (algoSteps) {
        renderStepInfo();
      } else {
        document.getElementById('step-info').textContent = 'Ожидание запуска...';
      }
    }
    
    updateControls();
    render();
  };
}

// ==================== ИНТЕГРАЦИЯ С API ====================
async function startAlgorithm() {
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
    
    // Получаем результат
    const result = await response.json();
    
    // === ОБНОВЛЕННАЯ ОБРАБОТКА ОШИБОК АЛГОРИТМА ===
    if (result.status === "error") {
      let message = result.message || "Неизвестная ошибка алгоритма";
      let color = "#e74c3c";
      
      if (result.error_type === "negative_cycle_in_input") {
        message = "⚠️ Обнаружен цикл отрицательной стоимости.\n" + message;
      } else if (result.error_type === "iteration_limit_exceeded") {
        message = "⚠️ Превышено число итераций.\n" + message;
        color = "#e67e22";
      }
      
      document.getElementById('step-info').innerHTML = 
        `<span style="color:${color}; white-space: pre-line;">${message}</span>`;
      
      // Отобразить шаги, если они есть (частичный результат)
      if (result.steps?.length > 0) {
        algoSteps = result;
        currentStepIndex = 0;
        render();
        renderStepInfo();
      }
      updateControls();
      return;
    }
    
    // === УСПЕШНОЕ ВЫПОЛНЕНИЕ ===
    algoSteps = result;
    currentStepIndex = 0;
    render();
    renderStepInfo();
    updateControls();
    
  } catch (err) {
    console.error('Ошибка API:', err);
    document.getElementById('step-info').textContent = `Ошибка: ${err.message}`;
    alert(`Ошибка соединения с сервером: ${err.message}`);
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

// Инициализация режима удаления
if (btnDeleteMode) {
  state.isDeleteMode = false;
  btnDeleteMode.classList.remove('active');
  document.body.classList.remove('delete-mode');
}

render();
updateControls();