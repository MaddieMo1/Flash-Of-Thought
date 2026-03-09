# TASK_IdeaGraphRedesign

- [x] **依赖管理**
  - [x] 安装 `streamlit-echarts` (降级为 0.4.0 以修复 pyproject.toml 兼容性问题)。
  - [x] 更新 `requirements.txt`。

- [x] **UI 开发**
  - [x] 移除旧版 `plotly` 3D 代码。
  - [x] 引入 `st_echarts`。
  - [x] 实现 ECharts Option 生成逻辑。
  - [x] 实现节点大小、颜色映射逻辑。
  - [x] 实现布局切换控件 (Force/Circular)。

- [x] **交互优化**
  - [x] 配置 `roam: True` (缩放/平移)。
  - [x] 配置 `emphasis: focus: 'adjacency'` (邻接高亮)。
  - [x] 添加 Tooltip 格式化。

- [x] **验证**
  - [x] 启动应用无报错。
  - [x] 检查图谱渲染效果。
