import time
import httpx
import json
import asyncio
from typing import List
from core.base import LLMProvider
from core.schema import TestResult, ChatMessage

class OpenAICompatibleProvider(LLMProvider):
    def __init__(self, api_key: str, base_url: str):
        # Ensure api_key is a string and strip whitespace to prevent "Illegal header value" errors
        self.api_key = (api_key or "").strip()
        
        # Ensure base_url is a string and strip whitespace
        base_url = (base_url or "").strip()
        
        # Default to OpenAI if empty
        if not base_url:
            base_url = "https://api.openai.com/v1"
            
        # Auto-fix protocol if missing
        if not base_url.startswith(("http://", "https://")):
            if "localhost" in base_url or "127.0.0.1" in base_url or "0.0.0.0" in base_url:
                base_url = "http://" + base_url
            else:
                base_url = "https://" + base_url
                
        self.base_url = base_url.rstrip('/')
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def test_connectivity(self) -> bool:
        # 简单的连通性测试，通常尝试列出模型，或者发一个极其简单的请求
        # 由于很多兼容接口不一定实现了 /models 端点，我们直接发一个简单的 chat 请求来测试
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/models",
                    headers=self.headers,
                    timeout=5.0
                )
                if response.status_code == 200:
                    return True
                # 如果 models 失败，尝试发一个空请求看看是否 401/403 (代表连通但认证失败) 或者 400
                # 这里我们假设能连上就行
                return True
        except Exception:
            return False

    async def run_benchmark(self, model: str, messages: List[ChatMessage], config: dict = None, stream_callback=None) -> TestResult:
        url = f"{self.base_url}/chat/completions"
        
        # Google Gemini Compatibility Fix: 
        # The Google OpenAI-compatible endpoint (v1beta/openai/chat/completions) 
        # expects the model name WITHOUT the 'models/' prefix (e.g., "gemini-2.0-flash").
        # However, the ListModels API returns names WITH 'models/' prefix (e.g., "models/gemini-2.0-flash").
        # We must strip the prefix if present.
        real_model_name = model
        if "generativelanguage.googleapis.com" in self.base_url:
             if real_model_name.startswith("models/"):
                 real_model_name = real_model_name.replace("models/", "", 1)

        # Default config if not provided
        if config is None:
            config = {
                "temperature": 0.7,
                "max_tokens": 512,
                "top_p": 1.0
            }
            
        payload = {
            "model": real_model_name,
            "messages": [m.dict() for m in messages],
            "stream": True,
            "max_tokens": config.get("max_tokens", 512),
            "temperature": config.get("temperature", 0.7),
            "top_p": config.get("top_p", 1.0)
        }

        start_time = time.perf_counter()
        first_token_time = None
        end_time = None
        token_count = 0
        response_content = []
        reasoning_content = []
        
        # Mimo Fix: Handle 307 Redirects manually if needed, though follow_redirects=True should handle it.
        # But some clients might have issues if the redirect drops the method to GET.
        # httpx handles 307 correctly by preserving the method (POST).
        # Let's verify if 'mimo' needs special handling.
        
        try:
            # Using follow_redirects=True is key here.
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                async with client.stream("POST", url, headers=self.headers, json=payload) as response:
                    if response.status_code != 200:
                        error_text = await response.aread()
                        return TestResult(
                            provider="OpenAICompatible",
                            model=model,
                            success=False,
                            error_message=f"HTTP {response.status_code}: {error_text.decode('utf-8')}"
                        )

                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str.strip() == "[DONE]":
                                break
                            
                            try:
                                data = json.loads(data_str)
                                choices = data.get("choices", [])
                                if not choices:
                                    continue
                                
                                delta = choices[0].get("delta", {})
                                content_delta = delta.get("content", "")
                                reasoning_delta = delta.get("reasoning_content", "")
                                
                                # Handle Reasoning Content (Thinking)
                                if reasoning_delta:
                                    reasoning_content.append(reasoning_delta)
                                    if stream_callback:
                                        if asyncio.iscoroutinefunction(stream_callback):
                                            await stream_callback("reasoning", reasoning_delta)
                                        else:
                                            stream_callback("reasoning", reasoning_delta)

                                # Handle Regular Content
                                if content_delta:
                                    if first_token_time is None:
                                        first_token_time = time.perf_counter()
                                    
                                    token_count += 1 # 这里简单按 chunk 计数，近似 token 数，不完全准确但作为 benchmark 可参考
                                    response_content.append(content_delta)
                                    # Optional: Stream regular content too if needed in future
                                    # if stream_callback:
                                    #    stream_callback("content", content_delta)

                            except json.JSONDecodeError:
                                continue
            
            end_time = time.perf_counter()
            
            # 计算指标
            ttft = (first_token_time - start_time) * 1000 if first_token_time else 0
            total_latency = (end_time - start_time) * 1000
            
            # Generate TPS (Tokens Per Second) - 基于生成时间
            generate_time = end_time - first_token_time if first_token_time else 0
            tps = token_count / generate_time if generate_time > 0 else 0

            return TestResult(
                provider="OpenAICompatible",
                model=model,
                success=True,
                ttft_ms=round(ttft, 2),
                total_latency_ms=round(total_latency, 2),
                output_tokens=token_count,
                tps=round(tps, 2),
                response_content="".join(response_content),
                reasoning_content="".join(reasoning_content) if reasoning_content else None
            )

        except Exception as e:
            return TestResult(
                provider="OpenAICompatible",
                model=model,
                success=False,
                error_message=str(e)
            )
