# 智能文档向量化系统

## 项目概述

本项目实现了一个完整的智能文档向量化系统，基于gme-qwen2-vl-7b模型进行文本向量化，使用FAISS进行高效的向量存储和检索。系统支持PDF文档处理、批量向量化、相似度搜索和RAG（检索增强生成）功能。

## 系统架构

```
智能文档向量化系统
├── 文档预处理模块 (document_processor.py)
├── 向量化处理模块 (embedding_processor.py)
├── 向量存储系统 (vector_storage.py)
├── RAG流水线 (rag_pipeline.py)
├── 向量数据库管理工具 (vector_db_manager.py)
└── 配置管理 (config.py)
```

## 核心功能

### 1. 文档预处理
- **PDF文档解析**: 支持批量处理PDF文档
- **文本分块**: 智能分割长文本为适合向量化的块
- **元数据提取**: 保留文档来源、页码等信息

### 2. 向量化处理
- **gme-qwen2-vl-7b模型**: 使用先进的多模态模型进行文本向量化
- **批量处理**: 支持大规模文本的并发向量化
- **错误处理**: 完善的重试机制和异常处理

### 3. 向量存储与检索
- **FAISS索引**: 高效的向量相似度搜索
- **多种索引类型**: 支持Flat、IVFFlat、HNSW等索引
- **持久化存储**: 向量和元数据的可靠保存

### 4. RAG系统
- **完整流水线**: 从文档到检索的端到端处理
- **上下文生成**: 为查询生成相关的上下文信息
- **智能搜索**: 基于语义相似度的文档检索

### 5. 数据库管理
- **增删改查**: 完整的向量数据库管理功能
- **批量操作**: 支持批量添加和删除
- **命令行工具**: 便捷的CLI界面

## 快速开始

### 1. 环境准备

```bash
# 安装依赖
pip install -r requirements.txt

# 准备文档
# 将PDF文档放入corpus目录
mkdir corpus
# 复制PDF文件到corpus目录
```

### 2. 基本使用

#### 处理文档并构建向量数据库

```python
from rag_pipeline import RAGPipeline

# 初始化RAG流水线
rag = RAGPipeline(storage_dir="my_vector_db")

# 处理文档
success = rag.process_documents("corpus")
if success:
    print("文档处理完成！")
```

#### 搜索相关文档

```python
# 搜索相关内容
results = rag.search("心血管疾病预防", k=5)
for result in results:
    print(f"相似度: {result['score']:.4f}")
    print(f"内容: {result['text'][:100]}...")
    print("-" * 50)
```

#### 获取查询上下文

```python
# 为查询生成上下文
context = rag.get_context_for_query("如何预防心血管疾病")
print("相关上下文:")
print(context)
```

### 3. 向量数据库管理

#### 使用Python API

```python
from vector_db_manager import VectorDBManager

# 初始化管理器
manager = VectorDBManager(storage_dir="my_vector_db")

# 添加文本
manager.add_text("新的健康建议", {'source': 'manual'})

# 搜索文本
results = manager.search_texts("健康建议", k=3)

# 获取数据库信息
info = manager.get_database_info()
print(f"总向量数: {info['total_vectors']}")

# 列出文本
texts = manager.list_texts(limit=10)
```

#### 使用命令行工具

```bash
# 查看数据库信息
python vector_db_manager.py --action info

# 搜索相似文本
python vector_db_manager.py --action search --query "心血管疾病" --k 5

# 添加新文本
python vector_db_manager.py --action add --text "新的健康建议" --source manual

# 列出所有文本
python vector_db_manager.py --action list --limit 10

# 删除指定来源的文本
python vector_db_manager.py --action delete --source manual
```

## 测试验证

### 运行完整测试

```bash
# 测试向量化系统
python test_vector_system.py

# 测试数据库管理工具
python test_vector_db_manager.py
```

### 测试覆盖范围
- ✅ 向量化处理器功能测试
- ✅ 向量存储系统测试
- ✅ RAG流水线集成测试
- ✅ 数据库管理工具测试
- ✅ 搜索和检索功能测试

## 配置说明

### config.py 配置项

```python
class Config:
    # API配置
    EMBEDDING_API_URL = "https://gme-qwen2-vl-7b.ai4s.com.cn/embed/text"
    
    # 向量化配置
    VECTOR_DIMENSION = 3584
    BATCH_SIZE = 10
    MAX_WORKERS = 5
    
    # 文档处理配置
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    
    # 搜索配置
    DEFAULT_K = 5
    DEFAULT_THRESHOLD = 0.0
```

## 性能特点

### 向量化性能
- **并发处理**: 支持多线程并发向量化
- **批量优化**: 批量处理减少API调用开销
- **错误恢复**: 自动重试和错误处理机制

### 存储性能
- **FAISS优化**: 使用高效的向量索引算法
- **内存管理**: 优化的内存使用和数据结构
- **持久化**: 快速的索引保存和加载

### 搜索性能
- **亚秒级搜索**: 毫秒级的相似度搜索
- **可扩展性**: 支持大规模向量数据库
- **精确度**: 高质量的语义相似度匹配

## 项目结构

```
sais-aie-wl25/
├── config.py                    # 配置管理
├── document_processor.py         # 文档预处理模块
├── embedding_processor.py        # 向量化处理模块
├── vector_storage.py            # 向量存储系统
├── rag_pipeline.py              # RAG流水线
├── vector_db_manager.py         # 向量数据库管理工具
├── test_vector_system.py        # 系统测试脚本
├── test_vector_db_manager.py    # 管理工具测试脚本
├── corpus/                      # 文档语料库目录
├── vector_db/                   # 默认向量数据库目录
├── output/                      # 输出结果目录
└── README_向量化系统.md          # 本文档
```

## 使用场景

### 1. 文档问答系统
- 构建企业知识库
- 智能客服系统
- 技术文档检索

### 2. 内容推荐
- 相似文章推荐
- 个性化内容分发
- 知识发现

### 3. 研究分析
- 学术文献检索
- 专利分析
- 市场研究

## 扩展功能

### 支持更多文档格式
- Word文档 (.docx)
- 纯文本文件 (.txt)
- Markdown文件 (.md)
- HTML文档 (.html)

### 高级搜索功能
- 混合搜索（关键词+语义）
- 时间范围过滤
- 来源权重调整
- 多语言支持

### 性能优化
- GPU加速向量化
- 分布式存储
- 缓存机制
- 增量更新

## 故障排除

### 常见问题

1. **API连接失败**
   - 检查网络连接
   - 验证API URL配置
   - 确认API服务状态

2. **向量化失败**
   - 检查文本内容是否为空
   - 验证API响应格式
   - 查看错误日志

3. **搜索结果为空**
   - 确认向量数据库已构建
   - 检查索引文件是否存在
   - 验证查询文本格式

4. **内存不足**
   - 减少批处理大小
   - 降低并发线程数
   - 使用更高效的索引类型

### 日志调试

```python
import logging

# 启用详细日志
logging.basicConfig(level=logging.DEBUG)

# 查看特定模块日志
logger = logging.getLogger('embedding_processor')
logger.setLevel(logging.DEBUG)
```

## 贡献指南

1. Fork项目仓库
2. 创建功能分支
3. 提交代码更改
4. 运行测试验证
5. 提交Pull Request

## 许可证

本项目采用MIT许可证，详见LICENSE文件。

## 联系方式

如有问题或建议，请通过以下方式联系：
- 项目Issues: [GitHub Issues]
- 邮箱: [your-email@example.com]

---

**版本**: 1.0.0  
**更新时间**: 2025-01-12  
**作者**: SAIS AI Team