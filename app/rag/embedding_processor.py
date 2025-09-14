#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
嵌入处理器
负责文档的向量化处理和相似度计算
"""

import os
import json
import logging
import numpy as np
import requests
import time
from typing import List, Dict, Any, Optional, Tuple
from sentence_transformers import SentenceTransformer
import faiss
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.config.config import Config

class EmbeddingProcessor:
    """文本向量化处理器"""
    
    def __init__(self, config: Optional[Config] = None):
        """初始化向量化处理器
        
        Args:
            config: 配置对象，如果为None则使用默认配置
        """
        self.config = config or Config()
        self.api_url = "https://gme-qwen2-vl-7b.ai4s.com.cn/embed/text"
        self.headers = {
            "Content-Type": "application/json"
        }
        self.logger = logging.getLogger(__name__)
        
        # 设置日志
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def embed_single_text(self, text: str, max_retries: int = 3) -> Optional[List[float]]:
        """对单个文本进行向量化
        
        Args:
            text: 待向量化的文本
            max_retries: 最大重试次数
            
        Returns:
            向量列表，失败时返回None
        """
        if not text or not text.strip():
            self.logger.warning("输入文本为空")
            return None
            
        payload = {
            "texts": [text.strip()]
        }
        
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self.api_url,
                    headers=self.headers,
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    # 处理不同的API响应格式
                    if isinstance(result, dict) and 'embeddings' in result:
                        # 格式: {"embeddings": [[vector1], [vector2], ...]}
                        embeddings = result['embeddings']
                        if isinstance(embeddings, list) and len(embeddings) > 0:
                            return embeddings[0]
                    elif isinstance(result, list) and len(result) > 0:
                        # 格式: [[vector1], [vector2], ...]
                        return result[0]
                    elif isinstance(result, dict) and 'data' in result:
                        # 格式: {"data": [{"embedding": [vector1]}, ...]}
                        data = result['data']
                        if isinstance(data, list) and len(data) > 0 and 'embedding' in data[0]:
                            return data[0]['embedding']
                    else:
                        self.logger.error(f"API返回格式异常: {result}")
                        return None
                else:
                    self.logger.error(f"API请求失败，状态码: {response.status_code}, 响应: {response.text}")
                    
            except requests.exceptions.RequestException as e:
                self.logger.error(f"请求异常 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # 指数退避
                    
        return None
    
    def embed_batch_texts(self, texts: List[str], batch_size: int = 10, max_workers: int = 5) -> List[Tuple[str, Optional[List[float]]]]:
        """批量文本向量化
        
        Args:
            texts: 文本列表
            batch_size: 每批处理的文本数量
            max_workers: 最大并发线程数
            
        Returns:
            (文本, 向量)元组列表
        """
        if not texts:
            return []
            
        results = []
        total_texts = len(texts)
        
        self.logger.info(f"开始批量向量化处理，共{total_texts}个文本")
        
        # 分批处理
        for i in range(0, total_texts, batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_results = []
            
            # 使用线程池并发处理
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_text = {executor.submit(self.embed_single_text, text): text for text in batch_texts}
                
                for future in as_completed(future_to_text):
                    text = future_to_text[future]
                    try:
                        vector = future.result()
                        batch_results.append((text, vector))
                    except Exception as e:
                        self.logger.error(f"处理文本时出错: {str(e)}")
                        batch_results.append((text, None))
            
            results.extend(batch_results)
            
            # 进度日志
            processed = min(i + batch_size, total_texts)
            self.logger.info(f"已处理 {processed}/{total_texts} 个文本")
            
            # 批次间休息，避免API限流
            if i + batch_size < total_texts:
                time.sleep(1)
        
        # 统计结果
        successful = sum(1 for _, vector in results if vector is not None)
        self.logger.info(f"批量向量化完成，成功: {successful}/{total_texts}")
        
        return results
    
    def embed_text_chunks(self, text_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """对文本块进行向量化处理
        
        Args:
            text_chunks: 文本块列表，每个元素包含text、source、chunk_id等字段
            
        Returns:
            包含向量信息的文本块列表
        """
        if not text_chunks:
            return []
            
        self.logger.info(f"开始对{len(text_chunks)}个文本块进行向量化")
        
        # 提取文本内容
        texts = [chunk.get('text', '') for chunk in text_chunks]
        
        # 批量向量化
        embedding_results = self.embed_batch_texts(texts)
        
        # 将向量结果合并到文本块中
        enhanced_chunks = []
        for i, (chunk, (text, vector)) in enumerate(zip(text_chunks, embedding_results)):
            enhanced_chunk = chunk.copy()
            enhanced_chunk['embedding'] = vector
            enhanced_chunk['embedding_status'] = 'success' if vector is not None else 'failed'
            enhanced_chunk['vector_dimension'] = len(vector) if vector else 0
            enhanced_chunks.append(enhanced_chunk)
        
        # 统计结果
        successful_embeddings = sum(1 for chunk in enhanced_chunks if chunk['embedding'] is not None)
        self.logger.info(f"文本块向量化完成，成功: {successful_embeddings}/{len(text_chunks)}")
        
        return enhanced_chunks
    
    def save_embeddings(self, embedded_chunks: List[Dict[str, Any]], output_path: str) -> bool:
        """保存向量化结果
        
        Args:
            embedded_chunks: 包含向量的文本块列表
            output_path: 输出文件路径
            
        Returns:
            保存是否成功
        """
        try:
            # 准备保存的数据
            save_data = {
                'metadata': {
                    'total_chunks': len(embedded_chunks),
                    'successful_embeddings': sum(1 for chunk in embedded_chunks if chunk.get('embedding') is not None),
                    'vector_dimension': embedded_chunks[0].get('vector_dimension', 0) if embedded_chunks else 0,
                    'created_at': time.strftime('%Y-%m-%d %H:%M:%S')
                },
                'chunks': embedded_chunks
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"向量化结果已保存到: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存向量化结果失败: {str(e)}")
            return False
    
    def load_embeddings(self, input_path: str) -> Optional[List[Dict[str, Any]]]:
        """加载向量化结果
        
        Args:
            input_path: 输入文件路径
            
        Returns:
            文本块列表，失败时返回None
        """
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if 'chunks' in data:
                self.logger.info(f"成功加载{len(data['chunks'])}个向量化文本块")
                return data['chunks']
            else:
                self.logger.error("文件格式错误，缺少chunks字段")
                return None
                
        except Exception as e:
            self.logger.error(f"加载向量化结果失败: {str(e)}")
            return None
    
    def get_embedding_stats(self, embedded_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """获取向量化统计信息
        
        Args:
            embedded_chunks: 包含向量的文本块列表
            
        Returns:
            统计信息字典
        """
        if not embedded_chunks:
            return {}
            
        successful_chunks = [chunk for chunk in embedded_chunks if chunk.get('embedding') is not None]
        
        stats = {
            'total_chunks': len(embedded_chunks),
            'successful_embeddings': len(successful_chunks),
            'failed_embeddings': len(embedded_chunks) - len(successful_chunks),
            'success_rate': len(successful_chunks) / len(embedded_chunks) * 100 if embedded_chunks else 0,
            'vector_dimension': successful_chunks[0].get('vector_dimension', 0) if successful_chunks else 0,
            'avg_text_length': np.mean([len(chunk.get('text', '')) for chunk in embedded_chunks]) if embedded_chunks else 0
        }
        
        return stats


def main():
    """主函数，用于测试向量化功能"""
    processor = EmbeddingProcessor()
    
    # 测试单个文本向量化
    test_text = "这是一个测试文本，用于验证向量化功能。"
    vector = processor.embed_single_text(test_text)
    
    if vector:
        print(f"单个文本向量化成功，向量维度: {len(vector)}")
        print(f"向量前5个元素: {vector[:5]}")
    else:
        print("单个文本向量化失败")
    
    # 测试批量文本向量化
    test_texts = [
        "医学文献中的重要发现",
        "心血管疾病的治疗方法",
        "临床试验的统计分析"
    ]
    
    batch_results = processor.embed_batch_texts(test_texts)
    print(f"\n批量向量化结果: {len(batch_results)}个文本")
    
    for text, vector in batch_results:
        if vector:
            print(f"文本: {text[:20]}... -> 向量维度: {len(vector)}")
        else:
            print(f"文本: {text[:20]}... -> 向量化失败")


if __name__ == "__main__":
    main()