#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
向量数据库管理工具
提供向量数据库的增删改查操作
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import time
from datetime import datetime

from vector_storage import VectorStorage
from embedding_processor import EmbeddingProcessor
from config import Config

class VectorDBManager:
    """向量数据库管理器"""
    
    def __init__(self, config: Optional[Config] = None, storage_dir: str = "vector_db"):
        """初始化向量数据库管理器
        
        Args:
            config: 配置对象
            storage_dir: 向量数据库存储目录
        """
        self.config = config or Config()
        self.storage_dir = storage_dir
        
        # 初始化组件
        self.vector_storage = VectorStorage(self.config, storage_dir)
        self.embedding_processor = EmbeddingProcessor(self.config)
        
        # 设置日志
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def create_database(self, dimension: int = 3584, index_type: str = "Flat") -> bool:
        """创建新的向量数据库
        
        Args:
            dimension: 向量维度
            index_type: 索引类型
            
        Returns:
            创建是否成功
        """
        try:
            success = self.vector_storage.create_index(dimension, index_type)
            if success:
                self.logger.info(f"成功创建向量数据库，维度: {dimension}, 索引类型: {index_type}")
            return success
        except Exception as e:
            self.logger.error(f"创建数据库失败: {str(e)}")
            return False
    
    def add_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """添加单个文本到数据库
        
        Args:
            text: 文本内容
            metadata: 元数据
            
        Returns:
            添加是否成功
        """
        try:
            # 向量化文本
            vector = self.embedding_processor.embed_single_text(text)
            if vector is None:
                self.logger.error("文本向量化失败")
                return False
            
            # 准备文本块数据
            chunk_data = {
                'text': text,
                'embedding': vector,
                'source': metadata.get('source', 'manual_input') if metadata else 'manual_input',
                'chunk_id': metadata.get('chunk_id', f'manual_{int(time.time())}') if metadata else f'manual_{int(time.time())}',
                'page_number': metadata.get('page_number', 0) if metadata else 0
            }
            
            # 添加到向量存储
            success = self.vector_storage.add_vectors([chunk_data])
            if success:
                self.logger.info("成功添加文本到数据库")
            return success
            
        except Exception as e:
            self.logger.error(f"添加文本失败: {str(e)}")
            return False
    
    def add_texts_batch(self, texts: List[str], metadata_list: Optional[List[Dict[str, Any]]] = None) -> bool:
        """批量添加文本到数据库
        
        Args:
            texts: 文本列表
            metadata_list: 元数据列表
            
        Returns:
            添加是否成功
        """
        try:
            if not texts:
                return True
            
            # 批量向量化
            embedding_results = self.embedding_processor.embed_batch_texts(texts)
            
            # 准备文本块数据
            chunks_data = []
            for i, (text, vector) in enumerate(embedding_results):
                if vector is not None:
                    metadata = metadata_list[i] if metadata_list and i < len(metadata_list) else {}
                    chunk_data = {
                        'text': text,
                        'embedding': vector,
                        'source': metadata.get('source', 'batch_input'),
                        'chunk_id': metadata.get('chunk_id', f'batch_{int(time.time())}_{i}'),
                        'page_number': metadata.get('page_number', 0)
                    }
                    chunks_data.append(chunk_data)
            
            # 添加到向量存储
            if chunks_data:
                success = self.vector_storage.add_vectors(chunks_data)
                if success:
                    self.logger.info(f"成功批量添加{len(chunks_data)}个文本到数据库")
                return success
            else:
                self.logger.warning("没有成功向量化的文本")
                return False
                
        except Exception as e:
            self.logger.error(f"批量添加文本失败: {str(e)}")
            return False
    
    def search_texts(self, query: str, k: int = 5, threshold: float = 0.0) -> List[Dict[str, Any]]:
        """搜索相似文本
        
        Args:
            query: 查询文本
            k: 返回结果数量
            threshold: 相似度阈值
            
        Returns:
            搜索结果列表
        """
        try:
            # 确保数据库已加载
            if self.vector_storage.index is None:
                if not self.vector_storage.load_index():
                    self.logger.error("无法加载向量数据库")
                    return []
            
            # 执行搜索
            results = self.vector_storage.search_by_text(query, self.embedding_processor, k, threshold)
            self.logger.info(f"搜索查询: '{query}', 找到{len(results)}个结果")
            return results
            
        except Exception as e:
            self.logger.error(f"搜索失败: {str(e)}")
            return []
    
    def delete_by_source(self, source: str) -> bool:
        """根据来源删除文本
        
        Args:
            source: 来源标识
            
        Returns:
            删除是否成功
        """
        try:
            # 找到匹配的索引
            indices_to_remove = []
            for i, metadata in enumerate(self.vector_storage.metadata):
                if metadata.get('source') == source:
                    indices_to_remove.append(i)
            
            if not indices_to_remove:
                self.logger.warning(f"未找到来源为'{source}'的文本")
                return False
            
            # 重建索引（FAISS不支持直接删除，需要重建）
            success = self._rebuild_index_without_indices(indices_to_remove)
            if success:
                self.logger.info(f"成功删除来源为'{source}'的{len(indices_to_remove)}个文本")
            return success
            
        except Exception as e:
            self.logger.error(f"删除失败: {str(e)}")
            return False
    
    def delete_by_ids(self, ids: List[int]) -> bool:
        """根据ID删除文本
        
        Args:
            ids: ID列表
            
        Returns:
            删除是否成功
        """
        try:
            # 验证ID
            valid_ids = [id for id in ids if 0 <= id < len(self.vector_storage.metadata)]
            if not valid_ids:
                self.logger.warning("没有有效的ID")
                return False
            
            # 重建索引
            success = self._rebuild_index_without_indices(valid_ids)
            if success:
                self.logger.info(f"成功删除{len(valid_ids)}个文本")
            return success
            
        except Exception as e:
            self.logger.error(f"删除失败: {str(e)}")
            return False
    
    def update_metadata(self, id: int, new_metadata: Dict[str, Any]) -> bool:
        """更新文本元数据
        
        Args:
            id: 文本ID
            new_metadata: 新的元数据
            
        Returns:
            更新是否成功
        """
        try:
            if not (0 <= id < len(self.vector_storage.metadata)):
                self.logger.error(f"无效的ID: {id}")
                return False
            
            # 更新元数据
            old_metadata = self.vector_storage.metadata[id]
            for key, value in new_metadata.items():
                old_metadata[key] = value
            old_metadata['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            self.logger.info(f"成功更新ID {id} 的元数据")
            return True
            
        except Exception as e:
            self.logger.error(f"更新元数据失败: {str(e)}")
            return False
    
    def get_database_info(self) -> Dict[str, Any]:
        """获取数据库信息
        
        Returns:
            数据库信息字典
        """
        try:
            # 确保数据库已加载
            if self.vector_storage.index is None:
                if not self.vector_storage.load_index():
                    return {'error': '无法加载向量数据库'}
            
            info = {
                'total_vectors': self.vector_storage.index.ntotal if self.vector_storage.index else 0,
                'dimension': self.vector_storage.dimension,
                'index_type': type(self.vector_storage.index).__name__ if self.vector_storage.index else 'None',
                'metadata_count': len(self.vector_storage.metadata),
                'storage_dir': str(self.vector_storage.storage_dir),
                'files': {
                    'index_exists': self.vector_storage.index_file.exists(),
                    'metadata_exists': self.vector_storage.metadata_file.exists(),
                    'id_mapping_exists': self.vector_storage.id_mapping_file.exists()
                }
            }
            
            # 统计来源信息
            sources = {}
            for metadata in self.vector_storage.metadata:
                source = metadata.get('source', 'unknown')
                sources[source] = sources.get(source, 0) + 1
            info['sources'] = sources
            
            return info
            
        except Exception as e:
            self.logger.error(f"获取数据库信息失败: {str(e)}")
            return {'error': str(e)}
    
    def list_texts(self, limit: int = 10, offset: int = 0, source_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出文本
        
        Args:
            limit: 返回数量限制
            offset: 偏移量
            source_filter: 来源过滤
            
        Returns:
            文本列表
        """
        try:
            # 确保数据库已加载
            if self.vector_storage.index is None:
                if not self.vector_storage.load_index():
                    return []
            
            # 过滤和分页
            filtered_metadata = []
            for i, metadata in enumerate(self.vector_storage.metadata):
                if source_filter is None or metadata.get('source') == source_filter:
                    metadata_copy = metadata.copy()
                    metadata_copy['index'] = i
                    # 截断长文本
                    if len(metadata_copy.get('text', '')) > 200:
                        metadata_copy['text'] = metadata_copy['text'][:200] + '...'
                    filtered_metadata.append(metadata_copy)
            
            # 应用分页
            start = offset
            end = offset + limit
            return filtered_metadata[start:end]
            
        except Exception as e:
            self.logger.error(f"列出文本失败: {str(e)}")
            return []
    
    def save_database(self) -> bool:
        """保存数据库
        
        Returns:
            保存是否成功
        """
        try:
            success = self.vector_storage.save_index()
            if success:
                self.logger.info("数据库保存成功")
            return success
        except Exception as e:
            self.logger.error(f"保存数据库失败: {str(e)}")
            return False
    
    def load_database(self) -> bool:
        """加载数据库
        
        Returns:
            加载是否成功
        """
        try:
            success = self.vector_storage.load_index()
            if success:
                self.logger.info("数据库加载成功")
            return success
        except Exception as e:
            self.logger.error(f"加载数据库失败: {str(e)}")
            return False
    
    def _rebuild_index_without_indices(self, indices_to_remove: List[int]) -> bool:
        """重建索引，排除指定的索引
        
        Args:
            indices_to_remove: 要移除的索引列表
            
        Returns:
            重建是否成功
        """
        try:
            # 获取要保留的数据
            kept_metadata = []
            kept_chunks = []
            
            for i, metadata in enumerate(self.vector_storage.metadata):
                if i not in indices_to_remove:
                    kept_metadata.append(metadata)
                    if i in self.vector_storage.id_to_chunk:
                        kept_chunks.append(self.vector_storage.id_to_chunk[i])
            
            if not kept_chunks:
                # 如果没有数据保留，创建空索引
                self.vector_storage.index = None
                self.vector_storage.metadata = []
                self.vector_storage.id_to_chunk = {}
                return True
            
            # 重新创建索引
            dimension = self.vector_storage.dimension
            self.vector_storage.create_index(dimension)
            
            # 重新添加保留的数据
            self.vector_storage.metadata = []
            self.vector_storage.id_to_chunk = {}
            success = self.vector_storage.add_vectors(kept_chunks)
            
            return success
            
        except Exception as e:
            self.logger.error(f"重建索引失败: {str(e)}")
            return False


def main():
    """命令行界面示例"""
    import argparse
    
    parser = argparse.ArgumentParser(description='向量数据库管理工具')
    parser.add_argument('--storage-dir', default='vector_db', help='数据库存储目录')
    parser.add_argument('--action', choices=['info', 'list', 'search', 'add', 'delete'], 
                       required=True, help='操作类型')
    parser.add_argument('--query', help='搜索查询')
    parser.add_argument('--text', help='要添加的文本')
    parser.add_argument('--source', help='来源标识')
    parser.add_argument('--limit', type=int, default=10, help='列表限制')
    parser.add_argument('--k', type=int, default=5, help='搜索结果数量')
    
    args = parser.parse_args()
    
    # 初始化管理器
    manager = VectorDBManager(storage_dir=args.storage_dir)
    
    if args.action == 'info':
        info = manager.get_database_info()
        print(json.dumps(info, indent=2, ensure_ascii=False))
    
    elif args.action == 'list':
        texts = manager.list_texts(limit=args.limit, source_filter=args.source)
        for text in texts:
            print(f"ID: {text['index']}, 来源: {text.get('source', 'unknown')}")
            print(f"文本: {text.get('text', '')[:100]}...")
            print("-" * 50)
    
    elif args.action == 'search':
        if not args.query:
            print("搜索需要提供 --query 参数")
            return
        results = manager.search_texts(args.query, k=args.k)
        for i, result in enumerate(results):
            print(f"结果 {i+1} (相似度: {result['score']:.4f}):")
            print(f"来源: {result['metadata'].get('source', 'unknown')}")
            print(f"文本: {result['text'][:200]}...")
            print("-" * 50)
    
    elif args.action == 'add':
        if not args.text:
            print("添加文本需要提供 --text 参数")
            return
        metadata = {'source': args.source} if args.source else None
        success = manager.add_text(args.text, metadata)
        if success:
            print("文本添加成功")
            manager.save_database()
        else:
            print("文本添加失败")
    
    elif args.action == 'delete':
        if not args.source:
            print("删除需要提供 --source 参数")
            return
        success = manager.delete_by_source(args.source)
        if success:
            print(f"成功删除来源为'{args.source}'的文本")
            manager.save_database()
        else:
            print("删除失败")


if __name__ == '__main__':
    main()