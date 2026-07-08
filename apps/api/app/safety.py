from __future__ import annotations

import re
from typing import Dict, Optional


COPYRIGHT_OR_REAL_PERSON_PATTERNS = [
    r"고죠",
    r"사토루",
    r"gojo",
    r"나루토",
    r"루피",
    r"도라에몽",
    r"짱구",
    r"아이유",
    r"뉴진스",
    r"성우\s*목소리",
    r"목소리\s*클론",
]

MINOR_PATTERNS = [r"미성년", r"중학생", r"고등학생", r"여고생", r"남고생"]
SEXUAL_PATTERNS = [r"섹스", r"성적", r"야한", r"노골", r"19금", r"롤플레이.*연인", r"가상\s*연인"]


def assess_text(text: Optional[str]) -> Dict[str, object]:
    raw_text = text or ""
    lowered = raw_text.lower()
    has_minor = any(re.search(pattern, lowered) for pattern in MINOR_PATTERNS)
    has_sexual = any(re.search(pattern, lowered) for pattern in SEXUAL_PATTERNS)
    if has_sexual or (has_minor and has_sexual):
        return {
            "action": "block",
            "policyKey": "explicit_or_minor_sexual_context",
            "message": (
                "이 앱은 일본어 회화 학습용이라 성적/미성년자 맥락의 롤플레이는 도와줄 수 없어요. "
                "대신 안전한 일상 회화 표현으로 바꿔 연습할게요."
            ),
        }

    if any(re.search(pattern, lowered) for pattern in COPYRIGHT_OR_REAL_PERSON_PATTERNS):
        transformed = re.sub(
            "|".join(COPYRIGHT_OR_REAL_PERSON_PATTERNS),
            "장난기 있는 오리지널 선배 타입",
            raw_text,
            flags=re.IGNORECASE,
        )
        return {
            "action": "transform",
            "policyKey": "copyright_or_real_person_archetype",
            "message": "유명 캐릭터/실존 인물을 그대로 복제하지 않고 오리지널 archetype으로 바꿨어요.",
            "transformedText": transformed,
        }

    return {"action": "allow", "policyKey": None, "message": ""}
