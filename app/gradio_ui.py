"""Gradio 前端界面"""
import gradio as gr
import requests
import json
from typing import List, Tuple, Optional
from datetime import datetime

# 后端 API 地址
API_BASE_URL = "http://localhost:8000"


def upload_file(file, chunk_mode: str) -> str:
    """
    上传文件到后端
    
    Args:
        file: 上传的文件对象
        chunk_mode: 分块模式 ("chunked" 或 "full")
    
    Returns:
        上传结果消息
    """
    if file is None:
        return "❌ 请选择要上传的文件"
    
    try:
        with open(file.name, "rb") as f:
            files = {"file": (file.name, f, "application/octet-stream")}
            data = {"chunk_mode": chunk_mode}
            
            response = requests.post(
                f"{API_BASE_URL}/api/upload",
                files=files,
                data=data,
                timeout=300
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get("success"):
                return f"""✅ 上传成功！

📄 文件名: {result['filename']}
🆔 文档ID: {result['document_id']}
📦 分块数量: {result['chunks_count']}
💬 {result['message']}"""
            else:
                return f"❌ 上传失败: {result.get('message', '未知错误')}"
    except requests.exceptions.RequestException as e:
        return f"❌ 上传失败: {str(e)}"
    except Exception as e:
        return f"❌ 发生错误: {str(e)}"


def query_document(question: str, top_k: int) -> Tuple[str, str]:
    """
    查询文档
    
    Args:
        question: 用户问题
        top_k: 检索的文档块数量
    
    Returns:
        (答案, 相关文档块信息) 元组
    """
    if not question or not question.strip():
        return "❌ 请输入问题", ""
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/query",
            json={
                "question": question,
                "top_k": top_k
            },
            timeout=120
        )
        response.raise_for_status()
        result = response.json()
        
        # 格式化答案
        answer = f"""**问题:** {result['question']}

**回答:**
{result['answer']}

---
*模型: {result['model']} | 时间: {result['timestamp']}*"""
        
        # 格式化相关文档块
        chunks_info = ""
        if result.get("relevant_chunks"):
            chunks_info = "**相关文档片段:**\n\n"
            for i, chunk in enumerate(result["relevant_chunks"], 1):
                metadata = chunk.get("metadata", {})
                filename = metadata.get("filename", "未知文件")
                score = chunk.get("score")
                score_str = f" (相似度: {score:.2f})" if score else ""
                
                chunks_info += f"""**片段 {i}** - {filename}{score_str}"""
        
        return answer, chunks_info
    except requests.exceptions.RequestException as e:
        return f"❌ 查询失败: {str(e)}", ""
    except Exception as e:
        return f"❌ 发生错误: {str(e)}", ""


