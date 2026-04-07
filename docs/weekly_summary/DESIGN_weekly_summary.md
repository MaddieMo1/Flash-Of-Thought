# 设计文档：AI 周报总结

## 1. 架构

### 后端
- **服务层**：
    - `RagService`：添加方法 `get_notes_by_time_range(start_timestamp, end_timestamp)` 以高效检索相关笔记。
    - `LLMService`：添加方法 `generate_weekly_summary(notes_list)` 以提示 LLM。
- **API 层**：
    - `POST /api/v1/analyze/weekly_summary`：触发流程的端点。接受可选的 `start_date` 和 `end_date`。

### 前端
- **UI 组件**：
    - 在 `ui/app.py` 中，位于 “🔍 知识回顾” -> “周报总结”（新标签页或部分）。
    - 一个 “生成周报” 按钮。
    - 一个用于显示 Markdown 结果的区域。

## 2. 数据流
1. **用户** 在 UI 中点击 “生成周报”。
2. **UI** 发送 `POST /api/v1/analyze/weekly_summary`，参数 `days=7`。
3. **API** 计算时间戳 `now - 7 days`。
4. **API** 调用 `RagService.get_notes_by_time_range`。
5. **RagService** 查询 ChromaDB（或在内存中过滤）以获取创建时间 > 时间戳的笔记。
6. **API** 将笔记（标题、摘要、标签）格式化为文本块。
7. **API** 调用 `LLMService.generate_weekly_summary` 处理文本块。
8. **LLM** 返回 JSON 或 Markdown 摘要。
9. **API** 将结果返回给 UI。
10. **UI** 渲染摘要。

## 3. 接口设计

### API 接口
```json
POST /api/v1/analyze/weekly_summary
Request:
{
  "days": 7
}

Response:
{
  "total_count": 12,
  "start_date": "2023-10-20",
  "end_date": "2023-10-27",
  "summary_markdown": "## 本周灵感总结\n..."
}
```

### LLM 提示词设计
```text
Role: Professional Personal Assistant.
Task: Summarize the following user ideas from the past week.
Input: List of ideas (Title, Summary, Tags).
Output:
1. Total count.
2. Topic breakdown (group by tags or inferred topics).
3. Key Highlights (3-5 most interesting ideas).
4. Brief synthesis of the week's focus.
Format: Markdown.
```
