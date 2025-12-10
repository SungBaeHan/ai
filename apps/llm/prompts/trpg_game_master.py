# apps/llm/prompts/trpg_game_master.py
"""
TRPG 게임 마스터 LLM 프롬프트
"""

SYSTEM_PROMPT_TRPG = """
당신은 TRPG 게임 마스터(AI GM)입니다.
당신의 역할은 주어진 세계관, 캐릭터 정보, 현재 턴 상태를 바탕으로
다음 턴의 상황 설명과 대화, 그리고 능력치/아이템 변화를 JSON 형식으로 생성하는 것입니다.

반드시 아래 JSON 스키마만을 따르세요. 추가 텍스트는 절대 출력하지 마세요.

출력 JSON 형식:

{
  "narration": "string, 이번 턴의 상황 묘사. 길어도 2문장, 200자 이내.",
  "dialogues": [
    {
      "speaker_type": "user | npc | system",
      "name": "string | null",
      "text": "string, 실제 대사"
    }
  ],
  "status_changes": {
    "user": {
      "hp_delta": "int (증가/감소, 없으면 0)",
      "mp_delta": "int",
      "items_add": ["string"],
      "items_remove": ["string"],
      "gold_delta": "int"
    },
    "characters": [
      {
        "char_ref_id": "int",
        "hp_delta": "int",
        "mp_delta": "int",
        "items_add": ["string"],
        "items_remove": ["string"],
        "gold_delta": "int"
      }
    ]
  }
}

규칙:
1. narration은 노란 영역에 표시될 이번 턴의 주요 상황 설명입니다.
   - 반드시 2문장 이내, 200자 이내로 짧게 작성하세요.
2. dialogues에는 실제 채팅창에 들어갈 대사만 넣습니다.
   - user는 플레이어를 의미합니다. 아직 이름이 없으면 name은 null로 둡니다.
   - npc는 등장한 캐릭터 중 하나를 사용합니다.
3. status_changes는 현재 상태에서의 변화량만 기록합니다.
   - hp_delta, mp_delta, gold_delta는 +또는 - 정수로 기록합니다.
   - 변화가 없다면 0으로 기록합니다.
4. 전투나 위험 상황이 아니라면, 플레이어를 쉽게 사망시키지 마세요.
5. {user}와 {npc} 플레이스홀더가 있을 경우, 컨텍스트로 주어진 실제 이름을 사용합니다.
6. 세계관과 캐릭터 설정에 어울리는 말투와 행동을 사용합니다.

JSON 이외의 설명 텍스트는 절대 출력하지 마세요.
"""


def build_trpg_user_prompt(game_status: dict, user_message: str, world_snapshot: dict) -> str:
    """
    TRPG 게임 마스터용 유저 프롬프트 생성
    
    Args:
        game_status: MongoDB에서 읽은 현재 게임 상태
        user_message: 플레이어 입력 메시지
        world_snapshot: 게임 생성 시 저장해둔 세계관 스냅샷
    
    Returns:
        유저 프롬프트 문자열
    """
    # 게임 상태 정보 포맷팅
    turn = game_status.get('turn', 1)
    user_info = game_status.get('user_info', {})
    characters_info = game_status.get('characters_info', [])
    story_history = game_status.get('story_history', [])
    
    # 최근 3턴 히스토리 포맷팅
    history_text = ""
    if story_history:
        recent = story_history[-3:]
        for h in recent:
            history_text += f"\n턴 {h.get('turn', '?')}: {h.get('narration', '')}\n"
            for d in h.get('dialogues', []):
                speaker = d.get('name') or d.get('speaker_type', 'unknown')
                history_text += f"  - {speaker}: {d.get('text', '')}\n"
    
    # 캐릭터 정보 포맷팅
    chars_text = ""
    for c in characters_info:
        name = c.get('snapshot', {}).get('name', 'Unknown')
        char_id = c.get('char_ref_id', '?')
        summary = c.get('snapshot', {}).get('summary', '')
        chars_text += f"\n- {name} (ID: {char_id}): {summary}\n"
    
    # 유저 정보 포맷팅
    user_attrs = user_info.get('attributes', {})
    user_items = user_info.get('items', {})
    user_text = f"속성: {user_attrs}\n아이템: {user_items}"
    
    return f"""
[세계관 정보]
이름: {world_snapshot.get('name', 'Unknown')}
요약: {world_snapshot.get('summary', '')}
상세: {world_snapshot.get('scenario_detail', world_snapshot.get('summary', ''))}

[현재 턴 정보]
턴 번호: {turn}

[플레이어(user) 상태]
{user_text}

[등장한 캐릭터들(characters_info)]
{chars_text}

[이전 스토리 히스토리 일부]
{history_text}

[플레이어 입력]
"{user_message}"

위 정보를 기반으로, 다음 턴의 상황 설명, 대사, 그리고 능력/아이템 변화를 위에서 정의한 JSON 포맷으로 생성하세요.
"""

