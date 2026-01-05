"""RAG 问答服务模块"""
import requests
from typing import List, Dict, Any
from app.config import OLLAMA_BASE_URL, OLLAMA_MODEL, TOP_K
from app.vector_store import VectorStore
from app.models import DocumentChunk


class RAGService:
    """RAG 问答服务类"""
    
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        self.ollama_url = f"{OLLAMA_BASE_URL}/api/generate"
        self.model = OLLAMA_MODEL
    
    def _build_prompt(self, question: str, context_chunks: List[Dict[str, Any]]) -> str:
        """
        构建 RAG prompt
        
        Args:
            question: 用户问题
            context_chunks: 检索到的文档块列表
            
        Returns:
            构建的 prompt
        """
        context_text = "\n\n".join([
            f"[文档片段 {i+1}]\n{chunk['document']}"
            for i, chunk in enumerate(context_chunks)
        ])
        
        prompt = f"""基于以下文档内容回答问题。如果文档中没有相关信息，请说明无法从文档中找到答案。

文档内容：
{context_text}

问题：{question}

请基于上述文档内容回答问题："""
        
        return prompt
    
    def _call_ollama(self, prompt: str) -> str:
        """
        调用 Ollama API 生成回答
        
        Args:
            prompt: 输入 prompt
            
        Returns:
            生成的回答
        """
        try:
            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=60
            )
            response.raise_for_status()
            result = response.json()
            return result.get("response", "抱歉，无法生成回答。")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Ollama API 调用失败: {str(e)}")
    
    def query(
        self,
        question: str,
        top_k: int = TOP_K
    ) -> tuple[str, List[DocumentChunk]]:
        """
        执行 RAG 查询
        
        Args:
            question: 用户问题
            top_k: 检索的文档块数量
            
        Returns:
            (答案, 相关文档块列表) 元组
        """
        # 1. 向量检索
        search_results = self.vector_store.search(query=question, n_results=top_k)
        
        # 2. 处理检索结果
        if not search_results.get("documents") or not search_results["documents"][0]:
            return "抱歉，未找到相关文档内容。", []
        
        # 构建文档块列表
        context_chunks = []
        relevant_chunks = []
        
        documents = search_results["documents"][0]
        metadatas = search_results.get("metadatas", [[]])[0]
        distances = search_results.get("distances", [[]])[0]
        ids = search_results.get("ids", [[]])[0]
        
        for i in range(len(documents)):
            chunk_data = {
                "document": documents[i],
                "metadata": metadatas[i] if i < len(metadatas) else {},
                "distance": distances[i] if i < len(distances) else None,
                "id": ids[i] if i < len(ids) else ""
            }
            context_chunks.append(chunk_data)
            
            # 构建 DocumentChunk 对象
            relevant_chunks.append(DocumentChunk(
                chunk_id=chunk_data["id"],
                content=chunk_data["document"],
                metadata=chunk_data["metadata"],
                score=1.0 - chunk_data["distance"] if chunk_data["distance"] is not None else None
            ))
        
        # 3. 构建 prompt
        prompt = self._build_prompt(question, context_chunks)
        
        # 4. 调用 Ollama 生成回答
        answer = self._call_ollama(prompt)
        
        return answer, relevant_chunks

