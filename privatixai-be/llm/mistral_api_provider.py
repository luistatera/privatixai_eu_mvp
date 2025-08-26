"""
Mistral API Provider - Direct integration with Mistral's API

Implements privacy-safe HTTP calls to Mistral's API using TLS 1.3+.
Only sends necessary data and respects privacy guidelines.
"""

from __future__ import annotations

from typing import List, Dict, Any, Optional, AsyncGenerator
import logging
import httpx
import ssl
import asyncio
import time
import json

from config.settings import settings, get_device_id
from .interface import LLMInterface, LLMResponse, ChatMessage, LLMUnavailableError

logger = logging.getLogger(__name__)


class MistralApiProvider(LLMInterface):
    """Direct Mistral API provider."""

    def __init__(self) -> None:
        # Respect DEFAULT_LLM_MODEL only; do not hardcode a model fallback
        self.model_name = settings.DEFAULT_LLM_MODEL
        
        if not settings.MISTRAL_API_KEY:
            raise RuntimeError("MISTRAL_API_KEY is not configured")
            
        self._base_url = "https://api.mistral.ai"
        self._headers = {
            "Authorization": f"Bearer {settings.MISTRAL_API_KEY}",
            "Content-Type": "application/json",
        }
        
        # HTTPX client with strict timeouts and TLS 1.3+
        ssl_context = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)
        try:
            ssl_context.minimum_version = ssl.TLSVersion.TLSv1_3
        except Exception:
            pass
            
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers=self._headers,
            timeout=httpx.Timeout(60.0),
            http2=True,  # Mistral API supports HTTP/2
            verify=ssl_context,
        )
        
        # Circuit breaker state
        self._fail_count: int = 0
        self._circuit_open_until: float = 0.0

    def _circuit_open(self) -> bool:
        return time.time() < self._circuit_open_until

    def _record_failure(self) -> None:
        self._fail_count += 1
        if self._fail_count >= 3:  # Lower threshold for API calls
            self._circuit_open_until = time.time() + 30
            self._fail_count = 0

    def _record_success(self) -> None:
        self._fail_count = 0
        self._circuit_open_until = 0.0

    async def ask_llm(
        self,
        prompt: str,
        context: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """Single prompt completion using Mistral API"""
        
        # Format the prompt with context if provided
        full_prompt = prompt
        if context:
            full_prompt = f"Context information:\n{context}\n\nQuestion: {prompt}\n\nPlease answer based on the provided context information."
        
        # Convert to chat format as Mistral API prefers chat completions
        messages = [
            {"role": "user", "content": full_prompt}
        ]
        
        payload: Dict[str, Any] = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
            
        if self._circuit_open():
            raise LLMUnavailableError("Mistral API unavailable")
        
        last_exc: Exception | None = None
        for attempt in range(3):  # 3 retries for API calls
            try:
                logger.info({"event": "mistral_api_call", "path": "/v1/chat/completions", "model": self.model_name})
                resp = await self._client.post("/v1/chat/completions", json=payload)
                
                if resp.status_code >= 500:
                    raise LLMUnavailableError("Mistral API server error")
                if resp.status_code == 429:
                    # Rate limited, wait and retry
                    await asyncio.sleep(2 ** attempt)
                    continue
                if resp.status_code != 200:
                    error_detail = resp.text if resp.status_code < 500 else "Server error"
                    raise RuntimeError(f"Mistral API request failed: {resp.status_code} - {error_detail}")
                
                data = resp.json()
                
                # Extract content from Mistral API response
                content = ""
                if "choices" in data and data["choices"]:
                    choice = data["choices"][0]
                    if "message" in choice and "content" in choice["message"]:
                        content = choice["message"]["content"]
                
                self._record_success()
                return LLMResponse(
                    content=content,
                    model=data.get("model", self.model_name),
                    usage=data.get("usage", {}),
                    metadata={"provider": "mistral_api", "api_version": "v1"},
                    is_local=False,
                )
                
            except (httpx.ConnectError, httpx.ReadTimeout, httpx.WriteTimeout, httpx.ConnectTimeout) as e:
                last_exc = e
                if attempt < 2:  # Retry on connection errors
                    await asyncio.sleep(2 ** attempt)
                    continue
                logger.exception("Mistral API connectivity error")
                self._record_failure()
                raise LLMUnavailableError("Mistral API unavailable")
            except (LLMUnavailableError, RuntimeError) as e:
                last_exc = e
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)
                    continue
                self._record_failure()
                raise
                
        # Should not reach here
        raise LLMUnavailableError("Mistral API unavailable")

    async def chat_completion(
        self,
        messages: List[ChatMessage],
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """Multi-turn chat completion using Mistral API"""
        
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": m.role, "content": m.content} for m in messages
            ],
            "temperature": temperature,
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
            
        if self._circuit_open():
            raise LLMUnavailableError("Mistral API unavailable")
        
        for attempt in range(3):
            try:
                logger.info({"event": "mistral_api_chat_call", "path": "/v1/chat/completions", "model": self.model_name})
                resp = await self._client.post("/v1/chat/completions", json=payload)
                
                if resp.status_code >= 500:
                    raise LLMUnavailableError("Mistral API server error")
                if resp.status_code == 429:
                    await asyncio.sleep(2 ** attempt)
                    continue
                if resp.status_code != 200:
                    error_detail = resp.text if resp.status_code < 500 else "Server error"
                    raise RuntimeError(f"Mistral API request failed: {resp.status_code} - {error_detail}")
                
                data = resp.json()
                
                content = ""
                if "choices" in data and data["choices"]:
                    choice = data["choices"][0]
                    if "message" in choice and "content" in choice["message"]:
                        content = choice["message"]["content"]
                
                self._record_success()
                return LLMResponse(
                    content=content,
                    model=data.get("model", self.model_name),
                    usage=data.get("usage", {}),
                    metadata={"provider": "mistral_api", "api_version": "v1"},
                    is_local=False,
                )
                
            except (httpx.ConnectError, httpx.ReadTimeout, httpx.WriteTimeout, httpx.ConnectTimeout, LLMUnavailableError, RuntimeError):
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)
                    continue
                logger.exception("Mistral API connectivity error")
                self._record_failure()
                raise LLMUnavailableError("Mistral API unavailable")
        
        raise LLMUnavailableError("Mistral API unavailable")

    async def stream_completion(
        self,
        prompt: str,
        context: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
    ) -> AsyncGenerator[str, None]:
        """Streaming completion using Mistral API"""
        
        # Format the prompt with context if provided
        full_prompt = prompt
        if context:
            full_prompt = f"Context information:\n{context}\n\nQuestion: {prompt}\n\nPlease answer based on the provided context information."
        
        # Convert to chat format
        messages = [
            {"role": "user", "content": full_prompt}
        ]
        
        payload: Dict[str, Any] = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "stream": True
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
            
        if self._circuit_open():
            raise LLMUnavailableError("Mistral API unavailable")
        
        try:
            logger.info({"event": "mistral_api_stream_call", "path": "/v1/chat/completions", "model": self.model_name})
            
            async with self._client.stream("POST", "/v1/chat/completions", json=payload) as response:
                if response.status_code >= 500:
                    raise LLMUnavailableError("Mistral API server error")
                if response.status_code != 200:
                    error_detail = await response.aread() if response.status_code < 500 else b"Server error"
                    raise RuntimeError(f"Mistral API stream request failed: {response.status_code} - {error_detail.decode()}")
                
                buffer = ""
                async for chunk in response.aiter_text():
                    buffer += chunk
                    
                    # Process Server-Sent Events format
                    while "\n\n" in buffer:
                        line, buffer = buffer.split("\n\n", 1)
                        line = line.strip()
                        
                        if line.startswith("data: "):
                            data_part = line[6:]  # Remove "data: " prefix
                            
                            if data_part == "[DONE]":
                                self._record_success()
                                return
                            
                            try:
                                chunk_data = json.loads(data_part)
                                
                                # Extract content from Mistral API streaming response
                                content = ""
                                if "choices" in chunk_data and chunk_data["choices"]:
                                    choice = chunk_data["choices"][0]
                                    if "delta" in choice and "content" in choice["delta"]:
                                        content = choice["delta"]["content"]
                                
                                if content:
                                    yield content
                                    
                            except json.JSONDecodeError:
                                # Skip malformed JSON chunks
                                continue
                            except Exception:
                                # Skip other parsing errors
                                continue
                
                self._record_success()
                
        except (httpx.ConnectError, httpx.ReadTimeout, httpx.WriteTimeout, httpx.ConnectTimeout) as e:
            logger.exception("Mistral API streaming connectivity error")
            self._record_failure()
            # Fall back to non-streaming response
            logger.info({"event": "streaming_fallback_to_nonstream"})
            response = await self.ask_llm(prompt=prompt, context=context, max_tokens=max_tokens, temperature=temperature)
            yield response.content
        except Exception as e:
            logger.exception("Mistral API streaming error")
            self._record_failure()
            # Fall back to non-streaming response
            logger.info({"event": "streaming_fallback_to_nonstream"})
            response = await self.ask_llm(prompt=prompt, context=context, max_tokens=max_tokens, temperature=temperature)
            yield response.content

    async def health_check(self) -> bool:
        """Check if Mistral API is available"""
        try:
            # Use a simple model list call to check API health
            resp = await self._client.get("/v1/models")
            return resp.status_code == 200
        except Exception:
            return False

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model"""
        return {
            "model": self.model_name,
            "provider": "mistral_api",
            "api_version": "v1",
            "hosted": False
        }

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._client.aclose()
