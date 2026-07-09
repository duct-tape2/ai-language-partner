# Contributor Outreach Playbook

The goal is not to make the repository look active. The goal is to make it
genuinely easy for Korean/Japanese learners, language reviewers, Expo
developers, FastAPI developers, accessibility reviewers, and local-first AI
builders to make useful small contributions.

## Weekly Cadence

Week 1:

- Publish the repo and seed at least 30 issues.
- Pin 10 issues that are low-context and reviewable in under one hour.
- Ask for language/content review first; it matches the project domain and is
  easier for non-coders to contribute meaningfully.
- Work through `docs/community/OUTREACH_QUEUE.json` in small batches and fill
  `posted_url` only after a real public post exists.

Week 2:

- Post 5 before/after examples from merged docs or content PRs.
- Invite Expo and accessibility contributors to pick mobile polish issues.
- Keep maintainer response time under 24 hours for new contributor PRs.

Week 3:

- Add a short "first contributors" note to the README.
- Open a second issue batch based on what contributors actually ask about.
- Prioritize tests, API examples, and setup docs so the repo becomes easier to
  run for the next wave.

Week 4:

- Regenerate the Claude for OSS evidence table.
- Confirm counted contributors are unique humans and external to the project.
- Apply only if the official threshold is met; otherwise keep the Phase A text
  honest and continue community building.

## Outreach Copy: Korean

```text
한국어권 일본어 학습자를 위한 local-first OSS를 공개했습니다.
런타임 LLM 없이 사전 저작 dialogue bank + 로컬 STT/TTS로 회화 연습을 만드는 프로젝트입니다.

도움이 필요한 작은 이슈들이 있습니다:
- 한국어/일본어 표현 자연스러움 검수
- JLPT 초급 예문/설명 리뷰
- Expo 모바일 접근성 개선
- FastAPI 예제와 테스트 보강

처음 기여하기 쉬운 이슈:
https://github.com/duct-tape2/ai-language-partner/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22

기여자 안내:
https://duct-tape2.github.io/ai-language-partner/community/CONTRIBUTOR_LANDING.html

공유용 모집 페이지:
https://duct-tape2.github.io/ai-language-partner/community/CALL_FOR_CONTRIBUTORS.html
```

## Outreach Copy: Japanese

```text
韓国語話者向けの日本語学習アプリ OSS を公開しました。
実行時に LLM を呼ばず、事前に作成した dialogue bank とローカル STT/TTS で会話練習を行う local-first プロジェクトです。

小さな貢献を募集しています:
- 日本語の自然さ・初級者向け表現のレビュー
- 韓国語説明の改善
- Expo モバイル UI / アクセシビリティ改善
- FastAPI ドキュメントとテスト追加

Good first issues:
https://github.com/duct-tape2/ai-language-partner/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22

Contributor landing:
https://duct-tape2.github.io/ai-language-partner/community/CONTRIBUTOR_LANDING.html

Contributor call:
https://duct-tape2.github.io/ai-language-partner/community/CALL_FOR_CONTRIBUTORS.html
```

## Outreach Copy: English

```text
I opened ai-language-partner, a local-first Japanese speaking practice app for Korean learners.
It avoids runtime LLM calls in the core speaking loop: learner audio is transcribed locally, matched against pre-authored dialogue-bank lines, and answered with local TTS assets.

Useful small contributions:
- Korean/Japanese language review
- Beginner-safe JLPT sample content review
- Expo accessibility fixes
- FastAPI/OpenAPI examples and tests
- Local STT/TTS setup docs

Good first issues:
https://github.com/duct-tape2/ai-language-partner/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22

Contributor landing:
https://duct-tape2.github.io/ai-language-partner/community/CONTRIBUTOR_LANDING.html

Contributor call:
https://duct-tape2.github.io/ai-language-partner/community/CALL_FOR_CONTRIBUTORS.html
```

## Review Promise

When posting outreach, include a maintainer promise:

- First response within 24 hours
- Clear acceptance criteria
- No private context required
- Docs/content review is valued the same as code when it improves learner or
  contributor experience

## Suggested Communities

Start with communities where the project has natural fit:

- Korean Japanese-learning study groups
- Japanese language review communities
- Expo / React Native developers
- FastAPI developers
- Accessibility reviewers
- Local-first AI and privacy-preserving education builders

Avoid mass posting identical messages. Tailor each post to the community and
point to a small set of relevant issues.

Validate the queue before a recruiting session:

```bash
python scripts/verify_outreach_queue.py
python scripts/render_outreach_messages.py
```

Rendered copy/paste messages live in `docs/community/OUTREACH_MESSAGES.md`.
For shorter community posts, direct messages, and after-posting steps, use
`docs/community/SHARE_KIT.md`.
