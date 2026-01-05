"""FastAPI 应用主入口"""
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Literal

from app.config import COLLECTION_NAME
from app.vector_store import VectorStore
from app.rag_service import RAGService
from app.api.upload import upload_document_with_store
from app.api.query import query_document_with_service
from app.models import UploadResponse, QueryRequest, QueryResponse

# 全局服务实例
vector_store: VectorStore = None
rag_service: RAGService = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global vector_store, rag_service
    
    # 启动时初始化
    print("正在初始化向量存储...")
    vector_store = VectorStore()
    vector_store.initialize()
    print(f"向量存储初始化完成，集合: {COLLECTION_NAME}")
    print(f"当前文档数量: {vector_store.get_collection_count()}")
    
    # 初始化 RAG 服务
    print("正在初始化 RAG 服务...")
    rag_service = RAGService(vector_store)
    print("RAG 服务初始化完成")
    
    yield
    
    # 关闭时清理（如果需要）


# 创建 FastAPI 应用
app = FastAPI(
    title="个人知识库后端",
    description="基于 FastAPI + ChromaDB + Ollama 的 RAG 知识库系统",
    version="1.0.0",
    lifespan=lifespan
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应设置具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "个人知识库后端 API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    global vector_store, rag_service
    
    if vector_store is None or rag_service is None:
        return {"status": "error", "message": "服务未初始化"}
    
    try:
        doc_count = vector_store.get_collection_count()
        return {
            "status": "healthy",
            "vector_store": "ok",
            "rag_service": "ok",
            "document_count": doc_count
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/api/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    chunk_mode: Literal["chunked", "full"] = Form(default="chunked")
):
    """
    上传文档接口
    
    - **file**: 上传的文件（PDF 或 TXT）
    - **chunk_mode**: 文档处理模式
      - `chunked`: 分块处理（推荐，适合长文档）
      - `full`: 整篇文档作为一个向量
    """
    global vector_store
    
    if vector_store is None:
        raise HTTPException(status_code=503, detail="向量存储服务未初始化")
    
    return await upload_document_with_store(file, chunk_mode, vector_store)


@app.post("/api/query", response_model=QueryResponse)
async def query_document(request: QueryRequest):
    """
    文档问答接口
    
    - **question**: 用户问题
    - **top_k**: 检索的文档块数量（默认 3）
    - **chunk_mode**: 文档处理模式（已弃用，保留兼容性）
    """
    global rag_service
    
    if rag_service is None:
        raise HTTPException(status_code=503, detail="RAG 服务未初始化")
    
    return await query_document_with_service(request, rag_service)


@app.get("/api/documents")
async def list_documents(limit: int = 100):
    """
    列出所有文档
    
    - **limit**: 返回数量限制（默认 100）
    """
    global vector_store
    
    if vector_store is None:
        raise HTTPException(status_code=503, detail="向量存储服务未初始化")
    
    try:
        documents = vector_store.list_documents(limit=limit)
        return {
            "success": True,
            "count": len(documents),
            "documents": documents
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文档列表失败: {str(e)}")


@app.delete("/api/documents/{document_id}")
async def delete_document(document_id: str):
    """
    删除文档
    
    - **document_id**: 文档 ID
    """
    global vector_store
    
    if vector_store is None:
        raise HTTPException(status_code=503, detail="向量存储服务未初始化")
    
    try:
        # 删除所有相关的文档块
        success = vector_store.delete_documents_by_filter(
            {"document_id": document_id}
        )
        
        if success:
            return {"success": True, "message": f"文档 {document_id} 已删除"}
        else:
            raise HTTPException(status_code=404, detail="文档未找到")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除文档失败: {str(e)}")


# 在文件末尾添加
if __name__ == "__main__":
    import sys
    import uvicorn
    import threading
    
    # 检查命令行参数
    if len(sys.argv) > 1 and sys.argv[1] == "gradio":
        # 启动 Gradio 界面
        from app.gradio_ui import create_interface
        demo = create_interface()
        demo.launch(
            server_name="0.0.0.0",
            server_port=7860,
            share=False
        )
    else:
        # 启动 FastAPI 服务
        uvicorn.run(app, host="0.0.0.0", port=8000)

