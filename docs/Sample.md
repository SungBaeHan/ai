================================
[users]
================================

{
  "_id": {
    "$oid": "692695d274f310fbaa14ccc5"
  },
  "email": "knodark@gmail.com",
  "google_id": "113602532019760492929",
  "display_name": "한성배",
  "is_use": "Y",
  "is_lock": "N",
  "member_level": 0,
  "created_at": {
    "$date": "2025-11-26T05:53:22.051Z"
  },
  "updated_at": {
    "$date": "2025-12-29T01:48:01.731Z"
  },
  "last_login_at": {
    "$date": "2025-12-29T01:48:01.731Z"
  },
  "personas": [
    {
      "persona_id": "p_20251222_6421",
      "name": "아리아",
      "gender": "female",
      "bio": "릴리는 여신급의 미모, H컵의 폭유지만, 아름다운 가슴\n관능적이고, 매혹적이며, 아름다운 몸매\n허리까지 오는 자연스런 롱헤어, 늘씬하고 매끄러운 다리\n섹시하고 관능적인 여왕 스타일, 여성들 마저 끌리는 미모이다",
      "image_key": "F01",
      "is_default": true,
      "created_at": {
        "$date": "2025-12-22T05:25:34.538Z"
      },
      "updated_at": {
        "$date": "2025-12-22T05:27:33.448Z"
      }
    },
    {
      "persona_id": "p_20251222_2910",
      "name": "마호",
      "gender": "male",
      "bio": "마호는 이국적인 외모의 꽃미남 스타일,\n남성 페르몬이 넘치며, 여성들이 강한 호감을 가진다.",
      "image_key": "M08",
      "is_default": false,
      "created_at": {
        "$date": "2025-12-22T05:28:19.133Z"
      },
      "updated_at": {
        "$date": "2025-12-22T05:28:19.133Z"
      }
    }
  ]
}

================================
[characters]
================================

{
  "_id": {
    "$oid": "690d94e534169dafd55e3cf6"
  },
  "id": 1,
  "archetype": "모험가",
  "background": "폐항의 창고 거점을 전전했다.",
  "created_at": 1761627149,
  "detail": "감정의 파고를 드러내지 않지만, 곁을 지키는 데 서툴지 않다.",
  "genre": "",
  "greeting": "왔어? 천천히 얘기하자.",
  "image": "/assets/char/d71b3d9ad83f.png",
  "img_hash": "d71b3d9ad83fcc1c83686db4786ff9db042d0d1e5561402bbeda2e9e538544db",
  "meta_version": 2,
  "name": "소라",
  "polish_model": "qwen2.5:7b-instruct-q4_K_M",
  "polish_status": "done",
  "scenario": "안개가 걷히자, 작은 등대 불빛이 숨을 고른다.",
  "src_file": "d71b3d9ad83f.png",
  "style": "현장 보고체, 간결하고 긴박한 톤",
  "summary": "잔상 같은 미소를 남기는 해결사.",
  "system_prompt": "구어체, 설정 일관, 장황한 독백 금지. 질문엔 간결히.",
  "tags": "[\"용병\", \"시골\", \"대담\", \"귀족\", \"궁수\", \"마법\"]",
  "updated_at": 1761627603,
  "vision_model": "moondream",
  "world": ""
}

================================
[worlds]
================================

