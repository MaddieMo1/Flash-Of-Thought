# TASK: 知识图谱 (Idea Graph)

## 1. 子任务拆分

### Task 1: 后端接口实现
- **输入**: 无。
- **输出**: `GET /api/v1/graph` 接口，返回 Nodes 和 Edges JSON 数据。
- **实现细节**:
    - 在 `app/services/rag_service.py` 确认 `get_all_notes` 支持大批量获取。
    - 在 `app/api/routes.py` 新增 `get_graph` 路由。
    - 编写解析逻辑：从 document 文本中提取 Core Ideas 和 Key Features。
    - 构建图数据结构。
- **依赖**: 无。

### Task 2: 前端页面实现
- **输入**: `/api/v1/graph` 接口数据。
- **输出**: Streamlit 页面中的 3D 知识图谱。
- **实现细节**:
    - 安装 `streamlit-agraph`。
    - 在 `ui/app.py` 中新增 `display_graph` 函数。
    - 配置 `agraph` 参数 (Config, Node, Edge)。
    - 添加 Sidebar 导航项。
- **依赖**: Task 1。

### Task 3: 验证与优化
- **输入**: 运行的应用。
- **输出**: 可交互的 3D 图谱。
- **实现细节**:
    - 验证节点点击是否显示详情 (Sidebar)。
    - 调整图谱物理参数 (Gravity, Spring Length) 以优化布局。
    - 确认中文显示正常。

## 2. 依赖关系图
Task 1 -> Task 2 -> Task 3
