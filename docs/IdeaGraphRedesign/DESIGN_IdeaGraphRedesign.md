# DESIGN_IdeaGraphRedesign

## 1. 架构设计
保持原有的前后端分离架构：
- **Backend (FastAPI)**: 提供 `/graph` 接口，返回 `nodes` 和 `edges` 数据。
- **Frontend (Streamlit)**: 获取数据，转换为 ECharts 配置项 (Option)，通过 `st_echarts` 组件渲染。

## 2. 视觉设计
- **背景**: 与 Streamlit 深色主题一致 (`#0E1117`)。
- **节点**:
  - **核心节点 (Level 1)**: 大尺寸 (60)，橙色高亮，强发光。
  - **分类节点 (Level 2)**: 中尺寸 (30)，根据分类分配霓虹色（青、红、绿、紫）。
  - **知识节点 (Level 3)**: 小尺寸 (15)，默认淡蓝色，根据连接关系分布。
- **连线**:
  - 曲线 (`curveness: 0.3`)。
  - 颜色随源节点 (`source`)。
  - 半透明，减少视觉杂乱。

## 3. 交互设计
- **布局切换**: 下拉菜单选择 `Force` 或 `Circular`。
- **参数调节**: 力导向图模式下提供 `Repulsion` (排斥力) 滑块，控制节点间距。
- **标签控制**: Toggle 开关控制是否显示节点名称。
- **鼠标交互**:
  - **Hover**: 显示 Tooltip (标题 + 摘要)，高亮相邻节点和连线。
  - **Drag**: 允许拖拽节点重新布局。
  - **Zoom**: 滚轮缩放画布。

## 4. 数据映射
| 字段 | 来源 | 映射属性 |
|---|---|---|
| id | node.id | name (key) |
| name | node.label | label.formatter |
| symbolSize | node.group | level1=60, level2=30, level3=15 |
| itemStyle.color | node.category | category_colors 字典映射 |
| tooltip | node.summary | tooltip.formatter |