{
  "_id": {
    "$oid": "693282d0e30d117369615a11"
  },
  "id": 1,
  "name": "아카디언 대륙",
  "genre": null,
  "summary": "",
  "tags": [],
  "image": "/assets/world/12f6e6d96b5b4b8c9cee13f83e7d6e25.png",
  "image_path": "/assets/world/12f6e6d96b5b4b8c9cee13f83e7d6e25.png",
  "src_file": "/assets/world/12f6e6d96b5b4b8c9cee13f83e7d6e25.png",
  "img_hash": "1a1bbeabdc8248dba3f376fa534bfbeb",
  "detail": "아카디언 대륙은 신비로운 마법과 고대의 유적이 가득한 땅으로, 다양한 종족과 문화가 공존하는 세계입니다. 이 대륙은 그 자체로 살아있는 존재처럼 느껴지며, 각 지역마다 독특한 특성과 이야기를 지니고 있습니다. 탐험가와 모험가들이 끊임없이 새로운 경험을 찾아 나서는 이곳은, 전설과 신화가 현실로 존재하는 신비로운 장소입니다.",
  "regions": [
    "엘프의 숲",
    "드워프의 산맥",
    "마법사들의 탑"
  ],
  "factions": [
    "은빛 엘프 연합",
    "산악 드워프 연맹",
    "암흑 마법사 협회"
  ],
  "conflicts": "아카디언 대륙에서는 엘프와 드워프 간의 고대의 갈등이 아직도 지속되고 있으며, 이들 사이의 평화를 깨뜨리려는 암흑 마법사들의 음모가 진행 중입니다. 세력 간의 정치적 긴장과 자원 분쟁이 끊임없이 대립을 일으키고 있으며, 각 세력의 목표가 서로 충돌하고 있습니다. 이러한 갈등 속에서 모험가들은 자신의 운명을 결정짓는 선택을 해야 합니다.",
  "opening_scene": "모험가들은 아카디언 대륙의 중심부에 위치한 작은 마을에서 모험을 시작합니다. 마을의 광장에서는 전설적인 보물을 찾기 위한 탐험대가 모집되고 있으며, 각종 상점과 정보 제공자들이 분주하게 움직이고 있습니다. 그러나 불길한 기운이 감돌고 있는 가운데, 마을의 수호자가 무언가를 숨기고 있다는 소문이 퍼지고 있습니다.",
  "style": "신비롭고 판타지적인 분위기, 마법과 고대의 유적이 얽혀 있는 세계",
  "status": "active",
  "reg_user": "113602532019760492929",
  "created_at": 1764917968,
  "updated_at": 1764917968
}

