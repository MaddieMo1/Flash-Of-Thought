# IdeaPills: 智能语音笔记助手

IdeaPills 是一个能够将你的语音想法转化为结构化知识的智能助手。它利用通义千问 (Qwen) 进行语音转写和内容整理，并使用向量数据库构建个人知识库，支持自然语言检索。

## ✨ 核心功能

1.  **语音转结构化笔记**: 录音 -> 文字 (ASR) -> 结构化整理 (摘要/详情/行动建议)。
2.  **个人知识库**: 所有笔记自动向量化存储，支持语义搜索。
3.  **多端接入**:
    *   **Web UI**: 直观的 Streamlit 界面。
    *   **REST API**: 标准 FastAPI 接口。
    *   **MCP Server**: 支持作为工具接入 Claude Desktop 或 Trae IDE。

## 🛠️ 技术栈

*   **Backend**: FastAPI, Python 3.10+
*   **Frontend**: Streamlit
*   **AI Services**: Aliyun DashScope (Qwen-Plus, Qwen-ASR, Text-Embedding-v4)
*   **Storage**: Aliyun OSS (Audio), ChromaDB (Vector), SQLite (Metadata)
*   **Protocol**: Model Context Protocol (MCP)

## 🚀 快速开始

### 1. 环境准备

确保已安装 Python 3.10+，并配置好 `.env` 文件（包含 OSS 和 DashScope Key）。

```bash
# 安装依赖
pip install -r requirements.txt
```

### 2. 启动服务

**启动后端 API**:
```bash
uvicorn app.main:app --reload
```
API 文档地址: http://localhost:8000/docs

**启动前端界面**:
```bash
streamlit run ui/app.py
```
访问地址: http://localhost:8501

### 3. MCP 集成

IdeaPills 遵循 MCP 协议，可以作为工具集成到支持 MCP 的客户端中。

**Stdio 模式运行**:
```bash
python mcp_server.py
```

## 📂 目录结构

```
IdeaPills/
├── app/                # 后端核心代码
│   ├── api/            # API 路由
│   ├── core/           # 配置管理
│   ├── services/       # 业务逻辑 (OSS, LLM, RAG)
│   └── models/         # 数据模型
├── ui/                 # Streamlit 前端代码
├── docs/               # 项目文档
├── data/               # 本地数据存储
├── mcp_server.py       # MCP 服务入口
└── requirements.txt    # 项目依赖
```
