# DESIGN: 知识图谱 (Idea Graph)

## 1. 系统分层设计

### 1.1 整体架构
- **Frontend (Streamlit)**: 使用 `streamlit-agraph` 组件渲染 3D 力导向图。
- **Backend (FastAPI)**: 提供 `/api/v1/graph` 接口，返回图谱所需的节点 (Nodes) 和边 (Edges) 数据。
- **Data Layer (ChromaDB)**: 存储笔记数据。

### 1.2 接口设计
- **`GET /api/v1/graph`**
    - **Request**: None
    - **Response**:
        ```json
        {
          "nodes": [
            {"id": "note_1", "label": "AI Idea", "group": "note", "size": 20},
            {"id": "idea_1_1", "label": "Virtual Sim", "group": "idea", "size": 10}
          ],
          "edges": [
            {"source": "note_1", "target": "idea_1_1", "type": "hierarchy"}
          ]
        }
        ```

### 1.3 数据流向
1. Frontend 请求 `/api/v1/graph`。
2. Backend 调用 `RagService.get_all_notes()` 获取所有笔记。
3. Backend 解析笔记内容：
    - 提取 Title 作为主节点。
    - 解析 Core Ideas / Key Features 作为子节点。
4. Backend 构建层级关系 (Note -> Idea)。
5. (可选) Backend 计算笔记间相似度构建关联关系 (Note <-> Note)。
6. Frontend 接收数据并渲染。

## 2. 模块设计

### 2.1 Backend (`app/api/routes.py`)
- 新增 `get_graph_data` 函数。
- 逻辑：
    - 遍历所有笔记。
    - 解析 `document` 字段中的 "Core Ideas" 和 "Key Features"。
    - 生成 Node 和 Edge 对象。

### 2.2 Frontend (`ui/app.py`)
- 引入 `streamlit_agraph`。
- 新增页面/Tab: "知识图谱"。
- 配置图谱参数 (Physics, Colors)。

## 3. 异常处理
- 解析失败：如果笔记格式不规范，仅展示 Title 节点。
- 空数据：提示用户去录入想法。
