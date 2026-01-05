"""数据模型定义"""
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime


class UploadResponse(BaseModel):
    """文档上传响应"""
    success: bool
    document_id: str
    filename: str
    file_type: Literal["pdf", "txt"]
    chunks_count: int
    message: str


class QueryRequest(BaseModel):
    """查询请求"""
    question: str = Field(..., description="用户问题", min_length=1)
    top_k: Optional[int] = Field(default=3, description="检索的文档块数量", ge=1, le=10)
    chunk_mode: Optional[Literal["chunked", "full"]] = Field(
        default="chunked", description="文档处理模式"
    )


class DocumentChunk(BaseModel):
    """文档块信息"""
    chunk_id: str
    content: str
    metadata: dict
    score: Optional[float] = None


class QueryResponse(BaseModel):
    """查询响应"""
    answer: str
    relevant_chunks: List[DocumentChunk]
    question: str
    model: str
    timestamp: datetime = Field(default_factory=datetime.now)


class DocumentInfo(BaseModel):
    """文档信息"""
    document_id: str
    filename: str
    file_type: str
    upload_time: datetime
    chunks_count: int

