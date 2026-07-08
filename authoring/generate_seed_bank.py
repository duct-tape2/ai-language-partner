from __future__ import annotations

import base64
import csv
import hashlib
import json
import math
import struct
import wave
import zipfile
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AUTHORING_ROOT = PROJECT_ROOT / "authoring"
SCENARIO_ROOT = AUTHORING_ROOT / "scenarios"
PACKS_ROOT = PROJECT_ROOT / "packs"
VOICE_MAP = json.loads((PROJECT_ROOT / "apps" / "api" / "app" / "persona_voices.json").read_text(encoding="utf-8"))
PACK_VERSION = "v1"

PERSONAS = {
    "yui": {"name": "유이", "ja": "ゆい", "tone": "친근하고 부드러운 친구"},
    "haruka": {"name": "하루카 센세", "ja": "はるか先生", "tone": "차분하고 정확한 선생님"},
    "ren": {"name": "렌 선배", "ja": "レン先輩", "tone": "장난기 있지만 실전적인 선배"},
}

TOPICS = {
    "greetings_intro": {
        "title": "인사·자기소개",
        "n5": [
            ("まずは自然にあいさつしましょう。", "먼저 자연스럽게 인사해요.", [("こんにちは", "안녕하세요"), ("はじめまして", "처음 뵙겠습니다")]),
            ("名前を短く言ってみましょう。", "이름을 짧게 말해요.", [("私はミンです", "저는 민입니다"), ("ミンといいます", "민이라고 합니다")]),
            ("出身も一言で言えます。", "출신도 한마디로 말할 수 있어요.", [("韓国から来ました", "한국에서 왔습니다"), ("ソウルに住んでいます", "서울에 살고 있습니다")]),
            ("勉強していることを伝えましょう。", "공부 중이라는 말을 전해요.", [("日本語を勉強しています", "일본어를 공부하고 있습니다"), ("日本語を少し話せます", "일본어를 조금 말할 수 있습니다")]),
            ("相手に会えてうれしい気持ちを足します。", "만나서 반가운 마음을 더해요.", [("会えてうれしいです", "만나서 기쁩니다"), ("話せてうれしいです", "이야기할 수 있어서 기쁩니다")]),
            ("最後はやわらかく締めましょう。", "마지막은 부드럽게 마무리해요.", [("よろしくお願いします", "잘 부탁드립니다"), ("また話したいです", "또 이야기하고 싶습니다")]),
        ],
        "n4": [
            ("自己紹介に理由を一つ足しましょう。", "자기소개에 이유를 하나 더해요.", [("日本のドラマが好きで勉強しています", "일본 드라마를 좋아해서 공부하고 있습니다"), ("旅行で話したくて勉強しています", "여행에서 말하고 싶어서 공부하고 있습니다")]),
            ("最近の目標を言ってみましょう。", "최근 목표를 말해요.", [("自然に会話できるようになりたいです", "자연스럽게 대화할 수 있게 되고 싶습니다"), ("聞き取りをもっと練習したいです", "듣기를 더 연습하고 싶습니다")]),
            ("相手にも質問を返します。", "상대에게도 질문을 돌려줘요.", [("お名前を聞いてもいいですか", "성함을 여쭤봐도 될까요"), ("どちらから来ましたか", "어디에서 오셨나요")]),
            ("少しくだけた言い方も試します。", "조금 편한 말투도 시도해요.", [("日本語はまだ勉強中なんです", "일본어는 아직 공부 중이에요"), ("ゆっくり話してもらえると助かります", "천천히 말해주시면 도움이 됩니다")]),
            ("会話を続けたい意思を出します。", "대화를 이어가고 싶다는 뜻을 말해요.", [("よかったら少し話しませんか", "괜찮으면 조금 이야기하지 않을래요"), ("おすすめの表現を教えてください", "추천 표현을 알려주세요")]),
            ("丁寧に締めます。", "정중하게 마무리해요.", [("今日は話せてよかったです", "오늘 이야기할 수 있어서 좋았습니다"), ("これからもよろしくお願いします", "앞으로도 잘 부탁드립니다")]),
        ],
    },
    "today": {
        "title": "오늘 뭐했어",
        "n5": [
            ("今日の気分から言ってみましょう。", "오늘 기분부터 말해요.", [("今日は疲れました", "오늘은 피곤했습니다"), ("今日は楽しかったです", "오늘은 즐거웠습니다")]),
            ("したことを一つ足します。", "한 일을 하나 더해요.", [("仕事をしました", "일을 했습니다"), ("学校に行きました", "학교에 갔습니다")]),
            ("場所も言えます。", "장소도 말할 수 있어요.", [("家で休みました", "집에서 쉬었습니다"), ("カフェに行きました", "카페에 갔습니다")]),
            ("人と会ったかを話します。", "사람을 만났는지 말해요.", [("友達に会いました", "친구를 만났습니다"), ("一人で過ごしました", "혼자 보냈습니다")]),
            ("今の状態を短く言います。", "지금 상태를 짧게 말해요.", [("少し眠いです", "조금 졸립니다"), ("まだ元気です", "아직 괜찮습니다")]),
            ("明日の予定で締めます。", "내일 일정으로 마무리해요.", [("明日は早く起きます", "내일은 일찍 일어납니다"), ("明日も勉強します", "내일도 공부합니다")]),
        ],
        "n4": [
            ("理由をつけて一文にしましょう。", "이유를 붙여 한 문장으로 만들어요.", [("仕事が忙しくて疲れました", "일이 바빠서 피곤했습니다"), ("よく寝たので元気です", "잘 자서 괜찮습니다")]),
            ("時間の流れを入れます。", "시간 흐름을 넣어요.", [("朝から会議がありました", "아침부터 회의가 있었습니다"), ("昼すぎに買い物へ行きました", "오후에 장보러 갔습니다")]),
            ("気持ちをもう少し自然にします。", "감정을 조금 더 자연스럽게 말해요.", [("ちょっと大変でした", "조금 힘들었습니다"), ("思ったより楽でした", "생각보다 편했습니다")]),
            ("相手に聞き返します。", "상대에게 되물어요.", [("そちらはどうでしたか", "그쪽은 어땠나요"), ("今日は何をしましたか", "오늘은 무엇을 했나요")]),
            ("次の行動を言います。", "다음 행동을 말해요.", [("これから少し休みます", "이제 조금 쉴 겁니다"), ("あとで復習しようと思います", "나중에 복습하려고 합니다")]),
            ("自然な締めの一言です。", "자연스러운 마무리 한마디예요.", [("明日はもう少し余裕がほしいです", "내일은 조금 더 여유가 있으면 좋겠습니다"), ("今日は早めに寝るつもりです", "오늘은 일찍 잘 생각입니다")]),
        ],
    },
    "food_order": {
        "title": "음식 주문",
        "n5": [
            ("店員さんに注文してみましょう。", "점원에게 주문해요.", [("ラーメンをください", "라멘을 주세요"), ("これをください", "이것을 주세요")]),
            ("飲み物も頼めます。", "음료도 부탁할 수 있어요.", [("水をお願いします", "물을 부탁합니다"), ("お茶をください", "차를 주세요")]),
            ("数を言います。", "수량을 말해요.", [("一つください", "하나 주세요"), ("二つお願いします", "두 개 부탁합니다")]),
            ("苦手な味を伝えます。", "싫어하는 맛을 전해요.", [("辛くしないでください", "맵게 하지 말아 주세요"), ("ねぎは入れないでください", "파는 넣지 말아 주세요")]),
            ("おすすめを聞きます。", "추천을 물어요.", [("おすすめは何ですか", "추천은 무엇인가요"), ("人気のメニューはどれですか", "인기 메뉴는 어느 것인가요")]),
            ("会計で締めます。", "계산으로 마무리해요.", [("会計お願いします", "계산 부탁합니다"), ("カードで払えますか", "카드로 낼 수 있나요")]),
        ],
        "n4": [
            ("丁寧に注文を始めます。", "정중하게 주문을 시작해요.", [("注文してもいいですか", "주문해도 될까요"), ("このセットを一つお願いします", "이 세트를 하나 부탁합니다")]),
            ("条件をつけます。", "조건을 붙여요.", [("辛さを少なめにできますか", "매운맛을 약하게 할 수 있나요"), ("ご飯を少なめにしてください", "밥을 적게 해 주세요")]),
            ("アレルギーを伝えます。", "알레르기를 전해요.", [("卵が入っていますか", "달걀이 들어 있나요"), ("えびは食べられません", "새우는 먹을 수 없습니다")]),
            ("待ち時間を聞きます。", "대기 시간을 물어요.", [("どのくらい時間がかかりますか", "시간이 얼마나 걸리나요"), ("すぐできますか", "금방 되나요")]),
            ("味の感想を言います。", "맛 감상을 말해요.", [("とてもおいしいです", "정말 맛있습니다"), ("思ったより辛いです", "생각보다 맵습니다")]),
            ("持ち帰りを頼みます。", "포장을 부탁해요.", [("持ち帰りにできますか", "포장할 수 있나요"), ("残りを包んでもらえますか", "남은 것을 싸 주실 수 있나요")]),
        ],
    },
    "hobbies": {
        "title": "취미",
        "n5": [
            ("好きなことを言ってみましょう。", "좋아하는 것을 말해요.", [("映画が好きです", "영화를 좋아합니다"), ("音楽が好きです", "음악을 좋아합니다")]),
            ("よくすることを言います。", "자주 하는 것을 말해요.", [("音楽を聞きます", "음악을 듣습니다"), ("本を読みます", "책을 읽습니다")]),
            ("週末の行動です。", "주말 행동이에요.", [("週末に散歩します", "주말에 산책합니다"), ("友達とゲームをします", "친구와 게임을 합니다")]),
            ("頻度を足します。", "빈도를 더해요.", [("毎日少し見ます", "매일 조금 봅니다"), ("ときどき料理します", "가끔 요리합니다")]),
            ("相手にも聞きます。", "상대에게도 물어요.", [("趣味は何ですか", "취미는 무엇인가요"), ("何が好きですか", "무엇을 좋아하나요")]),
            ("一緒にする提案です。", "같이 하자는 제안이에요.", [("一緒に見ましょう", "같이 봅시다"), ("今度一緒に行きましょう", "다음에 같이 갑시다")]),
        ],
        "n4": [
            ("理由をつけて話します。", "이유를 붙여 말해요.", [("映画を見るとリラックスできます", "영화를 보면 릴랙스할 수 있습니다"), ("音楽を聞くのが一番好きです", "음악 듣는 것을 제일 좋아합니다")]),
            ("最近はまっていることです。", "요즘 빠진 것을 말해요.", [("最近日本のドラマにはまっています", "요즘 일본 드라마에 빠져 있습니다"), ("最近写真を撮るのが楽しいです", "요즘 사진 찍는 것이 재미있습니다")]),
            ("経験を言います。", "경험을 말해요.", [("去年からギターを始めました", "작년부터 기타를 시작했습니다"), ("子どものころから絵を描いています", "어릴 때부터 그림을 그리고 있습니다")]),
            ("好みを比べます。", "취향을 비교해요.", [("にぎやかな場所より静かな場所が好きです", "시끄러운 곳보다 조용한 곳을 좋아합니다"), ("映画よりアニメをよく見ます", "영화보다 애니를 자주 봅니다")]),
            ("おすすめを求めます。", "추천을 구해요.", [("おすすめの映画はありますか", "추천 영화가 있나요"), ("初心者にいい趣味は何ですか", "초보자에게 좋은 취미는 무엇인가요")]),
            ("次の約束につなげます。", "다음 약속으로 이어요.", [("よかったら今度一緒に行きませんか", "괜찮으면 다음에 같이 가지 않을래요"), ("時間があるときに教えてください", "시간 있을 때 알려주세요")]),
        ],
    },
    "weather_seasons": {
        "title": "날씨·계절",
        "n5": [
            ("今日の天気を言います。", "오늘 날씨를 말해요.", [("今日は暑いです", "오늘은 덥습니다"), ("今日は寒いです", "오늘은 춥습니다")]),
            ("雨や雪も言えます。", "비와 눈도 말할 수 있어요.", [("雨が降っています", "비가 오고 있습니다"), ("雪が降っています", "눈이 오고 있습니다")]),
            ("好きな季節です。", "좋아하는 계절이에요.", [("春が好きです", "봄을 좋아합니다"), ("秋が好きです", "가을을 좋아합니다")]),
            ("苦手な季節です。", "어려운 계절이에요.", [("夏は苦手です", "여름은 어렵습니다"), ("冬は寒すぎます", "겨울은 너무 춥습니다")]),
            ("服装を話します。", "옷차림을 말해요.", [("コートを着ます", "코트를 입습니다"), ("傘を持っていきます", "우산을 가져갑니다")]),
            ("明日の天気を聞きます。", "내일 날씨를 물어요.", [("明日の天気はどうですか", "내일 날씨는 어떤가요"), ("明日は雨ですか", "내일은 비인가요")]),
        ],
        "n4": [
            ("体感を自然に言います。", "체감 날씨를 자연스럽게 말해요.", [("今日は蒸し暑いですね", "오늘은 무덥네요"), ("風が強くて寒く感じます", "바람이 강해서 춥게 느껴집니다")]),
            ("予定との関係を話します。", "일정과의 관계를 말해요.", [("雨なら家で過ごすつもりです", "비라면 집에서 보낼 생각입니다"), ("晴れたら散歩したいです", "맑으면 산책하고 싶습니다")]),
            ("季節の好みを詳しくします。", "계절 취향을 자세히 말해요.", [("桜が咲くので春が好きです", "벚꽃이 피어서 봄을 좋아합니다"), ("涼しくなるので秋が好きです", "선선해져서 가을을 좋아합니다")]),
            ("注意を伝えます。", "주의를 전해요.", [("今日は傘を持ったほうがいいです", "오늘은 우산을 가져가는 편이 좋습니다"), ("夜は冷えるかもしれません", "밤에는 추워질지도 모릅니다")]),
            ("相手の地域を聞きます。", "상대 지역을 물어요.", [("そちらの天気はどうですか", "그쪽 날씨는 어떤가요"), ("東京も暑いですか", "도쿄도 덥나요")]),
            ("自然な感想で締めます。", "자연스러운 감상으로 마무리해요.", [("早く涼しくなってほしいです", "빨리 선선해졌으면 좋겠습니다"), ("この季節は歩きやすいですね", "이 계절은 걷기 좋네요")]),
        ],
    },
}

