"""文档上传 API"""
import uuid
from pathlib import Path
from datetime import datetime
from fastapi import UploadFile, HTTPException
from typing import Literal

from app.config import (
    DOCUMENTS_DIR,
    SUPPORTED_FILE_TYPES,
    MAX_FILE_SIZE,
    CHUNK_SIZE,
    CHUNK_OVERLAP
)
from app.document_processor import process_document
from app.vector_store import VectorStore
from app.models import UploadResponse

def get_file_type(filename: str) -> Literal["pdf", "txt"]:
    """根据文件名获取文件类型"""
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        return "pdf"
    elif ext == ".txt":
        return "txt"
    else:
        raise ValueError(f"不支持的文件类型: {ext}")


# 上传处理函数，在 main.py 中直接调用
async def upload_document_with_store(
    file: UploadFile,
    chunk_mode: Literal["chunked", "full"],
    vector_store: VectorStore
) -> UploadResponse:
    """
    带向量存储的文档上传处理函数
    
    Args:
        file: 上传的文件
        chunk_mode: 文档处理模式
        vector_store: 向量存储实例
        
    Returns:
        上传结果
    """
    # 1. 验证文件类型
    try:
        file_type = get_file_type(file.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    if file_type not in SUPPORTED_FILE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型，仅支持: {', '.join(SUPPORTED_FILE_TYPES)}"
        )
    
    # 2. 验证文件大小
    file_content = await file.read()
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"文件大小超过限制 ({MAX_FILE_SIZE / 1024 / 1024}MB)"
        )
    
    # 3. 保存文件
    document_id = str(uuid.uuid4())
    file_extension = Path(file.filename).suffix
    saved_filename = f"{document_id}{file_extension}"
    saved_path = DOCUMENTS_DIR / saved_filename
    
    try:
        with open(saved_path, "wb") as f:
            f.write(file_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")
    
    # 4. 处理文档
    try:
        text, chunks = process_document(
            file_path=saved_path,
            file_type=file_type,
            chunk_mode=chunk_mode,
            chunk_size=CHUNK_SIZE,
            overlap=CHUNK_OVERLAP
        )
    except Exception as e:
        saved_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"文档处理失败: {str(e)}")
    
    # 5. 生成向量并存储
    try:
        documents = [chunk[0] for chunk in chunks]
        metadata_list = [
            {
                "document_id": document_id,
                "filename": file.filename,
                "file_type": file_type,
                "chunk_index": i,
                "chunk_start": chunk[1],
                "upload_time": datetime.now().isoformat()
            }
            for i, chunk in enumerate(chunks)
        ]
        chunk_ids = [f"{document_id}_chunk_{i}" for i in range(len(chunks))]
        
        vector_store.add_documents(
            documents=documents,
            metadata=metadata_list,
            ids=chunk_ids
        )
        
        return UploadResponse(
            success=True,
            document_id=document_id,
            filename=file.filename,
            file_type=file_type,
            chunks_count=len(chunks),
            message="文档上传并向量化成功"
        )
    except Exception as e:
        saved_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"向量存储失败: {str(e)}")

