# adapters/external/embedding/sentence_transformer.py

"""
sentence-transformers 를 requirements 에서 제거한 상태에서
서버가 실행되도록 하기 위한 임시 스텁 구현입니다.

- 현재는 임베딩 기능을 실제로 수행하지 않고,
  이 함수를 호출하면 RuntimeError 를 발생시킵니다.
- 나중에 sentence-transformers 를 다시 설치할 때는
  git 히스토리에서 원본 파일을 복구하면 됩니다.
"""

from typing import List


def embed(text: str | list[str]) -> List[float]:
    """
    텍스트 임베딩용 임시 스텁 함수.

    실제로 sentence-transformers 를 사용하지 않고,
    호출되면 바로 RuntimeError 를 발생시킵니다.
    """
    raise RuntimeError(
        "현재 컨테이너 빌드에서는 sentence-transformers 가 비활성화되어 있어 "
        "임베딩 기능을 사용할 수 없습니다. "
        "임베딩이 필요하면 requirements.txt 에 sentence-transformers 를 다시 추가하고 "
        "컨테이너 이미지를 재빌드하세요."
    )
