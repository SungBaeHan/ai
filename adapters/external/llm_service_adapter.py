# adapters/external/llm_service_adapter.py
"""
LLMService 어댑터 구현
"""

from typing import List, Dict, Optional
from src.ports.services.llm_service import LLMService
from adapters.external.llm_client import get_default_llm_client


class LLMServiceAdapter(LLMService):
    """LLMService 구현체"""
    
    def generate_reply(
        self,
        messages: List[Dict[str, str]],
        context: Optional[str] = None
    ) -> str:
        """LLM 응답 생성"""
        # context가 있으면 시스템 메시지에 추가
        if context:
            # 시스템 메시지가 있으면 컨텍스트를 추가, 없으면 새로 생성
            system_message = None
            for msg in messages:
                if msg.get("role") == "system":
                    system_message = msg
                    break
            
            if system_message:
                system_message["content"] = f"{system_message['content']}\n\n{context}"
            else:
                messages.insert(0, {"role": "system", "content": context})
        
        llm_client = get_default_llm_client()
        return llm_client.generate_chat_completion(
            messages=messages,
            model=None,  # 기본 모델 사용
            temperature=0.7,
            max_tokens=None,
        )

