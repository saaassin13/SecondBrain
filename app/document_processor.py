"""文档处理模块"""
import re
from pathlib import Path
from typing import List, Dict, Literal, Tuple
from pypdf import PdfReader


def process_pdf(file_path: Path) -> str:
    """
    提取 PDF 文件的文本内容
    
    Args:
        file_path: PDF 文件路径
        
    Returns:
        提取的文本内容
    """
    try:
        reader = PdfReader(file_path)
        text_parts = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
        return "\n\n".join(text_parts)
    except Exception as e:
        raise ValueError(f"PDF 处理失败: {str(e)}")


def process_txt(file_path: Path) -> str:
    """
    读取 TXT 文件的文本内容
    
    Args:
        file_path: TXT 文件路径
        
    Returns:
        文件文本内容
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        # 尝试其他编码
        with open(file_path, "r", encoding="gbk") as f:
            return f.read()


def chunk_text(
    text: str, 
    chunk_size: int = 500, 
    overlap: int = 50
) -> List[Tuple[str, int]]:
    """
    将文本分块，支持重叠窗口
    
    Args:
        text: 原始文本
        chunk_size: 分块大小（字符数）
        overlap: 重叠大小（字符数）
        
    Returns:
        分块列表，每个元素为 (chunk_text, start_index) 元组
    """
    if not text:
        return []
    
    # 清理文本：移除多余空白
    text = re.sub(r'\s+', ' ', text.strip())
    
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end]
        
        if chunk:
            chunks.append((chunk, start))
        
        # 移动到下一个块的起始位置（考虑重叠）
        start = end - overlap
        
        # 避免无限循环
        if start >= text_length:
            break
    
    return chunks


def process_document(
    file_path: Path,
    file_type: Literal["pdf", "txt"],
    chunk_mode: Literal["chunked", "full"] = "chunked",
    chunk_size: int = 500,
    overlap: int = 50
) -> Tuple[str, List[Tuple[str, int]]]:
    """
    统一处理文档入口
    
    Args:
        file_path: 文件路径
        file_type: 文件类型
        chunk_mode: 分块模式 ("chunked" 或 "full")
        chunk_size: 分块大小
        overlap: 重叠大小
        
    Returns:
        (原始文本, 分块列表) 元组
    """
    # 提取文本
    if file_type == "pdf":
        text = process_pdf(file_path)
    elif file_type == "txt":
        text = process_txt(file_path)
    else:
        raise ValueError(f"不支持的文件类型: {file_type}")
    
    # 分块处理
    if chunk_mode == "full":
        chunks = [(text, 0)]
    else:
        chunks = chunk_text(text, chunk_size, overlap)
    
    return text, chunks

