#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
向量存储系统
使用FAISS进行高效的向量存储和相似度检索
"""

import faiss
import numpy as np
import json
import os
import pickle
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import time
from app.config.config import Config

class VectorStorage:
    """向量存储和检索系统"""
    
    def __init__(self, config: Optional[Config] = None, storage_dir: str = "vector_db"):
        """初始化向量存储系统
        
        Args:
            config: 配置对象
            storage_dir: 向量数据库存储目录
        """
        self.config = config or Config()
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        
        # FAISS索引
        self.index = None
        self.dimension = None
        
        # 元数据存储
        self.metadata = []  # 存储文本块的元数据
        self.id_to_chunk = {}  # ID到文本块的映射
        
        # 文件路径
        self.index_file = self.storage_dir / "faiss_index.bin"
        self.metadata_file = self.storage_dir / "metadata.json"
        self.id_mapping_file = self.storage_dir / "id_mapping.pkl"
        
        self.logger = logging.getLogger(__name__)
        
        # 设置日志
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
        
        # 尝试加载现有索引
        self.load_index()
    
    def create_index(self, dimension: int, index_type: str = "auto", nlist: int = 100) -> bool:
        """创建FAISS索引
        
        Args:
            dimension: 向量维度
            index_type: 索引类型 ("Flat", "IVFFlat", "HNSW", "auto")
            nlist: IVF索引的聚类中心数量
            
        Returns:
            创建是否成功
        """
        try:
            self.dimension = dimension
            
            if index_type == "auto":
                # 根据预期数据量自动选择索引类型
                # 对于小数据集，使用Flat索引更稳定
                index_type = "Flat"
            
            if index_type == "Flat":
                # 暴力搜索，适合小数据集
                self.index = faiss.IndexFlatIP(dimension)  # 内积相似度
            elif index_type == "IVFFlat":
                # 倒排文件索引，适合中等数据集
                quantizer = faiss.IndexFlatIP(dimension)
                self.index = faiss.IndexIVFFlat(quantizer, dimension, nlist)
            elif index_type == "HNSW":
                # 分层导航小世界图，适合大数据集
                self.index = faiss.IndexHNSWFlat(dimension, 32)
                self.index.hnsw.efConstruction = 200
                self.index.hnsw.efSearch = 100
            else:
                raise ValueError(f"不支持的索引类型: {index_type}")
            
            self.logger.info(f"成功创建{index_type}索引，维度: {dimension}")
            return True
            
        except Exception as e:
            self.logger.error(f"创建索引失败: {str(e)}")
            return False
    
    def add_vectors(self, embedded_chunks: List[Dict[str, Any]]) -> bool:
        """添加向量到索引
        
        Args:
            embedded_chunks: 包含向量的文本块列表
            
        Returns:
            添加是否成功
        """
        try:
            # 过滤出成功向量化的文本块
            valid_chunks = [chunk for chunk in embedded_chunks if chunk.get('embedding') is not None]
            
            if not valid_chunks:
                self.logger.warning("没有有效的向量数据")
                return False
            
            # 提取向量
            vectors = np.array([chunk['embedding'] for chunk in valid_chunks], dtype=np.float32)
            
            # 如果索引不存在，创建索引
            if self.index is None:
                vector_dim = vectors.shape[1]
                if not self.create_index(vector_dim):
                    return False
            
            # 训练索引（如果需要）
            if hasattr(self.index, 'is_trained') and not self.index.is_trained:
                self.logger.info("开始训练索引...")
                self.index.train(vectors)
                self.logger.info("索引训练完成")
            
            # 添加向量
            start_id = len(self.metadata)
            self.index.add(vectors)
            
            # 更新元数据
            for i, chunk in enumerate(valid_chunks):
                chunk_id = start_id + i
                metadata = {
                    'id': chunk_id,
                    'text': chunk.get('text', ''),
                    'source': chunk.get('source', ''),
                    'chunk_id': chunk.get('chunk_id', ''),
                    'page_number': chunk.get('page_number', 0),
                    'vector_dimension': len(chunk['embedding']),
                    'added_at': time.strftime('%Y-%m-%d %H:%M:%S')
                }
                self.metadata.append(metadata)
                self.id_to_chunk[chunk_id] = chunk
            
            self.logger.info(f"成功添加{len(valid_chunks)}个向量到索引")
            return True
            
        except Exception as e:
            self.logger.error(f"添加向量失败: {str(e)}")
            return False
    
    def search_similar(self, query_vector: List[float], k: int = 5, threshold: float = 0.0) -> List[Dict[str, Any]]:
        """搜索相似向量
        
        Args:
            query_vector: 查询向量
            k: 返回的相似结果数量
            threshold: 相似度阈值
            
        Returns:
            相似结果列表
        """
        if self.index is None or len(self.metadata) == 0:
            self.logger.warning("索引为空或未初始化")
            return []
        
        try:
            # 转换查询向量格式
            query_vector = np.array([query_vector], dtype=np.float32)
            
            # 执行搜索
            scores, indices = self.index.search(query_vector, k)
            
            # 处理搜索结果
            results = []
            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                if idx == -1:  # FAISS返回-1表示没有找到足够的结果
                    break
                    
                if score >= threshold:
                    result = {
                        'rank': i + 1,
                        'score': float(score),
                        'metadata': self.metadata[idx],
                        'text': self.metadata[idx]['text']
                    }
                    results.append(result)
            
            self.logger.info(f"搜索完成，找到{len(results)}个相似结果")
            return results
            
        except Exception as e:
            self.logger.error(f"搜索失败: {str(e)}")
            return []
    
    def search_by_text(self, query_text: str, embedding_processor, k: int = 5, threshold: float = 0.0) -> List[Dict[str, Any]]:
        """通过文本搜索相似内容
        
        Args:
            query_text: 查询文本
            embedding_processor: 向量化处理器
            k: 返回的相似结果数量
            threshold: 相似度阈值
            
        Returns:
            相似结果列表
        """
        # 将查询文本向量化
        query_vector = embedding_processor.embed_single_text(query_text)
        
        if query_vector is None:
            self.logger.error("查询文本向量化失败")
            return []
        
        return self.search_similar(query_vector, k, threshold)
    
    def save_index(self) -> bool:
        """保存索引和元数据到磁盘
        
        Returns:
            保存是否成功
        """
        try:
            if self.index is None:
                self.logger.warning("索引为空，无法保存")
                return False
            
            # 保存FAISS索引
            faiss.write_index(self.index, str(self.index_file))
            
            # 保存元数据
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'metadata': self.metadata,
                    'dimension': self.dimension,
                    'total_vectors': len(self.metadata),
                    'saved_at': time.strftime('%Y-%m-%d %H:%M:%S')
                }, f, ensure_ascii=False, indent=2)
            
            # 保存ID映射
            with open(self.id_mapping_file, 'wb') as f:
                pickle.dump(self.id_to_chunk, f)
            
            self.logger.info(f"索引和元数据已保存到: {self.storage_dir}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存索引失败: {str(e)}")
            return False
    
    def load_index(self) -> bool:
        """从磁盘加载索引和元数据
        
        Returns:
            加载是否成功
        """
        try:
            # 检查文件是否存在
            if not all(f.exists() for f in [self.index_file, self.metadata_file, self.id_mapping_file]):
                self.logger.warning("索引文件不完整")
                return False
            
            # 加载FAISS索引
            self.index = faiss.read_index(str(self.index_file))
            
            # 加载元数据
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.metadata = data['metadata']
                self.dimension = data['dimension']
            
            # 加载ID映射
            with open(self.id_mapping_file, 'rb') as f:
                self.id_to_chunk = pickle.load(f)
            
            self.logger.info(f"成功加载索引，包含{len(self.metadata)}个向量")
            return True
            
        except Exception as e:
            self.logger.error(f"加载索引失败: {str(e)}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """获取向量存储统计信息
        
        Returns:
            统计信息字典
        """
        stats = {
            'total_vectors': len(self.metadata),
            'dimension': self.dimension,
            'index_type': type(self.index).__name__ if self.index else None,
            'storage_size_mb': self._get_storage_size(),
            'is_trained': getattr(self.index, 'is_trained', True) if self.index else False
        }
        
        return stats
    
    def _get_storage_size(self) -> float:
        """获取存储大小（MB）"""
        total_size = 0
        for file_path in [self.index_file, self.metadata_file, self.id_mapping_file]:
            if file_path.exists():
                total_size += file_path.stat().st_size
        return total_size / (1024 * 1024)
    
    def delete_vector(self, vector_id: int) -> bool:
        """删除指定向量（注意：FAISS不支持直接删除，这里只是标记）
        
        Args:
            vector_id: 向量ID
            
        Returns:
            删除是否成功
        """
        if vector_id < 0 or vector_id >= len(self.metadata):
            self.logger.error(f"无效的向量ID: {vector_id}")
            return False
        
        # 标记为已删除
        self.metadata[vector_id]['deleted'] = True
        self.metadata[vector_id]['deleted_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
        
        self.logger.info(f"向量{vector_id}已标记为删除")
        return True
    
    def rebuild_index(self) -> bool:
        """重建索引（移除已删除的向量）
        
        Returns:
            重建是否成功
        """
        try:
            # 获取未删除的向量
            active_chunks = []
            active_metadata = []
            
            for i, metadata in enumerate(self.metadata):
                if not metadata.get('deleted', False):
                    if i in self.id_to_chunk:
                        chunk = self.id_to_chunk[i]
                        if chunk.get('embedding') is not None:
                            active_chunks.append(chunk)
                            active_metadata.append(metadata)
            
            if not active_chunks:
                self.logger.warning("没有有效的向量数据用于重建索引")
                return False
            
            # 重置索引和元数据
            self.index = None
            self.metadata = []
            self.id_to_chunk = {}
            
            # 重新添加向量
            success = self.add_vectors(active_chunks)
            
            if success:
                self.logger.info(f"索引重建完成，包含{len(active_chunks)}个向量")
            
            return success
            
        except Exception as e:
            self.logger.error(f"重建索引失败: {str(e)}")
            return False


def main():
    """主函数，用于测试向量存储功能"""
    # 创建测试向量数据
    test_chunks = [
        {
            'text': '心血管疾病是全球主要的死亡原因之一',
            'source': 'test_doc1.pdf',
            'chunk_id': 'chunk_1',
            'embedding': np.random.rand(768).tolist()  # 模拟768维向量
        },
        {
            'text': '高血压是心血管疾病的重要危险因素',
            'source': 'test_doc2.pdf', 
            'chunk_id': 'chunk_2',
            'embedding': np.random.rand(768).tolist()
        },
        {
            'text': '定期运动有助于预防心血管疾病',
            'source': 'test_doc3.pdf',
            'chunk_id': 'chunk_3', 
            'embedding': np.random.rand(768).tolist()
        }
    ]
    
    # 创建向量存储系统
    storage = VectorStorage(storage_dir="test_vector_db")
    
    # 添加向量
    print("添加测试向量...")
    success = storage.add_vectors(test_chunks)
    print(f"添加结果: {success}")
    
    # 保存索引
    print("\n保存索引...")
    success = storage.save_index()
    print(f"保存结果: {success}")
    
    # 测试搜索
    print("\n测试向量搜索...")
    query_vector = np.random.rand(768).tolist()
    results = storage.search_similar(query_vector, k=3)
    
    print(f"搜索结果数量: {len(results)}")
    for result in results:
        print(f"排名: {result['rank']}, 相似度: {result['score']:.4f}, 文本: {result['text'][:50]}...")
    
    # 获取统计信息
    print("\n存储统计信息:")
    stats = storage.get_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()