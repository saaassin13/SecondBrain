"""配置管理模块"""
import os
from pathlib import Path
from typing import Literal

# 项目根目录
BASE_DIR = Path(__file__).parent.parent

# 向量模型配置
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384

# ChromaDB 配置
CHROMA_DB_PATH = BASE_DIR / "chroma_db"
COLLECTION_NAME = "knowledge_base"

# 文档存储配置
DOCUMENTS_DIR = BASE_DIR / "data" / "documents"
DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)

# Ollama 配置
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")

# 文档分块配置
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))  # 分块大小（字符数）
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))  # 重叠大小（字符数）

# 向量检索配置
TOP_K = int(os.getenv("TOP_K", "3"))  # 检索返回的文档块数量

# 文件类型
SUPPORTED_FILE_TYPES: list[Literal["pdf", "txt"]] = ["pdf", "txt"]
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

