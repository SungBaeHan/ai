# apps/api/config.py
"""
애플리케이션 설정 모듈
환경변수를 한 곳에서 관리
"""

import os
from typing import Optional


class Settings:
    """애플리케이션 설정"""
    
    # DB 백엔드 설정 (기본값: mongo)
    db_backend: str = os.getenv("DB_BACKEND", "mongo").lower()
    
    # MongoDB 설정
    mongodb_uri: str = os.getenv("MONGODB_URI") or os.getenv("MONGO_URI", "")
    mongo_db_name: str = os.getenv("MONGO_DB_NAME") or os.getenv("MONGO_DB", "arcanaverse")
    
    # SQLite 설정 (레거시 지원용, 기본적으로 사용 안 함)
    db_path: str = os.getenv("DB_PATH", "/data/db/app.sqlite3")
    
    # OpenAI 설정
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    openai_api_base: str = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    
    # LLM Provider 설정 (기본값: openai)
    llm_provider: str = os.getenv("LLM_PROVIDER", "openai").lower()
    
    @property
    def is_mongo(self) -> bool:
        """MongoDB를 사용하는지 확인"""
        return self.db_backend == "mongo"
    
    @property
    def is_sqlite(self) -> bool:
        """SQLite를 사용하는지 확인"""
        return self.db_backend == "sqlite"
    
    @property
    def is_openai(self) -> bool:
        """OpenAI를 사용하는지 확인"""
        return self.llm_provider == "openai"
    
    @property
    def is_ollama(self) -> bool:
        """Ollama를 사용하는지 확인"""
        return self.llm_provider == "ollama"


# 전역 설정 인스턴스
settings = Settings()


