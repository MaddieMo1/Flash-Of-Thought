# DESIGN: 知识图谱 (Idea Graph) - Iteration 2

## 1. 核心变更：基于标签的层级结构
用户希望图谱更能体现“想法”的归类和层级，而不仅仅是单篇笔记的拆解。结合“标签系统”，我们将图谱重构为：
**Tag (类别) -> Note (想法) -> Core Idea (细节)**

## 2. 数据结构设计

### 2.1 节点 (Nodes)
- **Level 0 (Root)**: "Idea Universe" (可选，作为一个中心点)
- **Level 1 (Tag)**: 标签节点。例如 "AI", "创业"。
    - Color: `#FF9F1C` (Orange)
    - Size: 30
- **Level 2 (Note)**: 笔记标题节点。例如 "AI虚拟仿真"。
    - Color: `#2EC4B6` (Teal)
    - Size: 20
- **Level 3 (Idea)**: 核心观点节点。例如 "AI教学助手"。
    - Color: `#CBF3F0` (Light Blue)
    - Size: 10

### 2.2 边 (Edges)
- `Tag` -> `Note`: 当笔记包含该标签时连接。
- `Note` -> `Idea`: 笔记与其提取出的核心观点连接。

## 3. 接口逻辑更新 (`GET /api/v1/graph`)
1. 获取所有笔记。
2. 提取所有不重复的 Tags。
3. 遍历 Tags，创建 Tag Nodes。
4. 遍历 Notes:
    - 创建 Note Node。
    - 找到该 Note 的 Tags，创建 `Tag -> Note` 的 Edges。
    - 如果 Note 没有 Tag，连接到一个 "Uncategorized" Tag。
    - 解析 Note 的 Core Ideas，创建 Idea Nodes 和 `Note -> Idea` 的 Edges。

## 4. UI 改进
- **标签展示**: 在笔记卡片中使用更醒目的 `#Tag` 样式。
- **图谱配置**: 调整 Physics 参数，使层级更分明（增加 `springLength`，减少 `gravity`）。

## 5. 技术选型
- 继续使用 `streamlit-agraph` 实现 3D 效果。
- 后端逻辑处理聚合，不引入 Neo4j。
