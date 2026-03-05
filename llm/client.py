"""
LLM 客户端 - 支持多种 LLM 提供商
"""
import asyncio
from typing import Dict, List, Optional, AsyncGenerator, Any
from openai import AsyncOpenAI, OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
import json

from config.settings import LLMConfig


class LLMClient:
    """LLM 客户端封装"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = AsyncOpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=config.timeout
        )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def complete(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict]] = None,
        tool_choice: Optional[str] = None,
        response_format: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """异步完成请求"""
        try:
            params = {
                "model": self.config.model,
                "messages": messages,
                "temperature": temperature or self.config.temperature,
                "max_tokens": max_tokens or self.config.max_tokens
            }
            
            if tools:
                params["tools"] = tools
            if tool_choice:
                params["tool_choice"] = tool_choice
            if response_format:
                params["response_format"] = response_format
            
            response = await self.client.chat.completions.create(**params)
            
            return {
                "content": response.choices[0].message.content or "",
                "role": response.choices[0].message.role,
                "tool_calls": response.choices[0].message.tool_calls,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0
                }
            }
        except Exception as e:
            print(f"[LLM Error] {str(e)}")
            raise
    
    async def stream(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        """流式响应"""
        try:
            stream = await self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=temperature or self.config.temperature,
                max_tokens=max_tokens or self.config.max_tokens,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            print(f"[Stream Error] {str(e)}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def complete_sync(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """同步完成请求"""
        try:
            client = OpenAI(
                api_key=self.config.api_key,
                base_url=self.config.base_url,
                timeout=self.config.timeout
            )
            
            params = {
                "model": self.config.model,
                "messages": messages,
                "temperature": temperature or self.config.temperature,
                "max_tokens": max_tokens or self.config.max_tokens
            }
            
            if response_format:
                params["response_format"] = response_format
            
            response = client.chat.completions.create(**params)
            
            return {
                "content": response.choices[0].message.content or "",
                "role": response.choices[0].message.role,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0
                }
            }
        except Exception as e:
            print(f"[LLM Sync Error] {str(e)}")
            raise
    
    async def is_available(self) -> bool:
        """检查 LLM 服务是否可用"""
        try:
            response = await self.complete(
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=5
            )
            return True
        except:
            return False