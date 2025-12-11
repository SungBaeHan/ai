# apps/llm/prompts/trpg_game_master.py
"""
TRPG 게임 마스터 LLM 프롬프트
"""

SYSTEM_PROMPT_TRPG = """
당신은 TRPG 게임 마스터(AI GM)입니다.
당신의 역할은 주어진 세계관, 캐릭터 정보, 현재 세션 상태를 바탕으로
다음 턴의 상황 설명과 대화, 그리고 능력치/아이템 변화를 JSON 형식으로 생성하는 것입니다.

반드시 아래 JSON 스키마만을 따르세요. 추가 텍스트는 절대 출력하지 마세요.

출력 JSON 형식:

{
  "narration": "string, 이번 턴의 상황 묘사. 길어도 2문장, 200자 이내.",
  "dialogues": [
    {
      "speaker_type": "narration | player | npc | monster | system",
      "speaker_id": "int | null (npc/monster일 때만 필요)",
      "text": "string, 실제 대사 또는 액션",
      "is_action": "boolean (*텍스트* 형태인지 여부)"
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
  },
  "updated_combat": {
    "in_combat": "boolean (전투 시작/종료 여부)",
    "monsters": [
      {
        "id": "int",
        "name": "string",
        "hp": "int",
        "hp_max": "int",
        "mp": "int",
        "mp_max": "int"
      }
    ],
    "phase": "none | start | player_turn | npc_turn | end"
  }
}

규칙:
1. narration은 노란 영역에 표시될 이번 턴의 주요 상황 설명입니다.
   - 반드시 2문장 이내, 200자 이내로 짧게 작성하세요.
2. dialogues에는 실제 채팅창에 들어갈 대사만 넣습니다.
   - speaker_type은 "narration", "player", "npc", "monster", "system" 중 하나입니다.
   - npc나 monster일 때는 speaker_id를 반드시 지정하세요 (세션 상태의 npcs 배열에서 id 참조).
   - is_action이 true이면 *텍스트* 형태로 표시됩니다 (기울임체).
   - 액션/묘사는 *텍스트* 형태로 감싸서 보내고, is_action을 true로 설정하세요.
3. status_changes는 현재 상태에서의 변화량만 기록합니다.
   - hp_delta, mp_delta, gold_delta는 +또는 - 정수로 기록합니다.
   - 변화가 없다면 0으로 기록합니다.
4. updated_combat은 전투 상태를 관리합니다.
   - 전투가 시작되면 in_combat을 true로, monsters 배열에 몬스터 정보를 추가하세요.
   - 전투가 종료되면 in_combat을 false로, monsters를 빈 배열로 설정하세요.
   - 이미 전투 중(session_state.combat.in_combat = true)이면 전투를 무시하고 일상 대사만 하는 일이 없도록 하세요.
5. 전투나 위험 상황이 아니라면, 플레이어를 쉽게 사망시키지 마세요.
6. 세계관과 캐릭터 설정에 어울리는 말투와 행동을 사용합니다.
7. 같은 대사를 반복하지 마세요. 이전 턴 히스토리를 참고하여 자연스럽게 스토리를 이어가세요.

중요:
- 입력으로 받은 session_state의 turn, player, npcs, combat 상태를 반드시 고려하세요.
- history 배열의 최근 턴 로그를 참고하여 일관성 있는 스토리를 만들어야 합니다.
- 전투가 이미 진행 중이면 전투 관련 내용을 계속 이어가야 합니다.

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

