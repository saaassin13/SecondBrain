# 个人知识库系统

基于 FastAPI + ChromaDB + Ollama + Gradio 的 RAG（检索增强生成）知识库系统，提供文档上传、向量存储、智能问答等功能。

## ✨ 功能特性

- 📄 **文档上传**：支持 PDF 和 TXT 格式文档上传
- 🔍 **向量存储**：使用 ChromaDB 进行文档向量化存储和检索
- 💬 **智能问答**：基于 RAG 技术的文档问答功能
- 📦 **文档管理**：文档列表查看、删除等管理功能
- 🎨 **Web 界面**：基于 Gradio 的友好 Web 界面
- 🚀 **一键启动**：提供便捷的启动脚本

## 🛠 技术栈

- **FastAPI**: 高性能 Web 框架，提供 RESTful API
- **ChromaDB**: 开源向量数据库，用于存储和检索文档向量
- **sentence-transformers**: 文本向量化模型（all-MiniLM-L6-v2）
- **Ollama**: LLM 推理服务，使用 qwen2.5:7b 模型
- **Gradio**: Web UI 框架，提供友好的用户界面
- **pypdf**: PDF 文档解析库

## 📋 环境要求

- Python 3.8+
- Docker 和 Docker Compose（用于运行 Ollama 服务）
- NVIDIA GPU（推荐，用于加速 LLM 推理，CPU 模式也可运行但较慢）
- 至少 8GB 内存
- 足够的磁盘空间（用于存储模型和文档）

## 🚀 快速开始

### 1. 克隆项目
h
git clone <repository-url>
cd second-brain### 2. 安装 Python 依赖

pip install -r requirements.txt### 3. 启动 Ollama 服务

使用 Docker Compose 启动 Ollama 服务（会自动拉取 qwen2.5:7b 模型）：

# 启动 Ollama 服务（首次启动会自动下载模型，可能需要较长时间）
docker compose up -d ollama

# 查看服务状态
docker compose ps ollama

# 查看日志
docker compose logs -f ollama**注意**：首次启动时会自动下载 qwen2.5:7b 模型（约 4.4GB），请确保网络畅通且有足够的磁盘空间。

### 4. 启动应用

#### 方式一：一键启动（推荐）

使用 `run.py` 脚本一键启动后端和前端：

python run.py该脚本会同时启动：
- FastAPI 后端服务：http://localhost:8000
- Gradio 前端界面：http://localhost:7860

按 `Ctrl+C` 可同时停止两个服务。

#### 方式二：分别启动

**启动后端服务**：

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload**启动前端界面**（新开一个终端）：

python -m app.gradio_ui或者：

python app/main.py gradio### 5. 访问服务

- **Gradio Web 界面**：http://localhost:7860（推荐使用）
- **FastAPI API 文档**：http://localhost:8000/docs
- **健康检查**：http://localhost:8000/health

## 📖 使用说明

### Web 界面使用

1. 访问 http://localhost:7860 打开 Gradio 界面
2. **上传文档**：
   - 选择 PDF 或 TXT 文件
   - 选择分块模式（chunked 推荐用于长文档，full 用于短文档）
   - 点击上传按钮
3. **文档问答**：
   - 在问答区域输入问题
   - 设置检索数量（top_k，默认 3）
   - 点击查询按钮获取答案
4. **文档管理**：
   - 查看已上传的文档列表
   - 删除不需要的文档

### API 使用示例

#### 1. 上传文档

curl -X POST "http://localhost:8000/api/upload" \
  -F "file=@document.pdf" \
  -F "chunk_mode=chunked"响应示例：
{
  "success": true,
  "document_id": "uuid-here",
  "filename": "document.pdf",
  "file_type": "pdf",
  "chunks_count": 10,
  "message": "文档上传并向量化成功"
}#### 2. 文档问答

curl -X POST "http://localhost:8000/api/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "文档的主要内容是什么？",
    "top_k": 3
  }'响应示例：
{
  "answer": "根据文档内容...",
  "relevant_chunks": [
    {
      "chunk_id": "...",
      "content": "文档片段内容...",
      "metadata": {...},
      "score": 0.95
    }
  ],
  "question": "文档的主要内容是什么？",
  "model": "qwen2.5:7b",
  "timestamp": "2026-01-05T12:00:00"
}#### 3. 列出所有文档

curl "http://localhost:8000/api/documents"
#### 4. 删除文档
h
curl -X DELETE "http://localhost:8000/api/documents/{document_id}"## ⚙️ 配置说明

配置文件：`app/config.py`

主要配置项：

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `EMBEDDING_MODEL` | 向量模型 | all-MiniLM-L6-v2 |
| `CHUNK_SIZE` | 文档分块大小（字符数） | 500 |
| `CHUNK_OVERLAP` | 分块重叠大小（字符数） | 50 |
| `OLLAMA_BASE_URL` | Ollama 服务地址 | http://localhost:11434 |
| `OLLAMA_MODEL` | 使用的 LLM 模型 | qwen2.5:7b |
| `TOP_K` | 检索返回的文档块数量 | 3 |
| `MAX_FILE_SIZE` | 最大文件大小 | 10MB |

### 环境变量配置

可通过环境变量覆盖配置：

export OLLAMA_BASE_URL=http://localhost:11434
export OLLAMA_MODEL=qwen2.5:7b
export CHUNK_SIZE=500
export CHUNK_OVERLAP=50
export TOP_K=3

## 📁 项目结构

second-brain/
├── app/                    # 应用代码
│   ├── api/               # API 路由
│   │   ├── query.py      # 问答接口
│   │   └── upload.py     # 上传接口
│   ├── config.py          # 配置管理
│   ├── document_processor.py  # 文档处理
│   ├── gradio_ui.py      # Gradio 前端界面
│   ├── models.py         # 数据模型
│   ├── rag_service.py    # RAG 服务
│   ├── vector_store.py   # 向量存储
│   └── main.py           # FastAPI 应用入口
├── data/
│   └── documents/         # 上传的文档存储
├── chroma_db/            # ChromaDB 数据目录
├── tests/                # 测试脚本
│   ├── check_chromadb.py
│   ├── check_qwen.py
│   └── check_sentence.py
├── docker-compose.yml    # Ollama 服务配置
├── requirements.txt      # Python 依赖
├── run.py               # 一键启动脚本
└── README.md            # 项目说明文档