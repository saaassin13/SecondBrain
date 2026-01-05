import chromadb

# 初始化内存客户端（无需持久化）
client = chromadb.Client()
# 创建集合
collection = client.create_collection(name="test_collection")
# 添加测试数据
collection.add(
    documents=["ChromaDB 安装成功"],
    ids=["id1"]
)
# 检索数据
results = collection.query(query_texts=["测试"], n_results=1)
print("检索结果：", results["documents"])  # 输出 ['ChromaDB 安装成功'] 即为成功