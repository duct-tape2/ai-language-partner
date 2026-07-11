---
layout: page
title: 5分 first PR guide
---

# 5分 first PR guide

この guide は、ローカル setup なしで GitHub web editor だけを使い、
小さな最初の PR を送るためのルートです。Expo、FastAPI、local STT/TTS engine、
生成音声、API key は不要です。

まず Web demo でアプリの方向性を確認できます:

`https://duct-tape2.github.io/ai-language-partner/demo/`

重複作業を避けたい場合は、issue に `/claim` とコメントしてください。自動コメントが
first PR checklist を案内し、maintainer triage 用の `claimed` label を付けます。

Claude for OSS 基準では、実在する外部コントリビューターの有用な merged PR だけを
count します。数字を増やすための小さな typo 分割、bot、重複アカウント、maintainer PR は
count しません。

## いちばん早い選択肢

[現在利用できる starter issue 一覧](STARTER_ISSUE_INDEX.md) から選んでください。
この一覧は予約済み・担当済みの issue を除くため、重複作業を避けられます。
日本語の自然さ、韓国語/日本語ドキュメント、dialogue content、アクセシビリティ、
API 例、テストの中から 1 つを選べます。

ブラウザで編集できる候補の全体は [No-install first PR board](NO_INSTALL_FIRST_PRS.md) に
ありますが、開始前に必ず現在利用できる一覧を確認してください。
日本語・韓国語・文化メモのレビュー範囲で迷う場合は
[Language review first PR kit](LANGUAGE_REVIEW_FIRST_PR_KIT.md) を見てください。

## PR title examples

- `content: review yui beginner Japanese dialogue`
- `docs: improve Japanese mobile mock setup`
- `docs: explain no-runtime-LLM design in Japanese`
- `content: review honorific consistency`

## PR body template

```text
Closes #ISSUE_NUMBER

What changed:
- 

Review/check:
- Docs/content/language review only; no local setup required.

Notes:
- I did not add generated audio, archives, SQLite files, screenshots, secrets,
  or local engine files.
```

## PR 前 checklist

- 1 つの PR は 1 つの issue または 1 つのテーマに集中します。
- PR body に `Closes #ISSUE_NUMBER` を入れます。
- `.wav`, `.zip`, `.npy`, `.sqlite`, `.db`, `.bin`, screenshot, local engine,
  private note, token, API key を commit しません。
- `story.json` または `variants.csv` を編集するときは、既存の構造と ID を保ちます。
  CI が schema、ID、reference、safety を自動検証するため、ローカル setup は不要です。
- 何を選ぶか迷う場合は
  [First PR help desk](https://github.com/duct-tape2/ai-language-partner/discussions/53)
  または
  [日本語 contributor interest form](https://github.com/duct-tape2/ai-language-partner/issues/new?template=contributor_interest_ja.yml)
  を使ってください。