def get_documents(page: int = 1, page_size: int = 10) -> Tuple[str, List[Tuple[str, str]]]:
    """
    获取文档列表（分页）
    
    Args:
        page: 页码（从1开始）
        page_size: 每页数量
    
    Returns:
        (文档列表HTML, 文档选择列表) 元组
    """
    try:
        # 获取所有文档（后端暂时只支持 limit，我们做客户端分页）
        response = requests.get(
            f"{API_BASE_URL}/api/documents",
            params={"limit": 1000},  # 获取足够多的文档
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        
        if not result.get("success"):
            return "❌ 获取文档列表失败", []
        
        documents = result.get("documents", [])
        
        # 按文档ID分组（因为一个文档可能有多个chunk）
        doc_dict = {}
        for doc in documents:
            metadata = doc.get("metadata", {})
            doc_id = metadata.get("document_id")
            if doc_id:
                if doc_id not in doc_dict:
                    doc_dict[doc_id] = {
                        "filename": metadata.get("filename", "未知"),
                        "file_type": metadata.get("file_type", "未知"),
                        "upload_time": metadata.get("upload_time", ""),
                        "chunks": []
                    }
                doc_dict[doc_id]["chunks"].append(doc)
        
        # 转换为列表并排序
        doc_list = [
            {
                "document_id": doc_id,
                "filename": info["filename"],
                "file_type": info["file_type"],
                "upload_time": info["upload_time"],
                "chunks_count": len(info["chunks"])
            }
            for doc_id, info in doc_dict.items()
        ]
        
        # 按上传时间倒序排序
        doc_list.sort(key=lambda x: x["upload_time"], reverse=True)
        
        total = len(doc_list)
        total_pages = (total + page_size - 1) // page_size
        
        # 分页
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_docs = doc_list[start_idx:end_idx]
        
        # 生成HTML表格
        html = f"""
        <div style="margin-bottom: 10px;">
            <strong>共 {total} 个文档 | 第 {page}/{total_pages} 页</strong>
        </div>
        <table style="width: 100%; border-collapse: collapse;">
            <thead>
                <tr style="background-color: #f0f0f0;">
                    <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">文件名</th>
                    <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">类型</th>
                    <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">分块数</th>
                    <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">上传时间</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for doc in page_docs:
            upload_time = doc["upload_time"][:19] if doc["upload_time"] else "未知"
            html += f"""
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;">{doc['filename']}</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{doc['file_type'].upper()}</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{doc['chunks_count']}</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{upload_time}</td>
                </tr>
            """
        
        html += """
            </tbody>
        </table>
        """
        
        # 生成文档选择列表（用于删除）
        doc_choices = [
            (f"{doc['filename']} ({doc['document_id'][:8]}...)", doc['document_id'])
            for doc in page_docs
        ]
        
        return html, doc_choices
    except requests.exceptions.RequestException as e:
        return f"❌ 获取文档列表失败: {str(e)}", []
    except Exception as e:
        return f"❌ 发生错误: {str(e)}", []


def delete_document(document_id: str) -> str:
    """
    删除文档
    
    Args:
        document_id: 文档ID
    
    Returns:
        删除结果消息
    """
    if not document_id:
        return "❌ 请选择要删除的文档"
    
    try:
        response = requests.delete(
            f"{API_BASE_URL}/api/documents/{document_id}",
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        
        if result.get("success"):
            return f"✅ {result.get('message', '删除成功')}"
        else:
            return f"❌ 删除失败: {result.get('message', '未知错误')}"
    except requests.exceptions.RequestException as e:
        return f"❌ 删除失败: {str(e)}"
    except Exception as e:
        return f"❌ 发生错误: {str(e)}"


def refresh_documents(page: int) -> Tuple[str, List[Tuple[str, str]], int]:
    """刷新文档列表"""
    html, choices = get_documents(page, page_size=10)
    return html, choices, page


# 创建 Gradio 界面
def create_interface():
    """创建 Gradio 界面"""
    
    with gr.Blocks(title="个人知识库", theme=gr.themes.Soft()) as demo:
        gr.Markdown(
            """
            # 📚 个人知识库系统
            
            基于 RAG（检索增强生成）的智能文档问答系统
            """
        )
        
        with gr.Tabs():
            # Tab 1: 文档上传
            with gr.Tab("📤 上传文档"):
                gr.Markdown("### 上传 PDF 或 TXT 文档到知识库")
                
                with gr.Row():
                    file_input = gr.File(
                        label="选择文件",
                        file_types=[".pdf", ".txt"]
                    )
                    chunk_mode = gr.Radio(
                        choices=["chunked", "full"],
                        value="chunked",
                        label="处理模式",
                        info="chunked: 分块处理（推荐）| full: 整篇文档"
                    )
                
                upload_btn = gr.Button("上传文档", variant="primary")
                upload_output = gr.Textbox(
                    label="上传结果",
                    lines=6,
                    interactive=False
                )
                
                upload_btn.click(
                    fn=upload_file,
                    inputs=[file_input, chunk_mode],
                    outputs=upload_output
                )
            
            # Tab 2: 文档问答
            with gr.Tab("💬 文档问答"):
                gr.Markdown("### 基于知识库的智能问答")
                
                with gr.Row():
                    question_input = gr.Textbox(
                        label="输入问题",
                        placeholder="例如：文档的主要内容是什么？",
                        lines=3
                    )
                
                with gr.Row():
                    top_k = gr.Slider(
                        minimum=1,
                        maximum=10,
                        value=3,
                        step=1,
                        label="检索文档块数量"
                    )
                    query_btn = gr.Button("查询", variant="primary")
                
                answer_output = gr.Markdown(label="回答")
                chunks_output = gr.Markdown(label="相关文档片段")
                
                query_btn.click(
                    fn=query_document,
                    inputs=[question_input, top_k],
                    outputs=[answer_output, chunks_output]
                )
            
            # Tab 3: 文档管理
            with gr.Tab("📋 文档管理"):
                gr.Markdown("### 文档列表和管理")
                
                with gr.Row():
                    page_input = gr.Number(
                        value=1,
                        minimum=1,
                        label="页码",
                        precision=0
                    )
                    refresh_btn = gr.Button("刷新列表", variant="secondary")
                
                docs_html = gr.HTML(label="文档列表")
                doc_choices = gr.Dropdown(
                    label="选择要删除的文档",
                    choices=[],
                    interactive=True
                )
                
                with gr.Row():
                    delete_btn = gr.Button("删除文档", variant="stop")
                    delete_output = gr.Textbox(
                        label="删除结果",
                        lines=2,
                        interactive=False
                    )
                
                # 初始化加载文档列表
                demo.load(
                    fn=lambda: get_documents(1, 10),
                    outputs=[docs_html, doc_choices]
                )
                
                # 刷新按钮
                refresh_btn.click(
                    fn=refresh_documents,
                    inputs=[page_input],
                    outputs=[docs_html, doc_choices, page_input]
                )
                
                # 页码变化时刷新
                page_input.submit(
                    fn=refresh_documents,
                    inputs=[page_input],
                    outputs=[docs_html, doc_choices, page_input]
                )
                
                # 删除按钮
                delete_btn.click(
                    fn=delete_document,
                    inputs=[doc_choices],
                    outputs=delete_output
                ).then(
                    fn=lambda: refresh_documents(1),
                    outputs=[docs_html, doc_choices, page_input]
                )
        
        # 页脚
        gr.Markdown(
            """
            ---
            **提示:** 确保后端服务运行在 http://localhost:8000
            """
        )
    
    return demo


if __name__ == "__main__":
    demo = create_interface()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )