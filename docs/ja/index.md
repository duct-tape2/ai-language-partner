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

- [5分で始める最初の PR](../community/FIVE_MINUTE_FIRST_PR.md)
- [starter issue index](../community/STARTER_ISSUE_INDEX.md)
- [no-install first PR board](../community/NO_INSTALL_FIRST_PRS.md)
- [contributor landing](../community/CONTRIBUTOR_LANDING.md)
- [first PR walkthrough](../community/FIRST_PR_WALKTHROUGH.md)
- [First PR help desk discussion](https://github.com/duct-tape2/ai-language-partner/discussions/53)
- [contributor interest form](https://github.com/duct-tape2/ai-language-partner/issues/new?template=contributor_interest.yml)

## おすすめの貢献分野

| 分野 | よい最初の PR の例 |
|---|---|
| 日本語の自然さレビュー | 初級者に安全な表現、トーンの一貫性、文化的安全性の確認 |
| 韓国語/日本語ドキュメント | セットアップ説明、用語集、学習者向け説明の改善 |
| dialogue content | `story.json` や `variants.csv` の文・翻訳レビュー |
| モバイルアクセシビリティ | accessibility label、タップ領域、コントラスト、小さい画面の layout |
| FastAPI/OpenAPI docs | curl 例、provider-status 説明、ローカル STT/TTS 設定ノート |
| テスト/ツール | 小さな fixture test、repo check、CI で動く検証スクリプト |

## Claude for OSS 基準

この repo は Claude for OSS の community-builder route を目標にしています:
過去 12 か月で 20 名以上の unique external contributors による useful merged
PR がある repo になることです。

重要な原則:

- 実在する外部コントリビューターの有用な merged PR だけを count します。
- maintainer の PR、bot、重複アカウント、数字だけを増やす無意味な PR は
  count しません。
- docs-only PR でも、実際のユーザー体験や contributor onboarding を改善する
  ものは歓迎します。

関連ドキュメント:

- [Claude for OSS application evidence](../CLAUDE_FOR_OSS_APPLICATION.md)
- [PR review and counting policy](../community/PR_REVIEW_AND_COUNTING_POLICY.md)
- [20 contributor sprint](../community/CONTRIBUTOR_SPRINT.md)

## コミットしないもの

以下は Git に入れないでください:

- 生成された `.wav`, `.zip`, `.npy`, `.sqlite`, `.db`, `.bin`, screenshot files
- ローカル speech engine folder
- private notes, handoff files, 個人パス
- token, API key, secret, private dataset

公開 repo は source-only として維持します。
