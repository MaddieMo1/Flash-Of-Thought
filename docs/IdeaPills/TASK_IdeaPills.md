# TASK_IdeaPills: 开发任务清单

## 1. 基础环境搭建 (Setup)
- [ ] **Task-001**: 初始化项目结构
    - 创建 `app/`, `ui/`, `data/` 等目录
    - 创建 `requirements.txt` 并安装依赖 (fastapi, uvicorn, streamlit, chromadb, dashscope, oss2, mcp)
    - 验证 `.env` 加载与 API Key 有效性
    - **Deliverable**: 可运行的 `Hello World` FastAPI 服务

## 2. 核心服务层 (Core Services)
- [ ] **Task-002**: 实现 OSS 服务 (`oss_service.py`)
    - 封装 OSS 上传功能
    - 封装 URL 生成功能
    - **Test**: 编写脚本上传一个测试文件并验证 URL 可访问
- [ ] **Task-003**: 实现 LLM 服务 (`llm_service.py`)
    - 封装 DashScope ASR (语音转文本)
    - 封装 DashScope Chat (文本结构化)
    - 封装 DashScope Embedding (文本向量化)
    - **Test**: 传入一段测试音频，验证能否输出结构化文本
- [ ] **Task-004**: 实现 存储与检索服务 (`rag_service.py`)
    - 初始化 ChromaDB Client
    - 实现 `add_document` (存入向量 + 元数据)
    - 实现 `query_documents` (语义检索)
    - **Test**: 存入 3 条测试数据，验证检索准确性

## 3. 接口与应用层 (API & App)
- [ ] **Task-005**: 开发 FastAPI 接口
    - `/upload`: 处理音频上传流程
    - `/process`: 触发处理流程
    - `/search`: 检索接口
    - **Test**: 使用 Postman/Curl 测试接口
- [ ] **Task-006**: 开发 Streamlit 前端 (`ui/app.py`)
    - 录音组件 / 文件上传组件
    - 笔记展示卡片
    - 搜索框与结果展示
    - **Deliverable**: 可交互的 Web 界面

## 4. MCP 集成 (Integration)
- [ ] **Task-007**: 封装 MCP Server
    - 定义 `add_idea` 工具
    - 定义 `search_ideas` 工具
    - 配置 MCP Server 启动入口
    - **Test**: 使用 MCP Inspector 或 Trae 自身连接测试

## 5. 验收与文档 (Finalize)
- [ ] **Task-008**: 编写使用文档与最终测试
    - 更新 `README.md`
    - 执行全流程测试
    - 录制演示 Demo (可选)
