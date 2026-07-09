---
layout: page
title: 日本語コントリビューター募集
---

# 日本語コントリビューター募集

`ai-language-partner` は、韓国語話者向けの local-first 日本語会話練習アプリです。
今は、日本語の自然さレビュー、初級者向け表現の確認、文化メモの安全性レビュー、
会話コンテンツの検収、ドキュメント改善に協力してくれる方を探しています。

共有リンク:

`https://duct-tape2.github.io/ai-language-partner/community/CALL_FOR_CONTRIBUTORS_JA.html`

## まず見るもの

- Web demo: `https://duct-tape2.github.io/ai-language-partner/demo/`
- GitHub repo: `https://github.com/duct-tape2/ai-language-partner`
- First PR help desk: `https://github.com/duct-tape2/ai-language-partner/discussions/53`
- Contributor discussion: `https://github.com/duct-tape2/ai-language-partner/discussions/55`
- 日本語 contributor guide: `https://duct-tape2.github.io/ai-language-partner/ja/`

Web demo は mock provider で動きます。ローカル音声エンジン、生成音声、
private data、API key がなくても、アプリの方向性を見て最初の PR を作れます。

## よい最初の PR

| できること | starter issue | よい PR の形 |
|---|---|---|
| 日本語 setup docs | `https://github.com/duct-tape2/ai-language-partner/issues/2` | mobile mock-mode 説明を日本語でわかりやすくする |
| 日本語の自然さレビュー | `https://github.com/duct-tape2/ai-language-partner/issues/8` | 初級者に安全な会話表現をレビューする |
| no-runtime-LLM 説明 | `https://github.com/duct-tape2/ai-language-partner/issues/35` | local-first 設計を日本語で中立的に説明する |
| 敬語・トーンの確認 | `https://github.com/duct-tape2/ai-language-partner/issues/37` | onboarding 例文の敬語とトーンをそろえる |
| 文化安全性レビュー | `https://github.com/duct-tape2/ai-language-partner/issues/47` | stereotype になりやすい例を安全に直す |
| dialogue content | `https://github.com/duct-tape2/ai-language-partner/issues/36` | レストラン/好みの会話例を自然にする |

選びやすいリンク:

- 日本語 5分 first PR: `https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIVE_MINUTE_FIRST_PR_JA.md`
- First issue matcher: `https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/FIRST_ISSUE_MATCHER.md`
- No-install first PR board: `https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/NO_INSTALL_FIRST_PRS.md`
- Starter issue index: `https://github.com/duct-tape2/ai-language-partner/blob/main/docs/community/STARTER_ISSUE_INDEX.md`
- 日本語 contributor interest form: `https://github.com/duct-tape2/ai-language-partner/issues/new?template=contributor_interest_ja.yml`

## 進め方

1. issue を 1 つ選びます。
2. 重複作業を避けたい場合は、issue に `/claim` とコメントします。
3. 1 つのファイルまたは 1 つのテーマに集中して修正します。
4. PR 本文に `Closes #issue番号` を入れます。
5. 実行した check を書くか、docs/content/language review only と明記します。

## コミットしないもの

- 生成された `.wav`, `.zip`, `.npy`, `.sqlite`, `.db`, `.bin`, screenshot files
- local speech engine folder
- private notes, handoff files, 個人パス
- token, API key, secret, private dataset

Daily Talk の中心的な会話フローは、実行時の LLM/API 呼び出しに依存しません。
学習者の音声をローカルで認識し、レビュー済みの dialogue-bank 文と照合し、
local TTS または事前準備済み音声アセットで応答します。貢献もこの
local-first 設計を保つ方向でお願いします。

## Claude for OSS メモ

この repo は Claude for OSS community-builder route を目標にしています。
基準は、過去 12 か月で 20 名以上の unique external contributors による
useful merged PR がある repo になることです。

実在する外部コントリビューターの有用な merged PR だけを count します。
maintainer PR、bot、重複アカウント、数字を増やすだけの無意味な PR は
count しません。
