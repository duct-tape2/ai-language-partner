#!/usr/bin/env python3
"""Render outreach queue items into copy/paste-ready messages."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "docs" / "community" / "OUTREACH_QUEUE.json"
OUTPUT = ROOT / "docs" / "community" / "OUTREACH_MESSAGES.md"

TEMPLATES = {
    "short-korean": """한국어권 일본어 학습자를 위한 local-first OSS를 공개했습니다.
런타임 LLM 없이 사전 저작 dialogue bank + 로컬 STT/TTS로 회화 연습을 만드는 프로젝트입니다.

아래 이슈에서 작은 기여를 찾고 있어요.
추천 이슈/목록:
{issue_query}

5분 첫 PR 가이드:
https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIVE_MINUTE_FIRST_PR.md

첫 이슈 매처:
https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIRST_ISSUE_MATCHER.md

기여자 페이지:
https://duct-tape2.github.io/ai-language-partner/ko/

브라우저 데모:
https://duct-tape2.github.io/ai-language-partner/demo/

기여자 모집 페이지:
https://duct-tape2.github.io/ai-language-partner/community/CALL_FOR_CONTRIBUTORS.html

이슈 색인:
https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/STARTER_ISSUE_INDEX.md

기여자 안내:
https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/CONTRIBUTOR_LANDING.md

질문/첫 PR 상담:
https://github.com/duct-tape2/ai-language-partner/discussions/53

원하는 이슈가 있으면 `/claim`이라고 댓글을 남기면 짧은 PR 체크리스트가 자동으로 달립니다.

생성 음성, 로컬 엔진, private data 없이 문서/언어 검수 PR만으로도 실제 도움이 됩니다.""",
    "short-japanese": """韓国語話者向けの日本語学習アプリ OSS を公開しました。
実行時に LLM を呼ばず、事前作成の dialogue bank とローカル STT/TTS で会話練習を行う local-first プロジェクトです。

以下の issue で小さな貢献を募集しています。
おすすめ issue:
{issue_query}

5分で始める最初の PR:
https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIVE_MINUTE_FIRST_PR.md

First issue matcher:
https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIRST_ISSUE_MATCHER.md

Contributor page:
https://duct-tape2.github.io/ai-language-partner/ja/

ブラウザデモ:
https://duct-tape2.github.io/ai-language-partner/demo/

コントリビューター募集ページ:
https://duct-tape2.github.io/ai-language-partner/community/CALL_FOR_CONTRIBUTORS.html

Starter issue index:
https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/STARTER_ISSUE_INDEX.md

Contributor landing:
https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/CONTRIBUTOR_LANDING.md

First PR help desk:
https://github.com/duct-tape2/ai-language-partner/discussions/53

気になる issue があれば `/claim` とコメントすると、短い PR checklist が自動返信されます。

生成音声や private data は不要です。日本語の自然さ、初級者向け表現、ドキュメント改善などの PR を歓迎します。""",
    "short-english": """I opened ai-language-partner, a local-first Japanese speaking practice app for Korean learners.
The core loop avoids runtime LLM calls: local STT, reviewed dialogue-bank lines, and local TTS assets.

I'm looking for a small, useful contribution from {audience}.
Suggested issue/list:
{issue_query}

Five-minute first PR guide:
https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIVE_MINUTE_FIRST_PR.md

First issue matcher:
https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIRST_ISSUE_MATCHER.md

Contributor page:
https://duct-tape2.github.io/ai-language-partner/

Hosted web demo:
https://duct-tape2.github.io/ai-language-partner/demo/

Contributor call:
https://duct-tape2.github.io/ai-language-partner/community/CALL_FOR_CONTRIBUTORS.html

Starter issue index:
https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/STARTER_ISSUE_INDEX.md

Contributor landing:
https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/CONTRIBUTOR_LANDING.md

First PR help desk:
https://github.com/duct-tape2/ai-language-partner/discussions/53

If an issue looks good, comment `/claim` on it and the repo will reply with a short PR checklist.

Docs, content review, accessibility, API examples, and focused tests all help. No generated audio, local engines, private data, or API keys are needed for a useful first PR.""",
}


def render_message(item: dict[str, object]) -> str:
    template_name = str(item["message_template"])
    template = TEMPLATES.get(template_name)
    if template is None:
        raise ValueError(f"unknown message_template: {template_name}")
    return template.format(
        audience=str(item["audience"]),
        issue_query=str(item["issue_query"]),
    )


def main(argv: list[str]) -> int:
    output = OUTPUT
    if len(argv) > 2:
        print("usage: render_outreach_messages.py [output_path]", file=sys.stderr)
        return 2
    if len(argv) == 2:
        output = Path(argv[1])

    payload = json.loads(QUEUE.read_text(encoding="utf-8"))
    items = payload.get("items")
    if not isinstance(items, list):
        print("OUTREACH_QUEUE.json items must be a list", file=sys.stderr)
        return 1

    lines = [
        "# Outreach Messages",
        "",
        "Copy these manually and tailor them to each community. Do not mass-post",
        "identical messages. A posted message is not Claude for OSS evidence; only",
        "useful merged external PRs count.",
        "",
        f"- Source queue: `{QUEUE.relative_to(ROOT)}`",
        f"- Items: `{len(items)}`",
        "",
    ]

    for item in items:
        item_id = str(item["id"])
        status = str(item["status"])
        posted_url = str(item["posted_url"])
        lines.extend(
            [
                f"## {item_id}: {item['audience']}",
                "",
                f"- Lane: `{item['lane']}`",
                f"- Status: `{status}`",
                f"- Posted URL: `{posted_url or 'TBD'}`",
                f"- Notes: {item['notes']}",
                "",
                "```text",
                render_message(item),
                "```",
                "",
            ]
        )

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")
    print(f"rendered {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
