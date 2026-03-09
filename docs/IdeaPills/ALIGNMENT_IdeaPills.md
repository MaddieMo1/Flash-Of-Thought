# ALIGNMENT_IdeaPills: 语音笔记智能助手需求对齐文档

## 1. 项目背景与目标
用户希望构建一个"即时语音记录想法"的应用，核心是将语音转化为结构化的知识，并能够被其他系统（如MCP客户端、第三方软件）调用。项目名称暂定为 **IdeaPills**。

## 2. 核心需求分析 (Core Requirements)

| 需求点 | 详细描述 | 技术实现推断 |
| :--- | :--- | :--- |
| **1. 语音转文字与结构化** | 用户录音 -> 转文字 -> 提取核心观点、待办事项、后续建议 -> 生成结构化文档 | **ASR**: Qwen-Audio / Qwen-ASR (qwen3-asr-flash)<br>**LLM**: Qwen-Plus (结构化处理) |
| **2. 向量化与知识库** | 转化后的文档内容需向量化存储，支持语义检索 | **Embedding**: text-embedding-v4<br>**Vector DB**: ChromaDB (本地轻量级) 或 Qdrant |
| **3. 对外API封装** | 供其他软件调用 (RESTful API) | **Framework**: FastAPI (Python)<br>**Protocol**: HTTP/JSON |
| **4. MCP/Skills封装** | 符合 Model Context Protocol 标准，可被Claude/Trae等IDE或Agent直接调用 | **SDK**: mcp-python-sdk<br>**Tools**: `add_idea`, `query_ideas` |

## 3. 技术架构栈 (Tech Stack)

基于 `.env` 配置和需求，建议采用以下技术栈：

*   **编程语言**: Python 3.10+
*   **Web框架**: FastAPI (高性能异步框架，适合IO密集型AI任务)
*   **云服务 (基于.env)**:
    *   **对象存储**: 阿里云 OSS (Bucket: `flashnote-audio`) - 存储原始录音文件
    *   **AI模型服务**: 阿里云 DashScope (Qwen-Plus, Qwen-ASR, Embedding-v4)
*   **数据存储**:
    *   **向量数据库**: ChromaDB (默认) 或 Qdrant (Docker部署)
    *   **元数据存储**: SQLite (轻量级) 或 PostgreSQL (生产级)
*   **协议标准**: Model Context Protocol (MCP)

## 4. 关键流程 (Key Workflows)

### 4.1 想法录入流程
1.  **Client** 上传音频文件 -> **API** 接收
2.  **API** 上传音频至 **Aliyun OSS**
3.  **API** 调用 **DashScope ASR** 获取原始文本
4.  **API** 调用 **Qwen-Plus** 进行文本清洗、结构化 (Markdown格式: 摘要/详情/行动建议)
5.  **API** 返回结构化内容供用户确认 (Review)

### 4.2 知识入库流程
1.  用户确认后 -> **System** 调用 **DashScope Embedding**
2.  **System** 将 向量 + 结构化文本 + 元数据 存入 **Vector DB**

## 5. 待确认问题 (Decision Points)

为了确保开发符合预期，请确认以下决策点：

1.  **用户界面 (UI)**:
    *   A: 仅提供后端 API 和 MCP Server (Headless)
    *   B: 提供一个简单的 Web 界面 (Streamlit/Gradio) 用于测试和演示 **(推荐)**
    *   C: 需要完整的 React/Vue 前端 (开发周期较长)
2.  **向量数据库选型**:
    *   A: ChromaDB (本地文件存储，无需Docker，Python原生支持，最简单) **(推荐)**
    *   B: Qdrant/Milvus (需要Docker容器，性能更强)
3.  **MCP 运行模式**:
    *   A: 通过 stdio 运行 (本地 IDE 直接连接)
    *   B: 通过 SSE (Server-Sent Events) 运行 (HTTP 服务模式)

## 6. 下一步计划 (Next Steps)

1.  用户确认上述架构。
2.  创建 `DESIGN_IdeaPills.md` 细化接口定义。
3.  初始化 FastAPI 项目与 MCP Server 框架。
