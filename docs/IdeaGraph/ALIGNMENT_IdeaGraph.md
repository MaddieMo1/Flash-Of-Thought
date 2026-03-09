# ALIGNMENT: 知识图谱 (Idea Graph)

## 1. 项目上下文分析
- **项目名称**: IdeaPills (语音想法助手)
- **核心功能**: 语音/文本录入想法，AI 自动整理结构化笔记，语义搜索回顾。
- **技术栈**:
    - **Frontend**: Streamlit
    - **Backend**: FastAPI
    - **Database**: ChromaDB (Vector Search), Local JSON/File storage (implied, need to verify persistence)
    - **AI**: DashScope (ASR, LLM)

## 2. 需求理解确认
- **目标**: 实现 "Idea Graph" (知识图谱) 功能。
- **核心特性**:
    - **3D 思维导图 UI**: 可视化展示想法及其层级结构。
    - **层级结构**: 例如 `AI -> AI虚拟仿真 -> AI教学助手`。
- **数据来源**:
    - 现有的笔记数据 (Title, Summary, Core Ideas, Key Features)。
    - 笔记之间的关联 (Semantic Similarity)。
    - 笔记内部的层级 (Note -> Core Ideas).

## 3. 智能决策策略 & 关键问题

### Q1: 3D 可视化技术选型
- **选项 A**: `streamlit-agraph`. 支持 3D Force Directed Graph，集成简单。
- **选项 B**: `streamlit-d3-demo` 或自定义 `ForceGraph3D` (via `react-force-graph-3d` in HTML component). 效果更炫酷，但开发成本高。
- **决策**: 推荐使用 **`streamlit-agraph`** 作为 MVP 方案，因为它有现成的 Streamlit 组件，支持配置节点和边，且支持 3D 模式。如果效果不满足，再考虑自定义 HTML/JS 组件。

### Q2: 图谱数据构建逻辑
- **节点 (Nodes)**:
    - Level 1: 笔记标题 (Title) - 作为主节点。
    - Level 2: 核心观点 (Core Ideas) / 关键功能 (Key Features) - 作为子节点。
- **边 (Edges)**:
    - 包含关系: 笔记 -> 核心观点。
    - 关联关系: 笔记 A <-> 笔记 B (基于语义相似度)。
- **决策**: 优先展示**层级结构** (Tree/Hierarchy)，辅助展示**关联结构** (Network)。

### Q3: 交互设计
- 点击节点显示详情？(Streamlit 刷新机制可能较慢，需优化体验)
- 筛选/搜索特定想法？

## 4. 待确认事项
- 是否需要持久化图谱布局？(通常不需要，自动布局即可)
- 颜色编码策略 (例如按标签着色?)

## 5. 结论
- **模块**: 新增 `ui/graph_view.py` (或在 `ui/app.py` 中新增 Tab)。
- **依赖**: 需要安装 `streamlit-agraph`。
