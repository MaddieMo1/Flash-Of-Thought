# TODO_FlashOfThought: 待办与支持事项

为了确保您能顺利运行 FlashOfThought，请关注以下事项：

## 1. 环境配置 (Immediate Actions)
- [ ] **安装依赖**: 请在终端运行 `pip install -r requirements.txt`。
- [ ] **环境变量**: 确保 `.env` 文件中的 `OSS_ACCESS_KEY_ID`, `OSS_ACCESS_KEY_SECRET`, `DASHSCOPE_API_KEY` 均已正确填写且有效。

## 2. 运行指引 (Running Guide)
建议开启两个终端窗口：
1.  **终端 1 (后端)**: `uvicorn app.main:app --reload`
2.  **终端 2 (前端)**: `streamlit run ui/app.py`

## 3. 已知限制 (Limitations)
-   **本地向量库**: ChromaDB 数据存储在本地 `data/chroma_db` 目录，请勿随意删除，否则会导致知识库丢失。
-   **并发限制**: 依赖阿里云 DashScope 的 API 配额，高并发下可能会触发限流。

## 4. 获取支持 (Support)
如果您在运行过程中遇到 `ModuleNotFoundError` 或 API 连接错误，请首先检查 `pip list` 确认依赖是否安装，以及 `.env` 配置是否生效。
