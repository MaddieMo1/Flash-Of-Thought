# FlashOfThought (闪念) 💡

**FlashOfThought** 是一款由大语言模型（LLM）驱动的智能语音笔记与灵感管理助手。它能够通过语音或文字快速捕捉用户的“闪念”，利用 AI 自动提取核心观点、构建结构化笔记，并提供知识图谱可视化、语义检索、AI 深度分析以及交互式问答等功能，帮助用户将零散的灵感转化为有价值的知识库。

## ✨ 核心功能

1. **🎙️ 灵感录入 (Record Idea)**
   - **多源输入**：支持上传音频文件、麦克风录音、纯文本输入。
   - **AI 自动结构化**：自动提取标题、标签、核心摘要、核心观点、关键功能等。
   - **第二大脑关联**：录入新想法时，通过 RAG 自动在侧边栏推荐库中相似的灵感。

2. **🧠 知识回顾与管理 (Knowledge Review)**
   - **智能搜索**：基于 ChromaDB 的向量语义检索，支持自然语言提问。
   - **聊天回顾**：与你的知识库对话，AI 会基于过往笔记作为上下文回答。
   - **AI 周报**：自动汇总近期笔记，生成主题分布和重点想法摘要。

3. **🤖 AI 深度分析 (Deep Analysis)**
   - **扩展想法**：AI 自动补充具体功能、商业模式及技术实现建议。
   - **生成路线**：自动规划出分阶段的落地执行 Roadmap。
   - **灵感评分**：从创新性、商业价值、技术难度、可行性四个维度进行打分评估。

4. **🌌 知识图谱 (Knowledge Graph)**
   - 将知识库渲染为可视化的节点图谱，支持力导向图与环形布局切换。

## 🛠️ 技术架构

- **后端 (Backend)**: `FastAPI` + `Python`
- **大语言模型 (LLM)**: 阿里云 DashScope (Qwen系列模型, 语音转写, 向量模型)
- **云存储 (OSS)**: 阿里云 OSS (用于音频文件存储)
- **向量数据库**: `ChromaDB` (本地化 RAG 检索)
- **前端 (Frontend)**: 
  - **当前版本**: `Streamlit` (基于 Python 的快速数据应用框架)
  - **下一代版本**: `React` + `Vite` + `TypeScript` + `Tailwind CSS` + `shadcn/ui`

## 🚀 快速开始

### 1. 环境准备

确保你已经安装了 `Python 3.10+` 和 `Node.js 18+`。

### 2. 后端配置与运行

1. 复制环境变量模板并填入你的阿里云 OSS 和 DashScope API Key：
   ```bash
   cp .env.example .env
   ```
2. 安装 Python 依赖：
   ```bash
   pip install -r requirements.txt
   ```
3. 启动 FastAPI 后端服务：
   ```bash
   uvicorn app.main:app --reload
   ```

### 3. 前端运行

**选项 A：运行 Streamlit 版本 (当前主版本)**
```bash
streamlit run ui/app_pro.py
```

**选项 B：运行 React 版本 (重构中)**
```bash
npm install
npm run dev
```

## 📝 许可证

MIT License
