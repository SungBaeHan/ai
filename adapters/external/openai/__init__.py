# adapters/external/openai/__init__.py
"""OpenAI 클라이언트 어댑터"""

from .openai_client import generate_chat_completion, client

__all__ = ["generate_chat_completion", "client"]

