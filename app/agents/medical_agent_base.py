#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
医疗诊断Agent基类
提供通用的RAG集成接口和医疗知识检索功能
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime

from app.rag.rag_qa_system import RAGQASystem
from app.clients.deepseek_client import DeepSeekClient
from app.config.deepseek_config import get_deepseek_config, get_rag_config

class MedicalAgentBase(ABC):
    """
    医疗诊断Agent基类
    
    提供通用功能：
    - RAG系统集成
    - 医学知识检索
    - 大语言模型调用
    - 日志记录
    """
    
    def __init__(self, agent_name: str, vector_db_path: str = "rag_vector_db"):
        """
        初始化医疗Agent
        
        Args:
            agent_name: Agent名称
            vector_db_path: 向量数据库路径
        """
        self.agent_name = agent_name
        self.vector_db_path = vector_db_path
        
        # 设置日志
        self.logger = logging.getLogger(f"MedicalAgent.{agent_name}")
        self.logger.setLevel(logging.INFO)
        
        # 初始化RAG系统
        try:
            self.rag_system = RAGQASystem(vector_db_path)
            self.logger.info(f"{agent_name} RAG系统初始化成功")
        except Exception as e:
            self.logger.error(f"{agent_name} RAG系统初始化失败: {e}")
            raise
        
        # 初始化DeepSeek客户端
        try:
            config = get_deepseek_config()
            self.deepseek_client = DeepSeekClient(
                api_key=config['api_key'],
                base_url=config['base_url']
            )
            self.logger.info(f"{agent_name} DeepSeek客户端初始化成功")
        except Exception as e:
            self.logger.error(f"{agent_name} DeepSeek客户端初始化失败: {e}")
            raise
    
    def retrieve_medical_knowledge(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        检索相关医学知识
        
        Args:
            query: 查询文本
            top_k: 返回文档数量
            
        Returns:
            相关医学文档列表
        """
        try:
            self.logger.info(f"{self.agent_name} 检索医学知识: {query[:50]}...")
            
            # 使用RAG系统检索相关文档
            documents = self.rag_system.retrieve_relevant_docs(query, top_k=top_k)
            
            self.logger.info(f"{self.agent_name} 检索到 {len(documents)} 个相关文档")
            return documents
            
        except Exception as e:
            self.logger.error(f"{self.agent_name} 医学知识检索失败: {e}")
            return []
    
    def generate_response(self, prompt: str, temperature: float = 0.7, max_tokens: int = 2000) -> str:
        """
        使用大语言模型生成响应
        
        Args:
            prompt: 输入提示词
            temperature: 生成温度
            max_tokens: 最大token数
            
        Returns:
            生成的响应文本
        """
        try:
            self.logger.info(f"{self.agent_name} 生成响应，提示词长度: {len(prompt)}")
            
            messages = [{"role": "user", "content": prompt}]
            result = self.deepseek_client.chat_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            if "error" in result:
                self.logger.error(f"{self.agent_name} DeepSeek API错误: {result['error']}")
                return f"抱歉，{self.agent_name}在生成响应时遇到错误。"
            
            if "choices" in result and len(result["choices"]) > 0:
                response = result["choices"][0]["message"]["content"]
                self.logger.info(f"{self.agent_name} 响应生成成功，长度: {len(response)}")
                return response
            else:
                self.logger.error(f"{self.agent_name} DeepSeek响应格式异常")
                return f"抱歉，{self.agent_name}在生成响应时遇到错误。"
            
        except Exception as e:
            self.logger.error(f"{self.agent_name} 响应生成失败: {e}")
            return f"抱歉，{self.agent_name}在生成响应时遇到错误。"
    
    def format_medical_context(self, documents: List[Dict[str, Any]]) -> str:
        """
        格式化医学文档为上下文
        
        Args:
            documents: 医学文档列表
            
        Returns:
            格式化的上下文文本
        """
        if not documents:
            return "未找到相关医学文献。"
        
        context_parts = []
        for i, doc in enumerate(documents, 1):
            content = doc.get('content', '').strip()
            source = doc.get('source', '未知来源')
            similarity = doc.get('similarity', 0.0)
            
            context_parts.append(
                f"【参考文献 {i}】\n"
                f"来源: {source}\n"
                f"相似度: {similarity:.3f}\n"
                f"内容: {content}\n"
            )
        
        return "\n".join(context_parts)
    
    def log_interaction(self, input_data: Dict[str, Any], output_data: Dict[str, Any]):
        """
        记录交互日志
        
        Args:
            input_data: 输入数据
            output_data: 输出数据
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent_name": self.agent_name,
            "input": input_data,
            "output": output_data
        }
        
        self.logger.info(f"{self.agent_name} 交互记录: {log_entry}")
    
    @abstractmethod
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理输入数据并生成输出
        
        Args:
            input_data: 输入数据
            
        Returns:
            处理结果
        """
        pass
    
    @abstractmethod
    def get_agent_description(self) -> str:
        """
        获取Agent描述
        
        Returns:
            Agent功能描述
        """
        pass
    
    def __str__(self) -> str:
        return f"MedicalAgent({self.agent_name})"
    
    def __repr__(self) -> str:
        return self.__str__()
    
    def parse_json_response(self, response: str) -> Dict[str, Any]:
        """
        解析JSON响应
        
        Args:
            response: 模型响应字符串
            
        Returns:
            解析后的JSON对象
        """
        import json
        
        try:
            # 清理响应内容
            cleaned_response = response.strip()
            
            # 如果响应被markdown代码块包围，提取JSON部分
            if cleaned_response.startswith("```json"):
                start_idx = cleaned_response.find("```json") + 7
                end_idx = cleaned_response.rfind("```")
                if end_idx > start_idx:
                    cleaned_response = cleaned_response[start_idx:end_idx].strip()
                    self.logger.info(f"{self.agent_name} 检测到markdown格式，已提取JSON部分")
            elif cleaned_response.startswith("```"):
                start_idx = cleaned_response.find("```") + 3
                end_idx = cleaned_response.rfind("```")
                if end_idx > start_idx:
                    cleaned_response = cleaned_response[start_idx:end_idx].strip()
                    self.logger.info(f"{self.agent_name} 检测到代码块格式，已提取内容")
            
            # 尝试解析JSON
            parsed_json = json.loads(cleaned_response)
            self.logger.info(f"{self.agent_name} JSON解析成功")
            return parsed_json
            
        except json.JSONDecodeError as e:
            self.logger.error(f"{self.agent_name} JSON解析失败: {e}")
            self.logger.error(f"原始响应前200字符: {response[:200]}")
            return {"error": "JSON解析失败，返回原始响应", "raw_response": response}