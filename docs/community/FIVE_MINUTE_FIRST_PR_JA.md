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

| できること | issue | すぐ編集 |
|---|---|---|
| 日本語 mobile setup 説明 | [#2](https://github.com/duct-tape2/ai-language-partner/issues/2) | [日本語 guide を編集](https://github.com/duct-tape2/ai-language-partner/edit/main/docs/ja/index.md) |
| 日本語の自然さレビュー | [#8](https://github.com/duct-tape2/ai-language-partner/issues/8) | [story source を編集](https://github.com/duct-tape2/ai-language-partner/edit/main/packs/yui/v1/story.json) |
| no-runtime-LLM 説明 | [#35](https://github.com/duct-tape2/ai-language-partner/issues/35) | [日本語 guide を編集](https://github.com/duct-tape2/ai-language-partner/edit/main/docs/ja/index.md) |
| レストランの好み表現 | [#36](https://github.com/duct-tape2/ai-language-partner/issues/36) | [variants CSV を編集](https://github.com/duct-tape2/ai-language-partner/edit/main/packs/yui/v1/variants.csv) |
| 敬語・トーンの確認 | [#37](https://github.com/duct-tape2/ai-language-partner/issues/37) | [story source を編集](https://github.com/duct-tape2/ai-language-partner/edit/main/packs/yui/v1/story.json) |
| 文化安全性レビュー | [#47](https://github.com/duct-tape2/ai-language-partner/issues/47) | [culture notes を編集](https://github.com/duct-tape2/ai-language-partner/edit/main/apps/mobile/src/culture/cultureNotes.ts) |

さらに多くの候補は [No-install first PR board](NO_INSTALL_FIRST_PRS.md) にあります。

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
- JSON/CSV/YAML を編集するときは、既存の構造と ID を保ちます。
- 何を選ぶか迷う場合は
  [First PR help desk](https://github.com/duct-tape2/ai-language-partner/discussions/53)
  または
  [日本語 contributor interest form](https://github.com/duct-tape2/ai-language-partner/issues/new?template=contributor_interest_ja.yml)
  を使ってください。
