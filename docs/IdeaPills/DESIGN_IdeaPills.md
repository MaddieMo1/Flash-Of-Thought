# DESIGN_IdeaPills: 系统架构与设计文档

## 1. 系统架构图 (System Architecture)

```mermaid
graph TD
    User[用户] --> WebUI[Streamlit Web UI]
    Agent[AI Agent / IDE] --> MCP[MCP Server (Stdio/SSE)]
    
    subgraph "IdeaPills Backend (FastAPI)"
        WebUI --> API[REST API]
        MCP --> API
        
        API --> Service_Audio[音频服务]
        API --> Service_Note[笔记服务]
        API --> Service_RAG[检索服务]
    end
    
    subgraph "External Services"
        Service_Audio --> OSS[阿里云 OSS]
        Service_Audio --> DashScope_ASR[Qwen ASR]
        Service_Note --> DashScope_LLM[Qwen LLM]
        Service_RAG --> DashScope_Embed[Qwen Embedding]
    end
    
    subgraph "Storage"
        Service_RAG --> ChromaDB[(ChromaDB 向量库)]
        Service_Note --> SQLite[(SQLite 元数据/笔记库)]
    end
```

## 2. 模块设计 (Module Design)

### 2.1 核心实体 (Entities)

*   **IdeaNote**:
    *   `id`: UUID
    *   `content`: String (结构化后的 Markdown 内容)
    *   `raw_text`: String (ASR 转出的原始文本)
    *   `audio_url`: String (OSS 链接)
    *   `created_at`: Datetime
    *   `tags`: List[String]
    *   `embedding_id`: String (关联向量库 ID)

### 2.2 接口定义 (API Endpoints)

*   `POST /api/v1/upload_audio`: 上传音频 -> OSS -> ASR -> 返回 `raw_text` 和 `audio_url`
*   `POST /api/v1/process_note`: `raw_text` -> LLM -> 返回 `IdeaNote` 结构
*   `POST /api/v1/save_note`: 保存 `IdeaNote` -> ChromaDB + SQLite
*   `GET /api/v1/query_notes`: `query_text` -> Embedding -> ChromaDB Search -> 返回 `List[IdeaNote]`

### 2.3 MCP 工具定义 (MCP Tools)

*   **Tool: `add_voice_idea`**
    *   **Description**: 上传一段语音或文本，将其转化为结构化笔记并保存。
    *   **Arguments**: `audio_path` (optional), `text_content` (optional)
*   **Tool: `search_ideas`**
    *   **Description**: 基于语义搜索用户的历史想法和笔记。
    *   **Arguments**: `query` (string, required), `limit` (int, default=5)

## 3. 目录结构 (Directory Structure)

```
IdeaPills/
├── .env                    # 环境变量
├── requirements.txt        # 依赖包
├── main.py                 # FastAPI 入口 & MCP Server 入口
├── app/
│   ├── api/                # API 路由
│   ├── core/               # 核心配置 (Config, Logging)
│   ├── services/           # 业务逻辑
│   │   ├── oss_service.py  # OSS 上传
│   │   ├── llm_service.py  # Qwen 调用 (ASR, Chat, Embed)
│   │   └── rag_service.py  # ChromaDB 操作
│   ├── models/             # 数据模型 (Pydantic)
│   └── utils/              # 工具函数
├── ui/                     # Streamlit 前端
│   └── app.py
└── data/                   # 本地数据存储 (ChromaDB, SQLite)
```

## 4. 数据流 (Data Flow) - 录音场景

1.  **Input**: 用户上传 `voice.mp3`
2.  **OSS**: 上传至 `oss://flashnote-audio/voice.mp3`，获取 URL
3.  **ASR**: 调用 DashScope ASR，获取文本 "我今天想到一个关于..."
4.  **LLM**: 调用 Qwen-Plus，Prompt: "你是一个专业的笔记整理助手..."，输出 JSON/Markdown
5.  **Storage**:
    *   文本存入 SQLite (作为持久化记录)
    *   文本调用 Embedding -> 向量存入 ChromaDB
6.  **Output**: 返回成功信息及笔记 ID

## 5. 异常处理 (Error Handling)

*   **ASR 失败**: 提示用户检查音频格式或重试，保留原始音频 URL。
*   **LLM 幻觉**: 在 Prompt 中增加约束，要求严格基于输入内容整理，不随意发散。
*   **OSS 连接失败**: 本地缓存音频，待网络恢复后重试（V2 版本特性，V1 直接报错）。
