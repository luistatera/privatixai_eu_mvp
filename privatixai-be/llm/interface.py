"""
LLM Interface - Unified abstraction layer for all LLM operations
Supports switching between local (Ollama) and cloud APIs for development
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncGenerator
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class LLMResponse:
    """Standardized LLM response format"""
    content: str
    model: str
    usage: Dict[str, int]
    metadata: Dict[str, Any]
    is_local: bool

@dataclass
class ChatMessage:
    """Chat message format"""
    role: str  # "user", "assistant", "system"
    content: str
    metadata: Optional[Dict[str, Any]] = None

class LLMInterface(ABC):
    """Abstract interface for all LLM providers"""
    
    @abstractmethod
    async def ask_llm(
        self, 
        prompt: str, 
        context: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7
    ) -> LLMResponse:
        """Single prompt completion"""
        pass
    
    @abstractmethod
    async def chat_completion(
        self,
        messages: List[ChatMessage],
        max_tokens: Optional[int] = None,
        temperature: float = 0.7
    ) -> LLMResponse:
        """Multi-turn chat completion"""
        pass
    
    @abstractmethod
    async def stream_completion(
        self,
        prompt: str,
        context: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7
    ) -> AsyncGenerator[str, None]:
        """Streaming completion"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the LLM service is available"""
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model"""
        pass

class LLMError(Exception):
    """Base exception for LLM operations"""
    pass

class LLMUnavailableError(LLMError):
    """Raised when LLM service is unavailable"""
    pass

class LLMContextLengthError(LLMError):
    """Raised when context exceeds model limits"""
    pass
