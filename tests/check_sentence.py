from sentence_transformers import SentenceTransformer

# 加载轻量级模型（首次运行会自动下载模型权重，约 80MB）
model = SentenceTransformer('all-MiniLM-L6-v2')
# 生成测试向量
embedding = model.encode("测试 Sentence Transformers 安装")
print(f"向量维度：{embedding.shape}")  # 输出 "向量维度：(384,)" 即为成功