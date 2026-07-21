# voice-deck — プロジェクト・ロール定義

声でMarkdownスライドを生成するCLIツール。
上位の `/Users/620306/Vibe-Coding/CLAUDE.md`（PgM 自動起動）に従属する。

## コンセプト（絶対に外さない一本の糸）

**「声がスライドの一次ソース」** —— Markdown を書く手間を省くのではなく、
「話す」という行為を設計の出発点に置く。
出力が Markdown であることで、Git・diff・再編集の自由度を保つ。

GUI に逃げない。CLI 完結・ローカルファイル出力を維持すること。

## ロール定義

| ロール | 責務 | このプロジェクトでの具体 |
|---|---|---|
| **CLI エンジニア** | Python Click CLI の実装 | record / build / preview コマンド。依存は最小限 |
| **音声処理** | STT パイプライン | Whisper ローカル優先・API fallback。低遅延を重視 |
| **プロンプトエンジニア** | Claude API 構造化 | 発話 → Markdown 変換の精度。見出し階層・コードブロック検出 |
| **テンプレートデザイナー** | HTML スライドテーマ | 2026 トレンド準拠（dark mode + bold typography + Bento Grid） |

## 技術方針

- **CLI 完結・ローカル保存**（チーム標準に準拠）
- STT: openai-whisper をローカル優先（GPU 不要の base モデル）
- 構造化: Claude API（claude-sonnet-4-6 以上）
- スライド生成: reveal.js 互換 HTML テンプレート出力（slidr は参考実装）
- Python 3.12+、Click、pyproject.toml でパッケージ管理
- 課金・外部発信が絡む変更は PgM 経由でボスに確認

## スコープ境界

- V0（現在）: スキャフォールド + README。技術選定まで。
- V1（66 部隊委譲）: record / build / preview の最小動作実装
- V2: テーマカスタマイズ・複数 STT バックエンド対応
- 対象外: クラウド保存・有料スライドホスティング・GUI（発生時は PgM 経由承認）

## 起案メタ

- 起案: アイデアマン（クローンリーダー）初回起案 / 2026-07-21
- 立ち位置: Cortana 戦略層とは独立軸。#cortana-info（資料脳 slidr）× GitHub Trending（voicebox）交差点から起案。
- アウター連携: 現時点で不要。外部 STT API 契約・大規模デプロイが必要になった場合はアウターリーダーに実体確認（推測で埋めない）。
