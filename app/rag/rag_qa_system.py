#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG智能问答系统
集成DeepSeek-V3模型和向量检索，实现基于文献的智能问答
"""

import json
import time
from typing import List, Dict, Optional
from app.clients.deepseek_client import DeepSeekClient
from app.config.deepseek_config import get_deepseek_config, get_system_prompt, get_rag_config
from app.rag.vector_storage import VectorStorage
from app.rag.embedding_processor import EmbeddingProcessor

class RAGQASystem:
    def __init__(self, vector_db_path: str = "rag_vector_db"):
        """
        初始化RAG问答系统
        
        Args:
            vector_db_path: 向量数据库路径
        """
        # 初始化DeepSeek客户端
        config = get_deepseek_config()
        self.deepseek_client = DeepSeekClient(config["api_key"], config["base_url"])
        
        # 初始化向量存储
        self.vector_storage = VectorStorage(storage_dir=vector_db_path)
        
        # 初始化嵌入处理器
        self.embedding_processor = EmbeddingProcessor()
        
        # 获取RAG配置
        self.rag_config = get_rag_config()
        
        print("🚀 RAG智能问答系统初始化完成")
    
    def retrieve_relevant_docs(self, query: str, top_k: int = None) -> List[Dict]:
        """
        检索相关文档
        
        Args:
            query: 查询文本
            top_k: 返回文档数量
            
        Returns:
            相关文档列表
        """
        if top_k is None:
            top_k = self.rag_config["max_retrieved_docs"]
        
        try:
            # 对查询进行向量化
            query_vector = self.embedding_processor.embed_single_text(query)
            
            if query_vector is None:
                return []
            
            # 检索相似文档
            threshold = self.rag_config["similarity_threshold"]
            results = self.vector_storage.search_similar(query_vector, k=top_k, threshold=threshold)
            
            # 转换结果格式以匹配期望的格式
            filtered_results = []
            for result in results:
                filtered_result = {
                    "content": result["text"],
                    "source": result["metadata"].get("source", "未知来源"),
                    "similarity": result["score"],
                    "metadata": result["metadata"]
                }
                filtered_results.append(filtered_result)
            
            return filtered_results
            
        except Exception as e:
            print(f"❌ 文档检索失败: {str(e)}")
            return []
    
    def format_context(self, retrieved_docs: List[Dict]) -> str:
        """
        格式化检索到的文档作为上下文
        
        Args:
            retrieved_docs: 检索到的文档列表
            
        Returns:
            格式化的上下文文本
        """
        if not retrieved_docs:
            return "没有找到相关文档。"
        
        context_parts = []
        for i, doc in enumerate(retrieved_docs, 1):
            source = doc.get("source", "未知来源")
            content = doc.get("content", "")
            similarity = doc.get("similarity", 0)
            
            context_part = f"""文档{i} (相似度: {similarity:.3f}):
来源: {source}
内容: {content}
"""
            context_parts.append(context_part)
        
        return "\n" + "-" * 50 + "\n".join(context_parts)
    
    def generate_answer(self, question: str, context: str) -> str:
        """
        基于上下文生成答案
        
        Args:
            question: 用户问题
            context: 检索到的上下文
            
        Returns:
            生成的答案
        """
        # 构建提示词
        prompt = self.rag_config["context_template"].format(
            context=context,
            question=question
        )
        
        # 调用DeepSeek模型
        messages = [
            {
                "role": "system",
                "content": get_system_prompt("rag")
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        try:
            result = self.deepseek_client.chat_completion(messages)
            
            if "error" in result:
                return f"生成答案时出错: {result['error']}"
            
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
            else:
                return "模型响应格式异常"
                
        except Exception as e:
            return f"调用模型时出错: {str(e)}"
    
    def ask(self, question: str, show_sources: bool = True) -> Dict:
        """
        问答主接口
        
        Args:
            question: 用户问题
            show_sources: 是否显示来源信息
            
        Returns:
            包含答案和元信息的字典
        """
        print(f"\n🔍 正在处理问题: {question}")
        
        start_time = time.time()
        
        # 检索相关文档
        print("📚 检索相关文档...")
        retrieved_docs = self.retrieve_relevant_docs(question)
        
        if not retrieved_docs:
            # 如果没有找到相关文档，直接使用模型回答
            print("⚠️ 未找到相关文档，使用通用知识回答")
            answer = self.deepseek_client.simple_chat(
                question, 
                get_system_prompt("medical")
            )
            
            return {
                "question": question,
                "answer": answer,
                "sources": [],
                "retrieval_time": time.time() - start_time,
                "has_sources": False,
                "num_sources": 0
            }
        
        # 格式化上下文
        context = self.format_context(retrieved_docs)
        
        # 生成答案
        print("🤖 生成答案...")
        answer = self.generate_answer(question, context)
        
        end_time = time.time()
        
        result = {
            "question": question,
            "answer": answer,
            "sources": retrieved_docs if show_sources else [],
            "retrieval_time": end_time - start_time,
            "has_sources": True,
            "num_sources": len(retrieved_docs)
        }
        
        return result
    
    def interactive_qa(self):
        """
        交互式问答模式
        """
        print("\n" + "=" * 60)
        print("🎯 RAG智能问答系统 - 交互模式")
        print("基于心血管医学文献的智能问答")
        print("输入 'quit' 或 'exit' 退出")
        print("=" * 60)
        
        while True:
            try:
                question = input("\n❓ 请输入您的问题: ").strip()
                
                if question.lower() in ['quit', 'exit', '退出', 'q']:
                    print("👋 感谢使用RAG智能问答系统！")
                    break
                
                if not question:
                    print("⚠️ 请输入有效问题")
                    continue
                
                # 处理问题
                result = self.ask(question)
                
                # 显示结果
                print(f"\n💡 答案:")
                print(f"{result['answer']}")
                
                if result['has_sources']:
                    print(f"\n📊 检索信息:")
                    print(f"- 找到 {result['num_sources']} 个相关文档")
                    print(f"- 处理时间: {result['retrieval_time']:.2f}秒")
                    
                    if result['sources']:
                        print(f"\n📚 参考来源:")
                        for i, source in enumerate(result['sources'], 1):
                            print(f"{i}. {source.get('source', '未知来源')} (相似度: {source.get('similarity', 0):.3f})")
                
            except KeyboardInterrupt:
                print("\n👋 感谢使用RAG智能问答系统！")
                break
            except Exception as e:
                print(f"❌ 处理过程中出现错误: {str(e)}")

def main():
    """
    主函数 - 演示RAG问答系统
    """
    try:
        # 初始化系统
        qa_system = RAGQASystem()
        
        # 测试几个问题
        test_questions = [
            "什么是主动脉瓣置换术？",
            "经导管主动脉瓣置换术的适应症有哪些？",
            "心脏康复训练的主要内容是什么？"
        ]
        
        print("\n🧪 进行系统测试...")
        for question in test_questions:
            result = qa_system.ask(question, show_sources=False)
            print(f"\n❓ {question}")
            print(f"💡 {result['answer'][:200]}..." if len(result['answer']) > 200 else f"💡 {result['answer']}")
            print(f"📊 检索到 {result['num_sources']} 个相关文档，耗时 {result['retrieval_time']:.2f}秒")
        
        # 启动交互模式
        qa_system.interactive_qa()
        
    except Exception as e:
        print(f"❌ 系统初始化失败: {str(e)}")
        print("\n🔧 请检查:")
        print("1. 向量数据库是否存在")
        print("2. DeepSeek API配置是否正确")
        print("3. 网络连接是否正常")

if __name__ == "__main__":
    main()