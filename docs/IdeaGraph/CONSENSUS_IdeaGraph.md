# CONSENSUS: 知识图谱 (Idea Graph)

## 1. 最终共识
- **目标**: 实现基于 3D 力导向图的知识图谱，可视化展示笔记与核心观点的层级结构。
- **技术方案**:
    - **Frontend**: `streamlit-agraph` (支持 3D 模式)。
    - **Backend**: `/api/v1/graph` 接口提供节点和边数据。
    - **Data Source**: ChromaDB 中的笔记数据，解析 Core Ideas 作为子节点。

## 2. 关键决策点
- **Q1: 3D 可视化**: 确认使用 `streamlit-agraph`。
- **Q2: 数据构建**: 仅展示层级结构 (Note -> Idea) 和关联结构 (Note <-> Note)。
- **Q3: 交互**: 简单的点击节点查看详情 (Sidebar)。

## 3. 验收标准
- **UI**: Streamlit 页面显示 3D 图谱，节点可点击。
- **数据**: 图谱能够正确展示笔记的标题和核心观点。
- **性能**: 加载 20+ 个笔记时不卡顿。
