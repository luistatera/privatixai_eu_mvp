"""
LLM Service - Main service for LLM operations
Handles provider selection and fallback logic
"""

import logging
from typing import List, Dict, Any, Optional, AsyncGenerator

from .interface import LLMInterface, LLMResponse, ChatMessage, LLMError, LLMUnavailableError
from .mistral_api_provider import MistralApiProvider
from config.settings import settings

logger = logging.getLogger(__name__)

class LLMService:
    """Main LLM service with provider management"""
    
    def __init__(self):
        self.provider: Optional[LLMInterface] = None
        self._initialize_provider()
    
    def _initialize_provider(self):
        """Initialize Mistral API provider"""
        try:
            # Always use Mistral API provider
            self.provider = MistralApiProvider()
            logger.info("Initialized LLM provider: Mistral API")
        except Exception as e:
            # Do not fail app startup in development if API key is missing
            self.provider = None
            logger.warning(f"Mistral API provider disabled: {e}")
        
    
    async def ask_llm(
        self, 
        prompt: str, 
        context: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        use_local: bool = True
    ) -> LLMResponse:
        """
        Main LLM query function using Mistral API
        
        Args:
            prompt: The user's question or instruction
            context: Optional context for the query (e.g., retrieved memories)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 to 1.0)
            use_local: Ignored, kept for compatibility
        """
        
        if self.provider:
            try:
                logger.info({"event": "llm_query_started", "provider": "mistral_api", "local": False})
                response = await self.provider.ask_llm(
                    prompt=prompt,
                    context=context,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                logger.info({"event": "llm_query_completed", "provider": "mistral_api", "tokens": response.usage.get("total_tokens", 0)})
                return response
            except LLMUnavailableError as e:
                logger.exception("Mistral API provider unavailable")
                raise LLMError("mistral_api_unavailable")
        
        # No provider configured/available (e.g., missing API key)
        raise LLMError("mistral_api_not_configured")
    
    async def chat_completion(
        self,
        messages: List[ChatMessage],
        max_tokens: Optional[int] = None,
        temperature: float = 0.7
    ) -> LLMResponse:
        """Multi-turn chat completion using Mistral API"""
        if not self.provider:
            raise LLMError("Mistral API provider not available")
        
        try:
            return await self.provider.chat_completion(
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
        except LLMUnavailableError:
            raise LLMError("Mistral API is unavailable for chat")
    
    async def stream_completion(
        self,
        prompt: str,
        context: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7
    ) -> AsyncGenerator[str, None]:
        """Streaming completion using Mistral API"""
        if not self.provider:
            raise LLMError("Mistral API provider not available")
        
        try:
            async for chunk in self.provider.stream_completion(
                prompt=prompt,
                context=context,
                max_tokens=max_tokens,
                temperature=temperature
            ):
                yield chunk
        except LLMUnavailableError:
            raise LLMError("Mistral API is unavailable for streaming")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of Mistral API provider"""
        status = {
            "mistral_api": False,
            "overall": False
        }
        
        if self.provider:
            status["mistral_api"] = await self.provider.health_check()
        
        status["overall"] = status["mistral_api"]
        
        return status
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about Mistral API provider"""
        if self.provider:
            return {"mistral_api": self.provider.get_model_info()}
        return {}

# Global service instance
llm_service = LLMService()

# Convenience function for backward compatibility
async def ask_llm(prompt: str, context: Optional[str] = None) -> LLMResponse:
    """Convenience function for simple LLM queries"""
    return await llm_service.ask_llm(prompt=prompt, context=context)