FILLERS = {
    "yui": {
        "filler": ["うん、いい感じ。", "その調子だよ。", "今の自然だった。", "ちょっと待ってね。", "聞こえてるよ。"],
        "confirm": ["今のはこういう意味で合ってる？", "もう一回だけ言ってみる？", "この表現を選ぶ感じでいい？", "近いよ、少し確認しよう。", "どっちの意味か教えて。"],
        "fallback": ["ごめん、今の言い方は拾えなかった。", "候補から近いものを選んでみて。", "短く言い直してくれる？", "もう少しゆっくりお願い。", "今はこの場面の表現で練習しよう。"],
    },
    "haruka": {
        "filler": ["はい、確認します。", "発音は落ち着いています。", "文の形はいいです。", "少し待ってください。", "聞き取れています。"],
        "confirm": ["今の意図はこちらで合っていますか。", "もう一度、同じ内容で言えますか。", "この選択肢に近いでしょうか。", "意味は近いので確認します。", "どの表現を使いたいですか。"],
        "fallback": ["すみません、現在の場面では判断できませんでした。", "候補文に近い形で言い直しましょう。", "短い文にしてもう一度お願いします。", "ゆっくり発話してください。", "この練習では場面内の表現に戻ります。"],
    },
    "ren": {
        "filler": ["お、いいね。", "今のノリ悪くない。", "そのまま行こう。", "ちょい待ち。", "聞こえてるぞ。"],
        "confirm": ["今の、こっちの意味で合ってる？", "もう一回いっとく？", "この返事を狙った感じ？", "近いから確認な。", "どっちで返したい？"],
        "fallback": ["悪い、今のは拾えなかった。", "候補に寄せてもう一回。", "短く言い直してみ。", "もう少しゆっくり頼む。", "いったんこの場面のセリフに戻ろう。"],
    },
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def stable_id(*parts: str) -> str:
    return "_".join(part.lower().replace("-", "_") for part in parts)


def expand_variants(text: str, ko: str) -> list[str]:
    compact = text.replace("を", "").replace("が", "").replace("は", "").replace("に", "").replace("です", "")
    variants = [
        text,
        text + "。",
        text.replace("です", ""),
        text.replace("ます", ""),
        compact,
        text.replace("ください", "お願いします"),
        text.replace("お願いします", "ください"),
        ko,
        ko.replace("습니다", "요"),
        text.replace("今日", "きょう").replace("日本語", "にほんご"),
    ]
    seen: list[str] = []
    for variant in variants:
        cleaned = variant.strip()
        if cleaned and cleaned not in seen:
            seen.append(cleaned)
    while len(seen) < 8:
        seen.append(f"{text} {len(seen) + 1}")
    return seen[:10]


def write_wav(path: Path, text: str, voice_id: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    sample_rate = 16000
    duration_ms = max(360, min(1100, len(text) * 38))
    frames = int(sample_rate * duration_ms / 1000)
    digest = int(hashlib.sha256(f"{voice_id}:{text}".encode("utf-8")).hexdigest()[:8], 16)
    frequency = 320 + digest % 360
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        data = bytearray()
        for index in range(frames):
            envelope = min(1.0, index / 800) * min(1.0, (frames - index) / 1200)
            tone = math.sin(2 * math.pi * frequency * index / sample_rate)
            overtone = 0.28 * math.sin(2 * math.pi * frequency * 1.5 * index / sample_rate)
            value = int(12000 * envelope * (tone + overtone) / 1.28)
            data.extend(value.to_bytes(2, "little", signed=True))
        wav.writeframes(bytes(data))


def write_npy_float32(path: Path, rows: list[list[float]]) -> None:
    if not rows:
        rows = [[0.0]]
    row_count = len(rows)
    col_count = len(rows[0])
    header = str({"descr": "<f4", "fortran_order": False, "shape": (row_count, col_count)}).encode("latin1")
    padding = 16 - ((10 + len(header) + 1) % 16)
    with path.open("wb") as handle:
        handle.write(b"\x93NUMPY\x01\x00")
        handle.write(struct.pack("<H", len(header) + padding + 1))
        handle.write(header + b" " * padding + b"\n")
        for row in rows:
            for value in row:
                handle.write(struct.pack("<f", float(value)))


def embedding_for(text: str, size: int = 16) -> list[float]:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    values = [(digest[index] / 255.0) * 2 - 1 for index in range(size)]
    norm = math.sqrt(sum(value * value for value in values)) or 1.0
    return [round(value / norm, 6) for value in values]


def persona_line(persona_id: str, base_ja: str) -> str:
    if persona_id == "yui":
        return base_ja + " いっしょに言ってみよ。"
    if persona_id == "haruka":
        return base_ja + " ゆっくり正確に確認しましょう。"
    return base_ja + " いい感じに決めよう。"


def scenario_to_ink(scenario: dict) -> str:
    lines = [f"// {scenario['title']} / {scenario['level']} / {scenario['personaId']}", f"=== {scenario['scenarioId']} ==="]
    for node in scenario["nodes"]:
        lines.append(f"{node['assistantText']} #line:{node['assistantLineId']} #ko:{node['assistantKo']}")
        for choice in node["choices"]:
            lines.append(f"+ [{choice['text']}] #line:{choice['lineId']} #ko:{choice['ko']}")
            lines.append(f"  -> {choice['nextNodeId']}")
        lines.append("")
    lines.append("-> END")
    return "\n".join(lines) + "\n"


def build() -> dict:
    SCENARIO_ROOT.mkdir(parents=True, exist_ok=True)
    PACKS_ROOT.mkdir(parents=True, exist_ok=True)
    all_variants: list[dict] = []
    summary = {"personaPacks": {}, "scenarioCount": 0, "variantCount": 0, "audioCount": 0}
    for persona_id in PERSONAS:
        persona_scenarios = []
        persona_audio = []
        persona_pack = PACKS_ROOT / persona_id / PACK_VERSION
        audio_root = persona_pack / "audio"
        persona_pack.mkdir(parents=True, exist_ok=True)
        (SCENARIO_ROOT / persona_id).mkdir(parents=True, exist_ok=True)
        voice_id = VOICE_MAP[persona_id]["emotions"]["default"]
        for topic_id, topic in TOPICS.items():
            for level_key in ["n5", "n4"]:
                scenario_id = stable_id(persona_id, topic_id, level_key)
                scenario = {
                    "scenarioId": scenario_id,
                    "personaId": persona_id,
                    "packVersion": PACK_VERSION,
                    "topicId": topic_id,
                    "title": topic["title"],
                    "level": level_key.upper(),
                    "nodes": [],
                }
                turns = topic[level_key]
                for index, (assistant_ja, assistant_ko, choices) in enumerate(turns, start=1):
                    node_id = f"{scenario_id}_node_{index:02d}"
                    next_node = f"{scenario_id}_node_{index + 1:02d}" if index < len(turns) else "END"
                    assistant_line_id = f"{scenario_id}_a{index:02d}"
                    assistant_text = persona_line(persona_id, assistant_ja)
                    audio_path = audio_root / f"{assistant_line_id}.wav"
                    write_wav(audio_path, assistant_text, voice_id)
                    persona_audio.append({"lineId": assistant_line_id, "path": str(audio_path.relative_to(persona_pack)), "category": "dialogue"})
                    node = {
                        "nodeId": node_id,
                        "assistantLineId": assistant_line_id,
                        "assistantText": assistant_text,
                        "assistantKo": assistant_ko,
                        "choices": [],
                    }
                    for choice_index, (choice_ja, choice_ko) in enumerate(choices, start=1):
                        suffix = chr(ord("a") + choice_index - 1)
                        line_id = f"{scenario_id}_u{index:02d}{suffix}"
                        choice = {"lineId": line_id, "text": choice_ja, "ko": choice_ko, "nextNodeId": next_node}
                        node["choices"].append(choice)
                        for variant in expand_variants(choice_ja, choice_ko):
                            all_variants.append(
                                {
                                    "personaId": persona_id,
                                    "packVersion": PACK_VERSION,
                                    "scenarioId": scenario_id,
                                    "nodeId": node_id,
                                    "lineId": line_id,
                                    "text": variant,
                                    "ko": choice_ko,
                                    "intent": "choice",
                                }
                            )
                    scenario["nodes"].append(node)
                persona_scenarios.append(scenario)
                (SCENARIO_ROOT / persona_id / f"{scenario_id}.ink").write_text(scenario_to_ink(scenario), encoding="utf-8")

        filler_manifest = []
        for category, lines in FILLERS[persona_id].items():
            for index, text in enumerate(lines, start=1):
                line_id = f"{persona_id}_{category}_{index:03d}"
                emotion = "confirm" if category == "confirm" else "fallback" if category == "fallback" else "default"
                filler_voice = VOICE_MAP[persona_id]["emotions"].get(emotion, voice_id)
                audio_path = audio_root / f"{line_id}.wav"
                write_wav(audio_path, text, filler_voice)
                item = {"lineId": line_id, "text": text, "path": str(audio_path.relative_to(persona_pack)), "category": category, "voiceUsed": filler_voice}
                persona_audio.append(item)
                filler_manifest.append(item)

        pack_variants = [row for row in all_variants if row["personaId"] == persona_id]
        with (persona_pack / "variants.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["personaId", "packVersion", "scenarioId", "nodeId", "lineId", "text", "ko", "intent"])
            writer.writeheader()
            writer.writerows(pack_variants)
        write_npy_float32(persona_pack / "embeddings.npy", [embedding_for(row["text"]) for row in pack_variants])
        story = {"schemaVersion": "dialogue_bank_story_v1", "personaId": persona_id, "packVersion": PACK_VERSION, "scenarios": persona_scenarios}
        (persona_pack / "story.json").write_text(json.dumps(story, ensure_ascii=False, indent=2), encoding="utf-8")
        manifest = {
            "schemaVersion": "dialogue_bank_manifest_v1",
            "personaId": persona_id,
            "packVersion": PACK_VERSION,
            "generatedAt": now_iso(),
            "runtimeLlmCalls": False,
            "ttsProvider": "local_mock_prebuilt",
            "voiceUsed": voice_id,
            "topics": sorted({scenario["topicId"] for scenario in persona_scenarios}),
            "levels": ["N5", "N4"],
            "scenarioCount": len(persona_scenarios),
            "lineCount": len(persona_audio),
            "audioCount": len(persona_audio),
            "variantCount": len(pack_variants),
            "audio": persona_audio,
            "filler": [item for item in filler_manifest if item["category"] == "filler"],
            "confirm": [item for item in filler_manifest if item["category"] == "confirm"],
            "fallback": [item for item in filler_manifest if item["category"] == "fallback"],
        }
        (persona_pack / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        with zipfile.ZipFile(persona_pack / "pack.zip", "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(item for item in persona_pack.rglob("*") if item.is_file() and item.name != "pack.zip"):
                archive.write(path, path.relative_to(persona_pack))
        summary["personaPacks"][persona_id] = {
            "scenarios": len(persona_scenarios),
            "variants": len(pack_variants),
            "audio": len(persona_audio),
            "packBytes": (persona_pack / "pack.zip").stat().st_size,
        }
        summary["scenarioCount"] += len(persona_scenarios)
        summary["audioCount"] += len(persona_audio)

    with (AUTHORING_ROOT / "variants.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["personaId", "packVersion", "scenarioId", "nodeId", "lineId", "text", "ko", "intent"])
        writer.writeheader()
        writer.writerows(all_variants)
    summary["variantCount"] = len(all_variants)
    (AUTHORING_ROOT / "seed_bank_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


if __name__ == "__main__":
    result = build()
    print(json.dumps(result, ensure_ascii=False, indent=2))
