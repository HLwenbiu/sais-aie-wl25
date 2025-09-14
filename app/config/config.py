#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件
包含文档处理、RAG系统和Multi-Agent的各种配置参数
"""

import os
from pathlib import Path

# 基础路径配置
BASE_DIR = Path(__file__).parent
CORPUS_DIR = BASE_DIR / "corpus"
MEDICAL_RECORDS_DIR = BASE_DIR / "medical_records"
OUTPUT_DIR = BASE_DIR / "output"
LOGS_DIR = BASE_DIR / "logs"

# 确保输出目录存在
OUTPUT_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# 文档处理配置
DOCUMENT_CONFIG = {
    # 文本切分配置
    "chunk_size": 1000,  # 文本块大小
    "chunk_overlap": 200,  # 文本块重叠大小
    "min_chunk_size": 100,  # 最小文本块大小
    
    # PDF处理配置
    "preferred_pdf_lib": "pdfplumber",  # 优先使用的PDF处理库
    "extract_images": False,  # 是否提取图片
    "extract_tables": True,  # 是否提取表格
    
    # 文本清理配置
    "remove_headers_footers": True,  # 是否移除页眉页脚
    "remove_references": False,  # 是否移除参考文献
    "min_sentence_length": 10,  # 最小句子长度
}

# Embedding模型配置
EMBEDDING_CONFIG = {
    "api_url": "https://gme-qwen2-vl-7b.ai4s.com.cn",
    "text_endpoint": "/embed/text",
    "image_endpoint": "/embed/image",
    "fused_endpoint": "/embed/fused",
    "timeout": 30,  # 请求超时时间（秒）
    "max_retries": 3,  # 最大重试次数
    "batch_size": 10,  # 批处理大小
}

# DeepSeek模型配置
DEEPSEEK_CONFIG = {
    "model_name": "deepseek-v3-0324",
    "api_key": os.getenv("DEEPSEEK_API_KEY", ""),  # 从环境变量获取
    "base_url": "https://api.juhenext.com",  # JuheNet API地址
    "max_tokens": 4000,
    "temperature": 0.7,
    "timeout": 60,
}

# RAG系统配置
RAG_CONFIG = {
    # 向量数据库配置
    "vector_db_type": "faiss",  # 可选: faiss, chroma
    "vector_db_path": str(OUTPUT_DIR / "vector_db"),
    "index_name": "medical_corpus",
    
    # 检索配置
    "top_k": 5,  # 检索返回的文档数量
    "similarity_threshold": 0.7,  # 相似度阈值
    "rerank": True,  # 是否重新排序
    
    # 上下文配置
    "max_context_length": 8000,  # 最大上下文长度
    "context_overlap": 100,  # 上下文重叠
}

# Multi-Agent配置
AGENT_CONFIG = {
    # Agent角色定义
    "agents": {
        "dr_hypothesis": {
            "name": "Dr.Hypothesis",
            "role": "诊断假设生成专家",
            "description": "根据患者病历信息生成初步诊断假设列表",
            "use_rag": True,
            "max_hypotheses": 5,
        },
        "dr_challenger": {
            "name": "Dr.Challenger",
            "role": "诊断质疑专家",
            "description": "对诊断假设进行分析，检查误差并提出替代诊断",
            "use_rag": True,
            "challenge_threshold": 0.6,
        },
        "dr_clinical_reasoning": {
            "name": "Dr.Clinical-Reasoning",
            "role": "临床推理专家",
            "description": "综合分析信息，生成最终诊断结果",
            "use_rag": True,
            "confidence_threshold": 0.8,
        }
    },
    
    # 协作配置
    "max_iterations": 3,  # 最大迭代次数
    "consensus_threshold": 0.8,  # 共识阈值
    "timeout_per_agent": 120,  # 每个Agent的超时时间
}

# 输出格式配置
OUTPUT_CONFIG = {
    "format": "json",
    "include_reasoning": True,  # 是否包含推理过程
    "include_confidence": True,  # 是否包含置信度
    "include_sources": True,  # 是否包含信息来源
    "language": "zh-CN",  # 输出语言
}

# 日志配置
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file_path": str(LOGS_DIR / "app.log"),
    "max_file_size": 10 * 1024 * 1024,  # 10MB
    "backup_count": 5,
}

# 性能配置
PERFORMANCE_CONFIG = {
    "max_workers": 4,  # 最大工作线程数
    "batch_processing": True,  # 是否启用批处理
    "cache_enabled": True,  # 是否启用缓存
    "cache_size": 1000,  # 缓存大小
}

class Config:
    """配置类，提供统一的配置访问接口"""
    
    def __init__(self):
        # 基础路径
        self.BASE_DIR = BASE_DIR
        self.CORPUS_DIR = CORPUS_DIR
        self.MEDICAL_RECORDS_DIR = MEDICAL_RECORDS_DIR
        self.OUTPUT_DIR = OUTPUT_DIR
        self.LOGS_DIR = LOGS_DIR
        
        # 各模块配置
        self.DOCUMENT_CONFIG = DOCUMENT_CONFIG
        self.EMBEDDING_CONFIG = EMBEDDING_CONFIG
        self.DEEPSEEK_CONFIG = DEEPSEEK_CONFIG
        self.RAG_CONFIG = RAG_CONFIG
        self.AGENT_CONFIG = AGENT_CONFIG
        self.OUTPUT_CONFIG = OUTPUT_CONFIG
        self.LOGGING_CONFIG = LOGGING_CONFIG
        self.PERFORMANCE_CONFIG = PERFORMANCE_CONFIG
    
    def get_document_config(self):
        """获取文档处理配置"""
        return self.DOCUMENT_CONFIG
    
    def get_embedding_config(self):
        """获取embedding配置"""
        return self.EMBEDDING_CONFIG
    
    def get_rag_config(self):
        """获取RAG配置"""
        return self.RAG_CONFIG
    
    def validate(self):
        """验证配置的有效性"""
        return validate_config()

# 验证配置
def validate_config():
    """
    验证配置的有效性
    """
    errors = []
    
    # 检查必要的目录
    if not CORPUS_DIR.exists():
        errors.append(f"Corpus目录不存在: {CORPUS_DIR}")
    
    if not MEDICAL_RECORDS_DIR.exists():
        errors.append(f"Medical records目录不存在: {MEDICAL_RECORDS_DIR}")
    
    # 检查API密钥
    if not DEEPSEEK_CONFIG["api_key"]:
        errors.append("DeepSeek API密钥未设置，请设置环境变量 DEEPSEEK_API_KEY")
    
    # 检查文本块配置
    if DOCUMENT_CONFIG["chunk_size"] <= DOCUMENT_CONFIG["chunk_overlap"]:
        errors.append("chunk_size 必须大于 chunk_overlap")
    
    if errors:
        raise ValueError("配置验证失败:\n" + "\n".join(errors))
    
    return True

if __name__ == "__main__":
    try:
        validate_config()
        print("配置验证通过")
    except ValueError as e:
        print(f"配置错误: {e}")