# ACCEPTANCE: 知识图谱 (Idea Graph)

## 1. 任务完成情况

### Task 1: 后端接口实现
- [x] 在 `app/services/rag_service.py` 确认 `get_all_notes` 支持大批量获取。
- [x] 在 `app/api/routes.py` 新增 `get_graph` 路由。
- [x] 编写解析逻辑：从 document 文本中提取 Core Ideas 和 Key Features。
- [x] 构建图数据结构。

### Task 2: 前端页面实现
- [x] 安装 `streamlit-agraph`。
- [x] 在 `ui/app.py` 中新增 `display_graph` 函数。
- [x] 配置 `agraph` 参数 (Config, Node, Edge)。
- [x] 添加 Sidebar 导航项。

### Task 3: 验证与优化
- [x] 运行的应用。
- [x] 可交互的 3D 图谱。
- [x] 验证节点点击是否显示详情 (Sidebar)。
- [x] 调整图谱物理参数 (Gravity, Spring Length) 以优化布局。
- [x] 确认中文显示正常。

## 2. 问题记录
- 曾遇到 Backend 未重新加载导致 404 的问题，已修复。
