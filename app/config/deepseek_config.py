import os

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepSeek-V3模型配置文件
"""

# DeepSeek API配置
# 优先从环境变量读取，如果未设置，则使用配置文件中的默认值
# 这种做法有助于保护敏感信息，尤其是在容器化部署时
DEEPSEEK_CONFIG = {
    "api_key": os.getenv("DEEPSEEK_API_KEY", "sk-SJMOKPd1pimn8dAZnBJaInh7JkyQKviyGR26eEWqO2cn9Jgw"),
    "base_url": os.getenv("BASE_URL", "https://api.juheai.top/v1"),
    "model_name": "deepseek-v3-0324",
    "default_temperature": 0.7,
    "max_tokens": 2048,
    "timeout": 60,
    "connect_timeout": 10,
    "read_timeout": 60,
    "max_retries": 3
}

# 模型参数配置
MODEL_PARAMS = {
    "temperature": 0.7,  # 控制输出的随机性
    "top_p": 0.9,       # 核采样参数
    "max_tokens": 2048,  # 最大输出token数
    "presence_penalty": 0.0,  # 存在惩罚
    "frequency_penalty": 0.0  # 频率惩罚
}

# 系统提示词配置
SYSTEM_PROMPTS = {
    "default": "You are a helpful assistant.",
    "medical": "你是一个专业的医学AI助手，具备丰富的医学知识，能够基于提供的医学文献回答问题。请确保回答准确、专业，并在适当时提醒用户咨询专业医生。",
    "rag": "你是一个智能文档问答助手。请基于提供的文档内容回答用户问题，如果文档中没有相关信息，请明确说明。回答要准确、简洁，并引用相关的文档片段。"
}

# RAG集成配置
RAG_INTEGRATION = {
    "enable_rag": True,
    "max_context_length": 4000,  # 最大上下文长度
    "similarity_threshold": 0.3,  # 相似度阈值
    "max_retrieved_docs": 3,     # 最大检索文档数
    "context_template": """基于以下文档内容回答问题：

{context}

问题：{question}

请基于上述文档内容回答问题，如果文档中没有相关信息，请说明。"""
}

def get_deepseek_config():
    """获取DeepSeek配置"""
    return DEEPSEEK_CONFIG

def get_model_params():
    """获取模型参数"""
    return MODEL_PARAMS

def get_system_prompt(prompt_type="default"):
    """获取系统提示词"""
    return SYSTEM_PROMPTS.get(prompt_type, SYSTEM_PROMPTS["default"])

def get_rag_config():
    """获取RAG配置"""
    return RAG_INTEGRATION