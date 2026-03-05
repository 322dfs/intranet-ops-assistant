import requests
import time
from typing import List, Dict, Any

from config import DEEPSEEK_API_KEY, DEEPSEEK_API_URL, DEEPSEEK_MODEL, DEEPSEEK_TEMPERATURE


def get_ai_response(messages: List[Dict[str, str]], system_prompt: str = None) -> str:
    """
    调用 DeepSeek API 获取 AI 响应
    
    Args:
        messages: 聊天消息历史，格式为 [{"role": "user/assistant", "content": "消息内容"}]
        system_prompt: 系统提示词，用于指导 AI 行为
    
    Returns:
        AI 生成的响应内容
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    }
    
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [],
        "temperature": DEEPSEEK_TEMPERATURE,
        "max_tokens": 1000
    }
    
    # 添加系统提示词
    if system_prompt:
        payload["messages"].append({"role": "system", "content": system_prompt})
    
    # 添加消息历史
    payload["messages"].extend(messages)
    
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except requests.exceptions.RequestException as e:
            print(f"DeepSeek API 调用失败 (尝试 {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                print(f"等待 {retry_delay} 秒后重试...")
                time.sleep(retry_delay)
                retry_delay *= 2  # 指数退避
            else:
                raise
        except Exception as e:
            print(f"DeepSeek API 处理失败: {e}")
            raise