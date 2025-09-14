#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG系统完整流水线
集成文档预处理、向量化和存储功能
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import time

from app.rag.document_processor import DocumentProcessor
from app.rag.embedding_processor import EmbeddingProcessor
from app.rag.vector_storage import VectorStorage
from app.config.config import Config

class RAGPipeline:
    """RAG系统完整流水线"""
    
    def __init__(self, config: Optional[Config] = None, storage_dir: str = "vector_db"):
        """初始化RAG流水线
        
        Args:
            config: 配置对象
            storage_dir: 向量数据库存储目录
        """
        self.config = config or Config()
        self.storage_dir = storage_dir
        
        # 初始化各个组件
        self.doc_processor = DocumentProcessor("corpus", self.config)
        self.embedding_processor = EmbeddingProcessor(self.config)
        self.vector_storage = VectorStorage(self.config, storage_dir)
        
        # 设置日志
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def process_documents(self, corpus_dir: str, force_reprocess: bool = False) -> bool:
        """处理文档并构建向量数据库
        
        Args:
            corpus_dir: 文档语料库目录
            force_reprocess: 是否强制重新处理
            
        Returns:
            处理是否成功
        """
        try:
            self.logger.info("开始RAG流水线处理...")
            
            # 检查是否已存在向量数据库
            if not force_reprocess and self.vector_storage.load_index():
                self.logger.info("发现已存在的向量数据库，跳过处理")
                return True
            
            # 步骤1: 文档预处理
            self.logger.info("步骤1: 开始文档预处理...")
            # 更新文档处理器的语料库路径
            from pathlib import Path
            self.doc_processor.corpus_path = Path(corpus_dir)
            processing_results = self.doc_processor.process_all_pdfs()
            
            # 从处理结果中提取文本块
            text_chunks = []
            for result in processing_results:
                if result['success']:
                    # 为每个文本块添加元数据
                    for chunk in result['chunks']:
                        text_chunks.append({
                            'text': chunk,
                            'source': result['file_name'],
                            'file_path': result['file_path']
                        })
            
            if not text_chunks:
                self.logger.error("文档预处理失败，没有提取到文本块")
                return False
            
            self.logger.info(f"文档预处理完成，共提取{len(text_chunks)}个文本块")
            
            # 步骤2: 文本向量化
            self.logger.info("步骤2: 开始文本向量化...")
            embedded_chunks = self.embedding_processor.embed_text_chunks(text_chunks)
            
            if not embedded_chunks:
                self.logger.error("文本向量化失败")
                return False
            
            # 统计向量化结果
            successful_embeddings = sum(1 for chunk in embedded_chunks if chunk.get('embedding') is not None)
            self.logger.info(f"文本向量化完成，成功: {successful_embeddings}/{len(embedded_chunks)}")
            
            # 步骤3: 构建向量存储
            self.logger.info("步骤3: 开始构建向量存储...")
            success = self.vector_storage.add_vectors(embedded_chunks)
            
            if not success:
                self.logger.error("构建向量存储失败")
                return False
            
            # 步骤4: 保存向量数据库
            self.logger.info("步骤4: 保存向量数据库...")
            success = self.vector_storage.save_index()
            
            if not success:
                self.logger.error("保存向量数据库失败")
                return False
            
            # 保存处理结果摘要
            self._save_processing_summary(embedded_chunks)
            
            self.logger.info("RAG流水线处理完成！")
            return True
            
        except Exception as e:
            self.logger.error(f"RAG流水线处理失败: {str(e)}")
            return False
    
    def search(self, query: str, k: int = 5, threshold: float = 0.0) -> List[Dict[str, Any]]:
        """搜索相关文档
        
        Args:
            query: 查询文本
            k: 返回结果数量
            threshold: 相似度阈值
            
        Returns:
            搜索结果列表
        """
        try:
            # 确保向量数据库已加载
            if self.vector_storage.index is None:
                if not self.vector_storage.load_index():
                    self.logger.error("无法加载向量数据库")
                    return []
            
            # 执行搜索
            results = self.vector_storage.search_by_text(
                query, self.embedding_processor, k, threshold
            )
            
            self.logger.info(f"搜索查询: '{query}', 找到{len(results)}个结果")
            return results
            
        except Exception as e:
            self.logger.error(f"搜索失败: {str(e)}")
            return []
    
    def get_context_for_query(self, query: str, max_context_length: int = 2000) -> str:
        """为查询获取上下文文本
        
        Args:
            query: 查询文本
            max_context_length: 最大上下文长度
            
        Returns:
            上下文文本
        """
        # 搜索相关文档
        search_results = self.search(query, k=5)
        
        if not search_results:
            return ""
        
        # 构建上下文
        context_parts = []
        current_length = 0
        
        for result in search_results:
            text = result.get('text', '')
            metadata = result.get('metadata', {})
            source = metadata.get('source', 'unknown')
            
            # 添加来源信息
            context_part = f"[来源: {source}]\n{text}\n"
            
            if current_length + len(context_part) > max_context_length:
                # 如果当前部分太长，尝试截断文本
                remaining_length = max_context_length - current_length - len(f"[来源: {source}]\n\n")
                if remaining_length > 50:  # 至少保留50个字符
                    truncated_text = text[:remaining_length] + "..."
                    context_part = f"[来源: {source}]\n{truncated_text}\n"
                    context_parts.append(context_part)
                break
            
            context_parts.append(context_part)
            current_length += len(context_part)
        
        return "\n".join(context_parts)
    
    def get_pipeline_stats(self) -> Dict[str, Any]:
        """获取流水线统计信息
        
        Returns:
            统计信息字典
        """
        stats = {
            'vector_storage': self.vector_storage.get_stats(),
            'embedding_processor': {
                'api_url': self.embedding_processor.api_url
            },
            'document_processor': {
                'supported_formats': ['pdf']
            }
        }
        
        return stats
    
    def _save_processing_summary(self, embedded_chunks: List[Dict[str, Any]]) -> None:
        """保存处理摘要
        
        Args:
            embedded_chunks: 向量化后的文本块列表
        """
        try:
            # 统计信息
            total_chunks = len(embedded_chunks)
            successful_embeddings = sum(1 for chunk in embedded_chunks if chunk.get('embedding') is not None)
            
            # 按来源统计
            source_stats = {}
            for chunk in embedded_chunks:
                source = chunk.get('source', 'unknown')
                if source not in source_stats:
                    source_stats[source] = {'total': 0, 'successful': 0}
                source_stats[source]['total'] += 1
                if chunk.get('embedding') is not None:
                    source_stats[source]['successful'] += 1
            
            # 创建摘要
            summary = {
                'processing_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                'total_chunks': total_chunks,
                'successful_embeddings': successful_embeddings,
                'success_rate': successful_embeddings / total_chunks * 100 if total_chunks > 0 else 0,
                'vector_dimension': embedded_chunks[0].get('vector_dimension', 0) if embedded_chunks else 0,
                'source_statistics': source_stats,
                'pipeline_config': {
                    'storage_dir': self.storage_dir,
                    'embedding_api': self.embedding_processor.api_url
                }
            }
            
            # 保存摘要
            summary_file = Path(self.storage_dir) / "processing_summary.json"
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"处理摘要已保存到: {summary_file}")
            
        except Exception as e:
            self.logger.error(f"保存处理摘要失败: {str(e)}")
    
    def load_processing_summary(self) -> Optional[Dict[str, Any]]:
        """加载处理摘要
        
        Returns:
            处理摘要字典，失败时返回None
        """
        try:
            summary_file = Path(self.storage_dir) / "processing_summary.json"
            if not summary_file.exists():
                return None
            
            with open(summary_file, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            self.logger.error(f"加载处理摘要失败: {str(e)}")
            return None
    
    def rebuild_database(self, corpus_dir: str) -> bool:
        """重建向量数据库
        
        Args:
            corpus_dir: 文档语料库目录
            
        Returns:
            重建是否成功
        """
        self.logger.info("开始重建向量数据库...")
        return self.process_documents(corpus_dir, force_reprocess=True)
    
    def add_documents(self, pdf_files: List[str]) -> bool:
        """添加新文档到现有数据库
        
        Args:
            pdf_files: PDF文件路径列表
            
        Returns:
            添加是否成功
        """
        try:
            # 确保向量数据库已加载
            if self.vector_storage.index is None:
                if not self.vector_storage.load_index():
                    self.logger.error("无法加载现有向量数据库")
                    return False
            
            # 处理新文档
            all_chunks = []
            for pdf_file in pdf_files:
                chunks = self.doc_processor.process_single_pdf(pdf_file)
                all_chunks.extend(chunks)
            
            if not all_chunks:
                self.logger.warning("没有从新文档中提取到文本块")
                return True
            
            # 向量化
            embedded_chunks = self.embedding_processor.embed_text_chunks(all_chunks)
            
            # 添加到向量存储
            success = self.vector_storage.add_vectors(embedded_chunks)
            
            if success:
                # 保存更新后的索引
                success = self.vector_storage.save_index()
            
            if success:
                self.logger.info(f"成功添加{len(pdf_files)}个新文档")
            
            return success
            
        except Exception as e:
            self.logger.error(f"添加新文档失败: {str(e)}")
            return False


def main():
    """主函数，演示RAG流水线的使用"""
    # 创建RAG流水线
    pipeline = RAGPipeline(storage_dir="rag_vector_db")
    
    # 处理文档
    corpus_dir = "corpus"
    if os.path.exists(corpus_dir):
        print("开始处理文档...")
        success = pipeline.process_documents(corpus_dir)
        print(f"文档处理结果: {success}")
        
        if success:
            # 获取统计信息
            print("\n流水线统计信息:")
            stats = pipeline.get_pipeline_stats()
            print(json.dumps(stats, indent=2, ensure_ascii=False))
            
            # 测试搜索
            print("\n测试搜索功能:")
            test_queries = [
                "心血管疾病的治疗方法",
                "高血压的预防措施",
                "主动脉瓣置换术"
            ]
            
            for query in test_queries:
                print(f"\n查询: {query}")
                results = pipeline.search(query, k=3)
                
                for i, result in enumerate(results, 1):
                    print(f"{i}. 相似度: {result['score']:.4f}")
                    print(f"   来源: {result['metadata']['source']}")
                    print(f"   内容: {result['text'][:100]}...")
    else:
        print(f"语料库目录不存在: {corpus_dir}")


if __name__ == "__main__":
    main()