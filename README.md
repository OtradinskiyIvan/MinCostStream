# Min-Cost Flow Visualizer

Веб-приложение для интерактивного построения графов и пошаговой визуализации работы алгоритма поиска **потока минимальной стоимости** (Minimum Cost Maximum Flow, MCMF).

![Демонстрация работы](docs/demo.gif) *(заглушка для скриншота)*

---

## 📋 Оглавление

- [О проекте](#-о-проекте)
- [Возможности](#-возможности)
- [Архитектура](#-архитектура)
- [Технологический стек](#-технологический-стек)
- [Быстрый старт](#-быстрый-старт)
- [API Reference](#-api-reference)
- [Формат данных](#-формат-данных)
- [Примеры использования](#-примеры-использования)
- [Тестирование](#-тестирование)
- [Структура проекта](#-структура-проекта)
- [Обработка ошибок](#-обработка-ошибок)
- [Расширение функционала](#-расширение-функционала)
- [Лицензия](#-лицензия)

---

## 🔍 О проекте

Данное приложение реализует классическую задачу теории графов: найти способ транспортировать заданный объём потока от источника к стоку через сеть с ограниченной пропускной способностью рёбер, минимизируя суммарную стоимость транспортировки.

**Ключевая особенность:** алгоритм работает в пошаговом режиме с генерацией детализированного трейса, что позволяет наглядно изучать процесс нахождения оптимального решения.

### Области применения
- 🎓 Образовательные цели: изучение алгоритмов потоков в сетях
- 🔬 Исследования: прототипирование транспортных и коммуникационных сетей
- 🛠️ Инженерия: визуальная отладка моделей распределения ресурсов

---

## ✨ Возможности

### 🎨 Frontend (Интерфейс)
| Функция | Описание |
|---------|----------|
| **Интерактивный редактор** | Добавление вершин кликом по холсту, создание рёбер через выделение пары узлов |
| **Режим удаления** | Кнопка 🗑️ для удаления вершин и рёбер (с каскадным удалением инцидентных рёбер) |
| **Визуализация ориентации** | Стрелки на рёбрах показывают направление потока |
| **Пошаговое управление** | Кнопки `Start` / `Prev` / `Next` для навигации по шагам алгоритма |
| **Подсветка активных элементов** | На каждом шаге подсвечиваются узлы и рёбра, участвующие в текущей итерации |
| **Информационная панель** | Отображение текущего потока, накопленной стоимости и описания шага |
| **Адаптивный дизайн** | Корректное отображение на экранах разного размера |

### ⚙️ Backend (Алгоритм)
| Компонент | Описание |
|-----------|----------|
| **Алгоритм с потенциалами** | Successive Shortest Path с редуцированными весами (Дейкстра + Джонсон) |
| **Поддержка отрицательных стоимостей** | Корректная обработка рёбер с отрицательной стоимостью |
| **Детекция циклов** | Обнаружение **только достижимых** отрицательных циклов с информативной ошибкой |
| **Детерминированный трейс** | Полная история изменений состояния для пошаговой визуализации |
| **Валидация данных** | Строгая проверка входных параметров через Pydantic |
| **Stateless-архитектура** | Каждый запрос обрабатывается независимо, упрощая масштабирование |

---

## 🏗️ Архитектура

```
┌─────────────────┐     HTTP/JSON      ┌─────────────────┐
│                 │ ◄──────────────►   │                 │
│   Frontend      │                    │   Backend       │
│   (Browser)     │                    │   (FastAPI)     │
│                 │                    │                 │
│ • Canvas/SVG    │                    │ • Algorithm     │
│ • State Mgmt    │                    │ • Validation    │
│ • API Client    │                    │ • Trace Gen     │
└─────────────────┘                    └─────────────────┘
```

### Поток данных
1. Пользователь строит граф в интерфейсе → состояние хранится в объекте `state`
2. При нажатии `Start` формируется JSON-запрос и отправляется на `POST /api/solve`
3. Backend валидирует данные, запускает алгоритм, генерирует массив шагов
4. Ответ возвращается на клиент, где сохраняется в `algoSteps`
5. Кнопки `Prev`/`Next` переключают индекс текущего шага → вызывается `render()` с подсветкой

---

## 🛠️ Технологический стек

### Backend
| Технология | Назначение |
|------------|-----------|
| **Python 3.10+** | Язык реализации |
| **FastAPI** | Веб-фреймворк, автоматическая генерация OpenAPI |
| **Pydantic v2** | Валидация и сериализация данных |
| **Uvicorn** | ASGI-сервер для разработки и продакшена |

### Frontend
| Технология | Назначение |
|------------|-----------|
| **HTML5 Canvas** | Отрисовка графа и анимаций |
| **Vanilla JavaScript** | Логика взаимодействия, управление состоянием |
| **CSS3 Flexbox** | Адаптивная вёрстка интерфейса |

### Инструменты разработки
```bash
# Backend
pip install fastapi uvicorn pydantic

# Frontend (не требует сборки)
# Достаточно любого статического сервера, например:
python -m http.server 8080  # в директории frontend/
```

---

## 🚀 Быстрый старт

### 1. Клонирование репозитория
```bash
git clone https://github.com/yourusername/min-cost-flow-visualizer.git
cd min-cost-flow-visualizer
```

### 2. Настройка Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Запуск сервера
```bash
# Из директории backend/
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Сервер будет доступен по адресу: **http://localhost:8000**  
Swagger-документация: **http://localhost:8000/docs**

### 4. Запуск Frontend
```bash
cd ../frontend
# Вариант 1: простой статический сервер
python -m http.server 8080

# Вариант 2: открыть index.html напрямую в браузере
# (может потребоваться разрешение CORS или запуск через сервер)
```

Откройте в браузере: **http://localhost:8080**

### 5. Проверка работы
1. Создайте 2–3 вершины кликом по холсту
2. Соедините их рёбрами (клик по первой вершине → клик по второй)
3. Нажмите **▶ Запустить алгоритм**, укажите:
   - Исток (например, `N1`)
   - Сток (например, `N3`)
   - Требуемый поток (например, `5`)
4. Используйте кнопки `Prev`/`Next` для пошагового просмотра

---

## 📡 API Reference

### `POST /api/solve`

Запускает алгоритм поиска потока минимальной стоимости.

#### 📥 Запрос (Request Body)

```json
{
  "nodes": [
    {
      "id": "string",      // Уникальный идентификатор вершины
      "x": 0,              // Координата X (пиксели)
      "y": 0               // Координата Y (пиксели)
    }
  ],
  "edges": [
    {
      "source": "string",  // ID исходной вершины
      "target": "string",  // ID целевой вершины
      "cost": 0.0,         // Стоимость прохождения ребра (может быть отрицательной)
      "capacity": 0.0      // Пропускная способность (> 0)
    }
  ],
  "source_node": "string", // ID узла-источника
  "sink_node": "string",   // ID узла-стока
  "required_flow": 0.0     // Требуемый объём потока (> 0)
}
```

#### 📤 Успешный ответ (200 OK)

```json
{
  "status": "success",
  "min_cost": 43.0,           // Минимальная суммарная стоимость
  "total_flow": 8.0,          // Фактически доставленный поток
  "steps": [                  // Массив шагов для визуализации
    {
      "step_index": 0,
      "description": "Инициализация...",
      "current_flow": 0.0,
      "current_cost": 0.0,
      "edge_flows": {},       // { "A->B": 5.0, ... }
      "highlighted_nodes": ["S", "T"],
      "highlighted_edges": [],
      "potentials": { "S": 0.0, "A": 2.0, ... }  // Опционально
    }
    // ... дополнительные шаги
  ]
}
```

#### ⚠️ Ответ с предупреждением (200 OK + warning)

Возвращается, когда требуемый поток не может быть достигнут полностью:

```json
{
  "status": "success",
  "min_cost": 50.0,
  "total_flow": 10.0,
  "steps": [...],
  "warning": "Требуемый поток недостижим при заданных ограничениях"
}
```

#### ❌ Ошибки

| Код | Тип ошибки | Описание |
|-----|-----------|----------|
| `422` | `validation_error` | Некорректный формат входных данных (см. `detail`) |
| `422` | `invalid_node_reference` | Источник/сток или вершина ребра не найдены в списке узлов |
| `500` | `negative_cycle_in_input` | Обнаружен достижимый из истока цикл отрицательной стоимости |
| `500` | `iteration_limit_exceeded` | Превышено максимальное число итераций (защита от зацикливания) |

Пример ошибки:
```json
{
  "status": "error",
  "error_type": "negative_cycle_in_input",
  "message": "Граф содержит достижимый из истока цикл отрицательной стоимости...",
  "steps": [],
  "min_cost": null,
  "total_flow": null
}
```

---

## 📐 Формат данных

### Ограничения валидации (Pydantic)

| Поле | Тип | Ограничения | Примечание |
|------|-----|-------------|------------|
| `nodes[].id` | `str` | `min_length=1` | Уникальный в пределах графа |
| `nodes[].x`, `y` | `int` | `≥ 0` | Координаты в пикселях |
| `edges[].source`, `target` | `str` | Должны существовать в `nodes` | Ссылки на вершины |
| `edges[].cost` | `float` | Любое конечное значение | Поддерживаются отрицательные стоимости |
| `edges[].capacity` | `float` | `> 0` | Нулевая ёмкость отклоняется валидатором |
| `required_flow` | `float` | `> 0` | Для потока 0 см. раздел "Расширение" |

### Структура шага трейса

Каждый элемент массива `steps` содержит:

```typescript
interface Step {
  step_index: number;           // Порядковый номер (0 = инициализация)
  description: string;          // Человекочитаемое описание действия
  current_flow: number;         // Накопленный поток к данному шагу
  current_cost: number;         // Накопленная стоимость к данному шагу
  edge_flows: Record<string, number>;  // Текущие значения потоков по рёбрам
  highlighted_nodes: string[];  // ID узлов для визуальной подсветки
  highlighted_edges: string[];  // Ключи рёбер ("A->B") для подсветки
  potentials?: Record<string, number>; // Опционально: значения потенциалов
}
```

---

## 💡 Примеры использования

### Пример 1: Базовый граф с двумя путями

```bash
curl -X POST http://localhost:8000/api/solve \
  -H "Content-Type: application/json" \
  -d '{
    "nodes": [
      {"id": "S", "x": 0, "y": 100},
      {"id": "A", "x": 100, "y": 50},
      {"id": "B", "x": 100, "y": 150},
      {"id": "T", "x": 200, "y": 100}
    ],
    "edges": [
      {"source": "S", "target": "A", "cost": 2, "capacity": 5},
      {"source": "S", "target": "B", "cost": 5, "capacity": 10},
      {"source": "A", "target": "T", "cost": 3, "capacity": 5},
      {"source": "B", "target": "T", "cost": 1, "capacity": 10}
    ],
    "source_node": "S",
    "sink_node": "T",
    "required_flow": 8
  }'
```

**Ожидаемый результат:**
- Сначала алгоритм использует дешёвый путь `S→A→T` (стоимость 5) на 5 единиц потока
- Затем насыщает оставшиеся 3 единицы через `S→B→T` (стоимость 6)
- Итог: `min_cost = 5×5 + 3×6 = 43`, `total_flow = 8`

### Пример 2: Отрицательная стоимость (без цикла)

```json
{
  "edges": [
    {"source": "S", "target": "A", "cost": -3, "capacity": 10},
    {"source": "A", "target": "T", "cost": 5, "capacity": 10}
  ],
  "required_flow": 5
}
```

**Результат:** `min_cost = 5 × (-3 + 5) = 10` — алгоритм корректно учитывает выгоду от отрицательного ребра.

### Пример 3: Недостижимый отрицательный цикл

```json
{
  "edges": [
    {"source": "S", "target": "A", "cost": 1, "capacity": 10},
    {"source": "A", "target": "T", "cost": 1, "capacity": 10},
    {"source": "B", "target": "C", "cost": 1, "capacity": 10},
    {"source": "C", "target": "D", "cost": 1, "capacity": 10},
    {"source": "D", "target": "B", "cost": -5, "capacity": 10}
  ]
}
```

**Результат:** ✅ Успех. Цикл `B→C→D→B` игнорируется, так как недостижим из `S`. Решение: поток 5 по пути `S→A→T` со стоимостью 10.

---

## 🧪 Тестирование

### Интеграционные тесты

В корне проекта доступен скрипт `test_api.sh` с 15 сценариями:

```bash
chmod +x test_api.sh
./test_api.sh
```

**Покрытие сценариев:**
- ✅ Нормальные графы с положительными стоимостями
- ✅ Отрицательные рёбра без циклов
- ✅ Достижимые и недостижимые отрицательные циклы
- ✅ Крайние случаи: нулевой поток, недостижимый сток, превышение ёмкости
- ✅ Валидация входных данных

### Модульные тесты (pytest)

```bash
cd backend
pip install pytest
pytest tests/ -v
```

Пример теста (`backend/tests/test_algorithm.py`):
```python
from algorithm import solve_mcmf

def test_negative_cycle_unreachable():
    """Цикл вне достижимой компоненты не должен вызывать ошибку"""
    result = solve_mcmf({
        "nodes": [{"id": "S", "x": 0, "y": 0}, {"id": "T", "x": 100, "y": 0},
                  {"id": "B", "x": 50, "y": 50}, {"id": "C", "x": 50, "y": 100}],
        "edges": [
            {"source": "S", "target": "T", "cost": 1, "capacity": 10},
            {"source": "B", "target": "C", "cost": 1, "capacity": 10},
            {"source": "C", "target": "B", "cost": -5, "capacity": 10}
        ],
        "source_node": "S", "sink_node": "T", "required_flow": 5
    })
    assert result["status"] == "success"
    assert result["min_cost"] == 5.0
```

### Ручное тестирование через Swagger
1. Откройте **http://localhost:8000/docs**
2. Разверните эндпоинт `POST /api/solve`
3. Нажмите **Try it out**, вставьте JSON из примеров
4. Нажмите **Execute** и изучите ответ

---

## 📁 Структура проекта

```
min-cost-flow-visualizer/
├── README.md                 # Этот файл
├── test_api.sh              # Скрипт интеграционных тестов
│
├── backend/
│   ├── main.py              # Точка входа FastAPI, CORS, маршруты
│   ├── models.py            # Pydantic-схемы запросов/ответов
│   ├── algorithm.py         # Реализация MCMF с потенциалами и трейсингом
│   ├── requirements.txt     # Зависимости Python
│   └── tests/
│       └── test_algorithm.py  # Модульные тесты
│
└── frontend/
    ├── index.html           # HTML-каркас приложения
    ├── style.css            # Стили интерфейса
    └── app.js               # Логика: состояние, отрисовка, API-клиент
```

---

## ⚠️ Обработка ошибок

### На стороне клиента (frontend)

При получении ответа с `status: "error"` приложение:
1. Отображает красное сообщение в панели статуса
2. Показывает `alert` с деталями ошибки
3. Блокирует кнопки навигации до повторного запуска

Пример обработки в `app.js`:
```javascript
if (result.status === "error") {
  const msg = result.message || "Неизвестная ошибка";
  document.getElementById('step-info').innerHTML = 
    `<span style="color:#e74c3c">⚠️ ${msg}</span>`;
  alert(`Ошибка алгоритма:\n${msg}`);
  updateControls();
  return;
}
```

### На стороне сервера (backend)

| Сценарий | Механизм обработки |
|----------|-------------------|
| Некорректный JSON | FastAPI автоматически возвращает `422` с деталями |
| Несуществующий узел | `KeyError` перехватывается, возвращается `invalid_node_reference` |
| Отрицательный цикл | `_bellman_ford_init` возвращает `None` → ошибка `negative_cycle_in_input` |
| Зацикливание алгоритма | Счётчик итераций `MAX_ITERATIONS` прерывает выполнение |
| Численная нестабильность | Эпсилон-сравнения (`1e-9`) для операций с плавающей точкой |

---

## 🔧 Расширение функционала

### Добавление поддержки нулевого потока
1. В `backend/models.py`:
   ```python
   required_flow: float = Field(..., ge=0)  # ge вместо gt
   ```
2. В `frontend/app.js` — убрать валидацию `requiredFlow > 0`

### Анимация переходов между шагами
```javascript
// В renderStep() добавить плавное изменение стилей
function renderStep() {
  // ...
  document.querySelectorAll('.edge').forEach(el => {
    el.style.transition = 'stroke 0.3s, stroke-width 0.3s';
    // применить стили подсветки
  });
}
```

### Экспорт/импорт графа в JSON
```javascript
// Экспорт
function exportGraph() {
  const data = JSON.stringify({ nodes: state.nodes, edges: state.edges }, null, 2);
  const blob = new Blob([data], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = 'graph.json'; a.click();
}

// Импорт (через <input type="file">)
function importGraph(jsonText) {
  const data = JSON.parse(jsonText);
  state.nodes = data.nodes;
  state.edges = data.edges;
  invalidateAlgorithmResults();
  render();
}
```

### Подключение библиотеки визуализации (опционально)
Для сложных графов рассмотрите замену Canvas на:
- **[Cytoscape.js](https://cytoscape.org/)** — интерактивные графы с лагами, фильтрами, анимациями
- **[vis.js Network](https://visjs.org/)** — физическая симуляция, авто-раскладка
- **[D3.js](https://d3js.org/)** — максимальная гибкость при высокой сложности

---

## 📄 Лицензия

Проект распространяется под лицензией **MIT**. См. файл [LICENSE](LICENSE) для деталей.

```
MIT License

Copyright (c) 2024 Your Name

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 🤝 Вклад в проект

1. Создайте форк репозитория
2. Создайте ветку для вашей фичи (`git checkout -b feature/amazing-feature`)
3. Внесите изменения и добавьте тесты
4. Закоммитьте (`git commit -m 'Add amazing feature'`)
5. Отправьте в форк (`git push origin feature/amazing-feature`)
6. Откройте Pull Request

**Требования к коду:**
- ✅ Соответствие PEP 8 (Python) и ESLint recommended (JS)
- ✅ Покрытие новых функций тестами
- ✅ Обновление документации при изменении API

---

> 💡 **Совет**: Для отладки алгоритма используйте логирование:
> ```bash
> # В backend/algorithm.py добавьте:
> import logging
> logging.basicConfig(level=logging.DEBUG)
> logger = logging.getLogger(__name__)
> logger.debug(f"Итерация {step_count}: поток {push}, стоимость {path_real_cost}")
> ```

---

**Разработано с ❤️ для изучения алгоритмов потоков в сетях.**  
Если проект оказался полезным — поставьте ⭐ на GitHub!