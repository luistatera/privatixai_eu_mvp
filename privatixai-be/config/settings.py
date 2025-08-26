"""
PrivatixAI Configuration Management
Centralized configuration for all backend services
"""

import os
from pathlib import Path
from typing import Optional, ClassVar, Set
from pydantic_settings import BaseSettings, SettingsConfigDict
import re
import platform

def _load_env_file(path: Path) -> None:
    """Lightweight .env loader (no external deps). Adds keys not already in os.environ."""
    try:
        if not path.exists():
            return
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, val = line.split("=", 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key:
                # Always prefer .env values on app start to simplify desktop configuration
                os.environ[key] = val
    except Exception:
        # Best-effort; ignore format errors
        pass


def _bootstrap_env_files() -> None:
    """Load .env.local then .env from backend root before settings are instantiated."""
    try:
        backend_root = Path(__file__).resolve().parents[1]
        # Prefer .env.local, then .env
        for fname in (".env.local", ".env"):
            _load_env_file(backend_root / fname)
    except Exception:
        pass


_bootstrap_env_files()


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application Settings
    DEBUG: bool = True
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    
    # Privacy & Local Processing
    USE_LOCAL_LLM: bool = False
    ENABLE_CLOUD_FALLBACK: bool = False  # Only for development
    
    # Model Configuration
    # LLM model name provided via .env (e.g., mistral-medium-latest)
    DEFAULT_LLM_MODEL: str = ""
    WHISPER_MODEL: str = "base"
    
    # Paths (OS-specific)
    @property
    def HOME_PATH(self) -> Path:
        """Cross-platform home directory"""
        return Path.home()
    
    @property
    def DATA_PATH(self) -> Path:
        """User data directory"""
        if platform.system() == "Darwin":  # macOS
            return self.HOME_PATH / "Library" / "Application Support" / "PrivatixAI" / "data"
        elif platform.system() == "Windows":
            return Path(os.environ.get("APPDATA", self.HOME_PATH)) / "PrivatixAI" / "data"
        else:  # Linux
            return self.HOME_PATH / ".local" / "share" / "PrivatixAI" / "data"
    
    @property
    def VECTORSTORE_PATH(self) -> Path:
        """Chroma DB storage path"""
        return self.DATA_PATH / "vectorstore"
    
    @property
    def MODEL_PATH(self) -> Path:
        """Local model storage path"""
        return self.DATA_PATH / "models"
    
    @property
    def UPLOAD_PATH(self) -> Path:
        """User uploaded files path"""
        return self.DATA_PATH / "uploads"
    
    @property
    def TRANSCRIPTS_PATH(self) -> Path:
        """Transcripts storage path"""
        return self.DATA_PATH / "transcripts"

    @property
    def CHUNKS_PATH(self) -> Path:
        """Encrypted text chunks storage path"""
        return self.DATA_PATH / "chunks"

    @property
    def KEYSTORE_PATH(self) -> Path:
        """Directory for local encryption keys (never committed)"""
        return self.DATA_PATH / "keystore"

    @property
    def PRIVACY_PATH(self) -> Path:
        """Directory for privacy-related artifacts (consent records, exports)"""
        return self.DATA_PATH / "privacy"
    
    # License Configuration (removed in MVP 1.0)
    
    # LLM API Configuration
    MISTRAL_API_KEY: Optional[str] = None
    
    # Processing Configuration
    MAX_FILE_SIZE_MB: int = 100
    MAX_AUDIO_DURATION_MINUTES: int = 60
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    # Retrieval/Prompt sizing
    SNIPPET_WINDOW_CHARS: int = 240
    MAX_CONTEXT_CHARS: int = 4000

    # Chunking (token-based) configuration
    # Target token window per chunk and overlap/minimums (approximate tokens)
    CHUNK_TARGET_TOKENS: int = 1000
    CHUNK_MIN_TOKENS: int = 200
    CHUNK_OVERLAP_TOKENS: int = 150

    # Retrieval configuration
    RETRIEVAL_TOPK: int = 12
    RETRIEVAL_MIN_SCORE: float = 0.15
    MMR_LAMBDA: float = 0.5

    # Re-ranking configuration (local, lightweight)
    ENABLE_RERANKER: bool = True
    RERANK_KEEP_TOPN: int = 6
    RERANKER_MAX_MS: int = 120

    # Optional lexical fallback
    ENABLE_BM25: bool = False

    # Multi-turn anchoring
    ENABLE_AUTO_ANCHORING: bool = True
    ANCHOR_MAX_CHUNKS: int = 3
    # Embeddings must always be generated locally by the bundled model in dev/prod
    
    # Cache Configuration
    ENABLE_MEMORY_CACHE: bool = True
    CACHE_TTL_SECONDS: int = 3600
    
    # Logging Configuration
    @property
    def LOG_DIR(self) -> Path:
        return self.DATA_PATH / "logs"
    LOG_MAX_BYTES: int = 5 * 1024 * 1024  # 5 MB
    LOG_BACKUP_COUNT: int = 3
    
    # Supported File Types
    SUPPORTED_TEXT_FORMATS: ClassVar[Set[str]] = {".txt", ".md", ".pdf", ".docx"}
    SUPPORTED_AUDIO_FORMATS: ClassVar[Set[str]] = {".mp3"}
    # Video and subtitles are out of scope for MVP 1.0
    
    # Pydantic v2 settings config
    model_config = SettingsConfigDict(
        env_file=".env.local",
        env_file_encoding="utf-8",
        extra="ignore",
    )

# Global settings instance
settings = Settings()

def get_device_id() -> str:
    """Generate a stable device ID for licensing"""
    import hashlib
    import uuid
    
    # Use MAC address as a stable identifier
    mac = uuid.getnode()
    device_string = f"{platform.system()}-{platform.machine()}-{mac}"
    return hashlib.sha256(device_string.encode()).hexdigest()[:16]

def validate_paths():
    """Ensure all required paths exist"""
    paths_to_create = [
        settings.DATA_PATH,
        settings.VECTORSTORE_PATH,
        settings.MODEL_PATH,
        settings.UPLOAD_PATH,
        settings.TRANSCRIPTS_PATH,
        settings.CHUNKS_PATH,
        settings.KEYSTORE_PATH,
        settings.PRIVACY_PATH,
    ]
    
    for path in paths_to_create:
        path.mkdir(parents=True, exist_ok=True)

def get_local_embedding_model_dir() -> Path:
    """Return the directory path where the BGE-m3 embedding model must be located.

    The installer must place the model files here so that runtime never attempts
    a network download. If the directory does not exist, the application should
    fail fast in normal dev/prod runs.
    """
    return settings.MODEL_PATH / "embedding" / "BAAI-bge-m3"

    