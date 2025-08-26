"""Router module - API endpoints for PrivatixAI backend"""

from . import chat_router, memory_router, upload_router, privacy_router

# License routes are planned for v1.1 and intentionally not exported in v1.0
__all__ = ["chat_router", "memory_router", "upload_router", "privacy_router"]
