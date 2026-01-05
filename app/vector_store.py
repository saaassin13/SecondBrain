"""向量存储模块"""
import uuid
from pathlib import Path
from typing import List, Dict, Optional, Any
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from app.config import (
    CHROMA_DB_PATH,
    COLLECTION_NAME,
    EMBEDDING_MODEL,
    EMBEDDING_DIMENSION
)


class VectorStore:
    """ChromaDB 向量存储管理类"""
    
    def __init__(self):
        self.client: Optional[chromadb.Client] = None
        self.collection: Optional[chromadb.Collection] = None
        self.embedding_model: Optional[SentenceTransformer] = None
    
    def initialize(self):
        """初始化 ChromaDB 客户端和集合"""
        # 初始化嵌入模型
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        
        # 初始化 ChromaDB 客户端（持久化）
        self.client = chromadb.PersistentClient(
            path=str(CHROMA_DB_PATH),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # 获取或创建集合
        try:
            self.collection = self.client.get_collection(name=COLLECTION_NAME)
        except Exception:
            # 集合不存在，创建新集合
            self.collection = self.client.create_collection(
                name=COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"}
            )
    
    def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """生成文本向量"""
        if not self.embedding_model:
            raise RuntimeError("嵌入模型未初始化")
        embeddings = self.embedding_model.encode(texts, show_progress_bar=False)
        return embeddings.tolist()
    
    def add_documents(
        self,
        documents: List[str],
        metadata: List[Dict[str, Any]],
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        添加文档到向量存储
        
        Args:
            documents: 文档文本列表
            metadata: 元数据列表
            ids: 文档 ID 列表（可选，自动生成）
            
        Returns:
            文档 ID 列表
        """
        if not self.collection:
            raise RuntimeError("集合未初始化，请先调用 initialize()")
        
        if not documents:
            return []
        
        # 生成向量
        embeddings = self._generate_embeddings(documents)
        
        # 生成 ID
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in documents]
        
        # 添加到集合
        self.collection.add(
            embeddings=embeddings,
            documents=documents,
            metadatas=metadata,
            ids=ids
        )
        
        return ids
    
    def search(
        self,
        query: str,
        n_results: int = 3,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        向量检索
        
        Args:
            query: 查询文本
            n_results: 返回结果数量
            filter_dict: 过滤条件
            
        Returns:
            检索结果字典，包含 documents, metadatas, distances, ids
        """
        if not self.collection:
            raise RuntimeError("集合未初始化，请先调用 initialize()")
        
        # 生成查询向量
        query_embedding = self._generate_embeddings([query])[0]
        
        # 执行检索
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=filter_dict
        )
        
        return results
    
    def delete_document(self, document_id: str) -> bool:
        """
        删除文档
        
        Args:
            document_id: 文档 ID
            
        Returns:
            是否删除成功
        """
        if not self.collection:
            raise RuntimeError("集合未初始化，请先调用 initialize()")
        
        try:
            self.collection.delete(ids=[document_id])
            return True
        except Exception:
            return False
    
    def delete_documents_by_filter(self, filter_dict: Dict[str, Any]) -> bool:
        """
        根据过滤条件删除文档
        
        Args:
            filter_dict: 过滤条件
            
        Returns:
            是否删除成功
        """
        if not self.collection:
            raise RuntimeError("集合未初始化，请先调用 initialize()")
        
        try:
            self.collection.delete(where=filter_dict)
            return True
        except Exception:
            return False
    
    def list_documents(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        列出所有文档
        
        Args:
            limit: 返回数量限制
            
        Returns:
            文档信息列表
        """
        if not self.collection:
            raise RuntimeError("集合未初始化，请先调用 initialize()")
        
        try:
            results = self.collection.get(limit=limit)
            documents = []
            for i in range(len(results["ids"])):
                documents.append({
                    "id": results["ids"][i],
                    "document": results["documents"][i],
                    "metadata": results["metadatas"][i]
                })
            return documents
        except Exception as e:
            return []
    
    def get_collection_count(self) -> int:
        """获取集合中的文档数量"""
        if not self.collection:
            return 0
        try:
            return self.collection.count()
        except Exception:
            return 0

