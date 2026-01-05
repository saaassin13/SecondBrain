"""问答 API"""
from fastapi import HTTPException
from app.rag_service import RAGService
from app.models import QueryRequest, QueryResponse


# 查询处理函数，在 main.py 中直接调用
async def query_document_with_service(
    request: QueryRequest,
    rag_service: RAGService
) -> QueryResponse:
    """
    带 RAG 服务的文档查询处理函数
    
    Args:
        request: 查询请求
        rag_service: RAG 服务实例
        
    Returns:
        查询响应
    """
    try:
        answer, relevant_chunks = rag_service.query(
            question=request.question,
            top_k=request.top_k or 3
        )
        
        return QueryResponse(
            answer=answer,
            relevant_chunks=relevant_chunks,
            question=request.question,
            model=rag_service.model
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")

