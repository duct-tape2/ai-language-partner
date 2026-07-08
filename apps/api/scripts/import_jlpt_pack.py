"""Convert the JLPT N4 final review pack (audit CSVs) into a content bundle
and import it through the running API's /v1/content/validate + /v1/content/import.

Deterministic conversion, no LLM. Source of truth:
  - 전체_문항_대조표.csv  (570 non-listening question items: section/answer/mark/difficulty)
  - 모의고사_어휘_커버리지.csv (per-question vocab: lemma/reading/Korean meaning)

Usage:
  python3 scripts/import_jlpt_pack.py                 # validate + import dry-run only
  python3 scripts/import_jlpt_pack.py --apply         # validate + real import (upsert, replaceExisting=false)
  python3 scripts/import_jlpt_pack.py --base-url http://127.0.0.1:8000 --pack-dir /path/to/JLPT_N4_final_review_pack

Admin key is read from AI_LANGUAGE_PARTNER_ADMIN_KEY (falls back to the dev-mode default).
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import urllib.error
import urllib.request
from collections import defaultdict
from pathlib import Path

DEFAULT_PACK_DIR = Path.home() / "Downloads" / "JLPT_N4_final_review_pack"
QUESTIONS_CSV = "전체_문항_대조표.csv"
VOCAB_CSV = "모의고사_어휘_커버리지.csv"

COURSE_ID = "jlpt_n4_final_review_ko"
PERSONA_ID = "haruka"  # JLPT-focused teacher persona shipped in the seed catalog

SECTION_KO = {"語彙": "문자어휘", "文法": "문법", "読解": "독해"}
SECTION_ORDER = ["語彙", "文法", "読解"]
MARK_TAG = {"x": "오답노트", "triangle": "애매했던문제", "known": "암기완료"}
CIRCLED = "①②③④⑤"


def set_slug(source_file: str, set_id: str) -> str:
    if source_file == "V18":
        return set_id.lower()  # set01..set08
    return "jitsu" + set_id.replace("제", "").replace("회", "")  # 제1회 -> jitsu1


def set_label(source_file: str, set_id: str) -> str:
    if source_file == "V18":
        return f"모의고사 {set_id}"
    return f"실전 {set_id}"


def strip_choice_prefix(answer: str) -> str:
    text = answer.strip()
    while text and (text[0] in CIRCLED or text[0].isspace()):
        text = text[1:]
    return text.strip() or answer.strip()


def load_rows(pack_dir: Path):
    q_path = pack_dir / "audit" / QUESTIONS_CSV
    v_path = pack_dir / "audit" / VOCAB_CSV
    questions = [
        r
        for r in csv.DictReader(open(q_path, encoding="utf-8"))
        if r["include_target"] == "TRUE" and r["is_listening"] == "FALSE"
    ]
    vocab = defaultdict(list)
    for r in csv.DictReader(open(v_path, encoding="utf-8")):
        vocab[(r["source_file"], r["set_id"], r["section"], r["original_no"])].append(r)
    return questions, vocab


def korean_hint(question, vocab_rows, ja_phrase: str) -> str:
    if vocab_rows:
        # Prefer a lemma actually contained in the answer phrase.
        matched = [v for v in vocab_rows if v["lemma_jp"] and v["lemma_jp"] in ja_phrase]
        pool = matched or vocab_rows
        meanings = []
        for v in pool:
            m = v["meaning_ko"].strip()
            if m and m not in meanings:
                meanings.append(m)
            if len(meanings) >= 3:
                break
        if meanings:
            return " / ".join(meanings)
    return f"JLPT N4 {SECTION_KO[question['section']]} 정답 표현 복습"


def build_room(question, vocab_rows) -> dict:
    src = question["source_file"]
    slug = set_slug(src, question["set_id"])
    label = set_label(src, question["set_id"])
    section_ko = SECTION_KO[question["section"]]
    no = int(question["original_no"])
    ja = strip_choice_prefix(question["answer"])
    alt = []
    for v in vocab_rows:
        lemma, reading = v["lemma_jp"].strip(), v["reading"].strip()
        if not lemma:
            continue
        phrase = f"{lemma}（{reading}）" if reading and reading != lemma else lemma
        if phrase not in alt:
            alt.append(phrase)
        if len(alt) >= 4:
            break
    mark = question["mark_status"]
    room = {
        "id": f"n4fr_{slug}_q{no:02d}_{question['section'][0]}",
        "title": f"[N4 {section_ko}] {label} {no}번",
        "primaryPhraseKo": korean_hint(question, vocab_rows, ja),
        "primaryPhraseJa": ja,
        "alternativePhrasesJa": alt,
        "personaId": PERSONA_ID,
        "scenario": f"JLPT N4 {section_ko} 복습 ({label} {no}번, 난이도 {question['difficulty']})",
        "openingMessage": (
            f"{label} {no}번({section_ko}) 복습이야. 정답 표현 「{ja}」를 소리 내어 읽고, 뜻을 떠올려 보자."
        ),
        "tags": ["JLPT", "N4", section_ko, MARK_TAG.get(mark, mark)],
        # Extra metadata (schema allows additional properties)
        "jlptLevel": "N4",
        "sourceSet": f"{src}/{question['set_id']}",
        "questionNo": no,
        "globalNo": int(question["global_no"]),
        "markStatus": mark,
        "difficulty": question["difficulty"],
        "topicSlug": question["title_or_topic"],
        "answerRaw": question["answer"],
    }
    return room


def build_bundle(pack_dir: Path) -> dict:
    questions, vocab = load_rows(pack_dir)
    rooms = []
    by_section_set = defaultdict(list)  # (section, source, set_id) -> room ids
    seen_ids = set()
    for q in questions:
        key = (q["source_file"], q["set_id"], q["section"], q["original_no"])
        room = build_room(q, vocab.get(key, []))
        if room["id"] in seen_ids:
            raise SystemExit(f"duplicate room id generated: {room['id']}")
        seen_ids.add(room["id"])
        rooms.append(room)
        by_section_set[(q["section"], q["source_file"], q["set_id"])].append(room["id"])

    units = []
    for unit_order, section in enumerate(SECTION_ORDER, start=1):
        section_ko = SECTION_KO[section]
        lessons = []
        lesson_order = 0
        for (sec, src, set_id), room_ids in sorted(
            by_section_set.items(), key=lambda kv: (kv[0][1] != "V18", kv[0][2])
        ):
            if sec != section:
                continue
            lesson_order += 1
            slug = set_slug(src, set_id)
            lessons.append(
                {
                    "id": f"lesson_n4fr_{SECTION_KO[section]}_{slug}",
                    "title": f"{section_ko} · {set_label(src, set_id)} ({len(room_ids)}문항)",
                    "order": lesson_order,
                    "practiceRoomIds": room_ids,
                }
            )
        units.append(
            {
                "id": f"unit_n4fr_{section_ko}",
                "title": f"JLPT N4 {section_ko} 복습",
                "order": unit_order,
                "skillTags": ["JLPT", "N4", section_ko],
                "lessons": lessons,
            }
        )

    course = {
        "id": COURSE_ID,
        "title": f"JLPT N4 총정리 {len(rooms)}제 (오답·핵심 복습)",
        "targetLanguage": "ja",
        "nativeLanguage": "ko",
        "level": "jlpt_n4",
        "descriptionKo": (
            "실제 N4 모의고사 8세트 + 실전 2회분에서 추출한 비청해 570문항 복습 코스. "
            "x(오답)/△(애매)/암기완료 표시와 문항별 핵심 어휘(읽기·뜻)를 담았다."
        ),
        "units": units,
    }
    return {"courses": [course], "practiceRooms": rooms}


def post_json(base_url: str, path: str, payload: dict, admin_key: str):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        base_url.rstrip("/") + path,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-Admin-Key": admin_key,
            "X-Admin-Role": "editor",
            "X-Admin-User": "jlpt-pack-importer",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        return err.code, json.loads(err.read().decode("utf-8"))


def summarize_report(report: dict) -> str:
    errors = report.get("errors", [])
    warnings = report.get("warnings", [])
    head = [f"counts={report.get('counts')}", f"errors={len(errors)}", f"warnings={len(warnings)}"]
    lines = ["; ".join(head)]
    for issue in errors[:10]:
        lines.append(f"  ERROR {issue.get('code')}: {issue.get('message')}")
    if len(errors) > 10:
        lines.append(f"  ... and {len(errors) - 10} more errors")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack-dir", default=str(DEFAULT_PACK_DIR))
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--apply", action="store_true", help="actually import (default: dry-run only)")
    parser.add_argument("--dump", help="optional path to write the generated bundle JSON")
    args = parser.parse_args()

    admin_key = os.environ.get("AI_LANGUAGE_PARTNER_ADMIN_KEY") or "local-dev-admin"

    bundle = build_bundle(Path(args.pack_dir))
    n_rooms = len(bundle["practiceRooms"])
    n_lessons = sum(len(u["lessons"]) for u in bundle["courses"][0]["units"])
    print(f"bundle built: 1 course / {len(bundle['courses'][0]['units'])} units / {n_lessons} lessons / {n_rooms} practice rooms")

    if args.dump:
        Path(args.dump).write_text(json.dumps(bundle, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"bundle written to {args.dump}")

    status, body = post_json(args.base_url, "/v1/content/validate", bundle, admin_key)
    print(f"validate: HTTP {status} ok={body.get('ok')}")
    print(summarize_report(body.get("report", body.get("detail", {}).get("report", {}))))
    if status != 200 or not body.get("ok"):
        return 1

    import_payload = {**bundle, "dryRun": True, "replaceExisting": False}
    status, body = post_json(args.base_url, "/v1/content/import", import_payload, admin_key)
    ok = body.get("ok")
    print(f"import dry-run: HTTP {status} ok={ok} importedCounts={body.get('importedCounts')}")
    if status != 200:
        print(summarize_report(body.get("detail", {}).get("report", {})))
        return 1

    if not args.apply:
        print("dry-run only. rerun with --apply to import for real.")
        return 0

    import_payload["dryRun"] = False
    status, body = post_json(args.base_url, "/v1/content/import", import_payload, admin_key)
    print(f"import apply: HTTP {status} ok={body.get('ok')} importedCounts={body.get('importedCounts')}")
    if status == 200:
        version = body.get("version", {})
        print(f"content version: id={version.get('id')} status={version.get('status')} source={version.get('source')}")
        return 0
    print(summarize_report(body.get("detail", {}).get("report", {})))
    return 1


if __name__ == "__main__":
    sys.exit(main())
