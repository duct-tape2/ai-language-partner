---
layout: page
title: 日本語コントリビューター向け案内
---

# AI Language Partner に最初の PR を送る

`ai-language-partner` は、韓国語話者向けの local-first 日本語会話練習アプリです。
Expo モバイルアプリ、FastAPI バックエンド、レビュー済みの dialogue bank、
ローカル STT/TTS の流れを使います。

Daily Talk の中心的な会話フローでは、実行時の LLM 呼び出しに依存しません。
学習者の音声をローカルで認識し、レビュー済みの dialogue-bank 文と照合し、
ローカル TTS または事前準備された音声アセットで応答する設計です。

## 最初の貢献

ローカル音声エンジン、生成音声、private data、API key がなくても、有用な
最初の PR を送れます。

開始リンク:

- [ブラウザでデモを見る](../demo/)
- [日本語 5分 first PR](../community/FIVE_MINUTE_FIRST_PR_JA.html)
- [日本語 contributor call](../community/CALL_FOR_CONTRIBUTORS_JA.html)
- [Language review first PR kit](../community/LANGUAGE_REVIEW_FIRST_PR_KIT.html)
- [5分で始める最初の PR](../community/FIVE_MINUTE_FIRST_PR.html)
- [現在利用できる starter issue 一覧 - 予約済み・担当済みを除外](../community/STARTER_ISSUE_INDEX.html)
- [ブラウザ編集候補一覧 - 開始前に現在の一覧を確認](../community/NO_INSTALL_FIRST_PRS.html)
- [contributor landing](../community/CONTRIBUTOR_LANDING.html)
- [first PR walkthrough](../community/FIRST_PR_WALKTHROUGH.html)
- [installable demo release plan](../community/INSTALLABLE_DEMO_RELEASE_PLAN.html)
- [First PR help desk discussion](https://github.com/duct-tape2/ai-language-partner/discussions/53)
- [日本語 contributor interest form](https://github.com/duct-tape2/ai-language-partner/issues/new?template=contributor_interest_ja.yml)

## おすすめの貢献分野

| 分野 | よい最初の PR の例 |
|---|---|
| 日本語の自然さレビュー | 初級者に安全な表現、トーンの一貫性、文化的安全性の確認 |
| 韓国語/日本語ドキュメント | セットアップ説明、用語集、学習者向け説明の改善 |
| dialogue content | `story.json` や `variants.csv` の文・翻訳レビュー |
| モバイルアクセシビリティ | accessibility label、タップ領域、コントラスト、小さい画面の layout |
| FastAPI/OpenAPI docs | curl 例、provider-status 説明、ローカル STT/TTS 設定ノート |
| テスト/ツール | 小さな fixture test、repo check、CI で動く検証スクリプト |

## 役に立つ最初の貢献

学習者の日本語練習を分かりやすく、安全に、使いやすくする変更や、プロジェクトを
維持しやすくする改善を歓迎します。docs-only PR でも、実際の学習者または
コントリビューターの体験を良くするものは価値があります。

1 つの issue または課題に集中し、PR 本文でリンクしてください。実行した最小限の
check も書くと、maintainer がレビューしやすくなります。

## コミットしないもの

以下は Git に入れないでください:

- 生成された `.wav`, `.zip`, `.npy`, `.sqlite`, `.db`, `.bin`, screenshot files
- ローカル speech engine folder
- private notes, handoff files, 個人パス
- token, API key, secret, private dataset

公開 repo は source-only として維持します。