================================
[games]
================================
{
  "_id": {
    "$oid": "693bb1f2855d79b798ad3971"
  },
  "id": 1,
  "title": "쟂빛 대지 생존전",
  "world_ref_id": 2,
  "world_snapshot": {
    "id": 2,
    "name": "바라카 대륙",
    "summary": "한 줄 요약",
    "tags": [
      "마법"
    ],
    "image_url": "/assets/world/e05ce31edb964ac1bac606481f190eb3.png",
    "img_hash": "ce780a814b2e44d8440b8ee2776e7b59"
  },
  "scenario_summary": "쟂빛 대지에서 생존자 길드의 일원이 되어 폐하가 된 도시를 탐험합니다.",
  "scenario_detail": "이 게임은 '쟂빛 대지'라는 황폐화된 대륙에서 진행된다. 플레이어들은 생존자 길드의 일원으로서, 황폐화된 대륙을 탐험한다.",
  "tags": [
    "전투 중심",
    "협상 중심",
    "판타지"
  ],
  "characters": [
    {
      "char_ref_id": 5,
      "role": "mage",
      "snapshot": {
        "id": 5,
        "name": "미유",
        "summary": "침착하지만 굳센 의지를 지닌 모험가.",
        "tags": [
          "신비",
          "열정",
          "미래",
          "검술",
          "쾌활",
          "차분"
        ],
        "image_url": "/assets/char/fa13520db4ba.png",
        "archetype": "연성술사",
        "attributes_base": {
          "hp": {
            "enabled": true,
            "max": 100,
            "base": 80
          },
          "mp": {
            "enabled": true,
            "max": 80,
            "base": 30
          },
          "sp": {
            "enabled": true,
            "max": 60,
            "base": 20
          },
          "str": {
            "enabled": true,
            "max": 20,
            "base": 10
          },
          "int": {
            "enabled": true,
            "max": 20,
            "base": 10
          },
          "pol": {
            "enabled": false,
            "max": 20,
            "base": 10
          },
          "cha": {
            "enabled": true,
            "max": 20,
            "base": 10
          },
          "agi": {
            "enabled": true,
            "max": 20,
            "base": 10
          },
          "log": {
            "enabled": false,
            "max": 20,
            "base": 10
          },
          "wis": {
            "enabled": true,
            "max": 20,
            "base": 10
          },
          "luck": {
            "enabled": true,
            "max": 20,
            "base": 10
          }
        }
      }
    },
    {
      "char_ref_id": 16,
      "role": "healer",
      "snapshot": {
        "id": 16,
        "name": "미나",
        "summary": "침착하지만 굳센 의지를 지닌 모험가.",
        "tags": [
          "길드",
          "바닷가",
          "모험",
          "낙천",
          "진중",
          "용병"
        ],
        "image_url": "/assets/char/aa0180780639.png",
        "archetype": "모험가",
        "attributes_base": {
          "hp": {
            "enabled": true,
            "max": 100,
            "base": 80
          },
          "mp": {
            "enabled": true,
            "max": 80,
            "base": 30
          },
          "sp": {
            "enabled": true,
            "max": 60,
            "base": 20
          },
          "str": {
            "enabled": true,
            "max": 20,
            "base": 10
          },
          "int": {
            "enabled": true,
            "max": 20,
            "base": 10
          },
          "pol": {
            "enabled": false,
            "max": 20,
            "base": 10
          },
          "cha": {
            "enabled": true,
            "max": 20,
            "base": 10
          },
          "agi": {
            "enabled": true,
            "max": 20,
            "base": 10
          },
          "log": {
            "enabled": false,
            "max": 20,
            "base": 10
          },
          "wis": {
            "enabled": true,
            "max": 20,
            "base": 10
          },
          "luck": {
            "enabled": true,
            "max": 20,
            "base": 10
          }
        }
      }
    },
    {
      "char_ref_id": 48,
      "role": "warrior",
      "snapshot": {
        "id": 48,
        "name": "미소",
        "summary": "침착하지만 굳센 의지를 지닌 모험가.",
        "tags": [
          "사막",
          "도시",
          "마법",
          "궁수",
          "열정",
          "용병"
        ],
        "image_url": "/assets/char/d1d135bb6faa.png",
        "archetype": "검사",
        "attributes_base": {
          "hp": {
            "enabled": true,
            "max": 100,
            "base": 80
          },
          "mp": {
            "enabled": true,
            "max": 80,
            "base": 30
          },
          "sp": {
            "enabled": true,
            "max": 60,
            "base": 20
          },
          "str": {
            "enabled": true,
            "max": 20,
            "base": 10
          },
          "int": {
            "enabled": true,
            "max": 20,
            "base": 10
          },
          "pol": {
            "enabled": false,
            "max": 20,
            "base": 10
          },
          "cha": {
            "enabled": true,
            "max": 20,
            "base": 10
          },
          "agi": {
            "enabled": true,
            "max": 20,
            "base": 10
          },
          "log": {
            "enabled": false,
            "max": 20,
            "base": 10
          },
          "wis": {
            "enabled": true,
            "max": 20,
            "base": 10
          },
          "luck": {
            "enabled": true,
            "max": 20,
            "base": 10
          }
        }
      }
    },
    {
      "char_ref_id": 71,
      "role": "merchant",
      "snapshot": {
        "id": 71,
        "name": "미소",
        "summary": "잔상 같은 미소를 남기는 해결사.",
        "tags": [
          "용병",
          "사막",
          "차분",
          "소심",
          "궁수",
          "냉정"
        ],
        "image_url": "/assets/char/d30a727449c9.png",
        "archetype": "모험가",
        "attributes_base": {
          "hp": {
            "enabled": true,
            "max": 100,
            "base": 80
          },
          "mp": {
            "enabled": true,
            "max": 80,
            "base": 30
          },
          "sp": {
            "enabled": true,
            "max": 60,
            "base": 20
          },
          "str": {
            "enabled": true,
            "max": 20,
            "base": 10
          },
          "int": {
            "enabled": true,
            "max": 20,
            "base": 10
          },
          "pol": {
            "enabled": false,
            "max": 20,
            "base": 10
          },
          "cha": {
            "enabled": true,
            "max": 20,
            "base": 10
          },
          "agi": {
            "enabled": true,
            "max": 20,
            "base": 10
          },
          "log": {
            "enabled": false,
            "max": 20,
            "base": 10
          },
          "wis": {
            "enabled": true,
            "max": 20,
            "base": 10
          },
          "luck": {
            "enabled": true,
            "max": 20,
            "base": 10
          }
        }
      }
    },
    {
      "char_ref_id": 84,
      "role": "mage",
      "snapshot": {
        "id": 84,
        "name": "하미",
        "summary": "침착하지만 굳센 의지를 지닌 모험가.",
        "tags": [
          "치유",
          "동양풍",
          "스팀펑크",
          "귀족",
          "낙천",
          "마법"
        ],
        "image_url": "/assets/char/d2615216b494.png",
        "archetype": "검사",
        "attributes_base": {
          "hp": {
            "enabled": true,
            "max": 100,
            "base": 80
          },
          "mp": {
            "enabled": true,
            "max": 80,
            "base": 30
          },
          "sp": {
            "enabled": true,
            "max": 60,
            "base": 20
          },
          "str": {
            "enabled": true,
            "max": 20,
            "base": 10
          },
          "int": {
            "enabled": true,
            "max": 20,
            "base": 10
          },
          "pol": {
            "enabled": false,
            "max": 20,
            "base": 10
          },
          "cha": {
            "enabled": true,
            "max": 20,
            "base": 10
          },
          "agi": {
            "enabled": true,
            "max": 20,
            "base": 10
          },
          "log": {
            "enabled": false,
            "max": 20,
            "base": 10
          },
          "wis": {
            "enabled": true,
            "max": 20,
            "base": 10
          },
          "luck": {
            "enabled": true,
            "max": 20,
            "base": 10
          }
        }
      }
    }
  ],
  "rules": {
    "success_base": 60,
    "difficulty_mod": {
      "easy": -10,
      "normal": 0,
      "hard": 10,
      "very_hard": 20
    },
    "ability_scale": 1,
    "attributes": {
      "hp": {
        "enabled": true,
        "max": 100,
        "base": 80
      },
      "mp": {
        "enabled": true,
        "max": 80,
        "base": 30
      },
      "sp": {
        "enabled": true,
        "max": 60,
        "base": 20
      },
      "str": {
        "enabled": true,
        "max": 20,
        "base": 10
      },
      "int": {
        "enabled": true,
        "max": 20,
        "base": 10
      },
      "pol": {
        "enabled": false,
        "max": 20,
        "base": 10
      },
      "cha": {
        "enabled": true,
        "max": 20,
        "base": 10
      },
      "agi": {
        "enabled": true,
        "max": 20,
        "base": 10
      },
      "log": {
        "enabled": false,
        "max": 20,
        "base": 10
      },
      "wis": {
        "enabled": true,
        "max": 20,
        "base": 10
      },
      "luck": {
        "enabled": true,
        "max": 20,
        "base": 10
      }
    },
    "dice": {
      "count": 5,
      "faces": 20
    },
    "damage": {
      "str_multiplier": 1,
      "flat_bonus": 0,
      "success_bonus_scale": 1,
      "on_fail_zero": true
    },
    "critical": {
      "threshold_ratio": 0.95,
      "multiplier": 2,
      "base_bonus_multiplier": 1.5
    },
    "events": {
      "base_chance": 70,
      "area_mod": {
        "town": -20,
        "field": 0,
        "dungeon": 20
      },
      "combat_weights": {
        "bandits": 40,
        "monsters": 40,
        "soldiers": 20
      }
    }
  },
  "background_image_path": "/assets/game/dae05619a06f4ff588ccf6c950d695c5.png",
  "img_hash": "92d14a70cecf377db0d06ef0c254ab05",
  "status": "active",
  "reg_user": "113602532019760492929",
  "created_at": {
    "$date": "2025-12-12T06:10:58.605Z"
  },
  "updated_at": {
    "$date": "2025-12-12T06:10:58.605Z"
  }
}


