#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepSeek API客户端
提供与DeepSeek API的交互功能
"""

import json
import logging
import requests
import time
from typing import Dict, List, Any, Optional

from app.config.deepseek_config import get_deepseek_config

class DeepSeekClient:
    def __init__(self, api_key: str, base_url: str = "https://api.juheai.top/v1"):
        """
        初始化DeepSeek客户端
        
        Args:
            api_key: API密钥
            base_url: API基础URL
        """
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        # 加载配置
        self.config = get_deepseek_config()
        self.timeout = self.config.get('timeout', 60)
        self.connect_timeout = self.config.get('connect_timeout', 10)
        self.read_timeout = self.config.get('read_timeout', 60)
        self.max_retries = self.config.get('max_retries', 3)
    
    def chat_completion(self, 
                       messages: List[Dict[str, str]], 
                       model: str = "deepseek-v3-0324",
                       temperature: float = 0.7,
                       max_tokens: Optional[int] = None) -> Dict:
        """
        调用聊天完成API
        
        Args:
            messages: 消息列表
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数
            
        Returns:
            API响应结果
        """
        url = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        # 设置超时参数
        timeout_config = (self.connect_timeout, self.read_timeout)
        
        # 重试机制
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    url, 
                    headers=self.headers, 
                    json=payload, 
                    timeout=timeout_config
                )
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.Timeout as e:
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt  # 指数退避
                    print(f"请求超时，{wait_time}秒后重试... (尝试 {attempt + 1}/{self.max_retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    return {"error": f"请求超时，已重试{self.max_retries}次: {str(e)}"}
                    
            except requests.exceptions.ConnectionError as e:
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"连接错误，{wait_time}秒后重试... (尝试 {attempt + 1}/{self.max_retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    return {"error": f"连接失败，已重试{self.max_retries}次: {str(e)}"}
                    
            except requests.exceptions.RequestException as e:
                return {"error": f"请求失败: {str(e)}"}
                
            except json.JSONDecodeError as e:
                return {"error": f"JSON解析失败: {str(e)}"}
        
        return {"error": "未知错误，所有重试都失败了"}
    
    def test_connection(self) -> bool:
        """
        测试API连接
        
        Returns:
            连接是否成功
        """
        print("🔍 正在测试DeepSeek-V3模型连接...")
        
        test_messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant."
            },
            {
                "role": "user",
                "content": "你好，请简单介绍一下你自己。"
            }
        ]
        
        start_time = time.time()
        result = self.chat_completion(test_messages)
        end_time = time.time()
        
        if "error" in result:
            print(f"❌ 连接失败: {result['error']}")
            return False
        
        if "choices" in result and len(result["choices"]) > 0:
            response_text = result["choices"][0]["message"]["content"]
            print(f"✅ 连接成功!")
            print(f"📊 响应时间: {end_time - start_time:.2f}秒")
            print(f"🤖 模型响应: {response_text[:100]}..." if len(response_text) > 100 else f"🤖 模型响应: {response_text}")
            
            # 显示详细信息
            if "usage" in result:
                usage = result["usage"]
                print(f"📈 Token使用情况:")
                print(f"   - 输入tokens: {usage.get('prompt_tokens', 'N/A')}")
                print(f"   - 输出tokens: {usage.get('completion_tokens', 'N/A')}")
                print(f"   - 总tokens: {usage.get('total_tokens', 'N/A')}")
            
            return True
        else:
            print(f"❌ 响应格式异常: {result}")
            return False
    
    def simple_chat(self, user_message: str, system_message: str = "You are a helpful assistant.") -> str:
        """
        简单聊天接口
        
        Args:
            user_message: 用户消息
            system_message: 系统消息
            
        Returns:
            模型回复
        """
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
        
        result = self.chat_completion(messages)
        
        if "error" in result:
            return f"错误: {result['error']}"
        
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        else:
            return "响应格式异常"

def main():
    """
    主函数 - 测试DeepSeek模型连接
    """
    # API配置
    API_KEY = "sk-SJMOKPd1pimn8dAZnBJaInh7JkyQKviyGR26eEWqO2cn9Jgw"
    
    print("=" * 50)
    print("🚀 DeepSeek-V3模型连接测试")
    print("=" * 50)
    
    # 创建客户端
    client = DeepSeekClient(API_KEY)
    
    # 测试连接
    success = client.test_connection()
    
    if success:
        print("\n" + "=" * 50)
        print("🎉 测试成功! DeepSeek-V3模型已就绪")
        print("=" * 50)
        
        # 进行一个简单的对话测试
        print("\n🔄 进行额外测试...")
        response = client.simple_chat("请用一句话解释什么是人工智能")
        print(f"💬 AI回复: {response}")
        
    else:
        print("\n" + "=" * 50)
        print("❌ 测试失败! 请检查API配置")
        print("=" * 50)
        print("\n🔧 故障排除建议:")
        print("1. 检查API密钥是否正确")
        print("2. 检查网络连接")
        print("3. 确认API端点URL是否可访问")
        print("4. 检查模型名称是否正确")

if __name__ == "__main__":
    main()