# voice-deck

> 声で話すだけで、Markdown スライドが生まれる CLI ツール。

## コンセプト

**「声がスライドの一次ソース」**

Markdown を書く必要がない。話すだけでスライドの骨格が立ち上がる。
出力は純粋な Markdown なので Git 管理・差分確認・再編集が自然にできる。

```
voice-deck record
> 話す（アウトラインを口頭で整理）
→ Whisper で文字起こし
→ Claude API で Markdown スライド構造に整形
→ slidr / Reveal.js 互換の HTML 生成
```

## なぜ今か（トレンド根拠 2026-07-21）

| シグナル | 意味 |
|---|---|
| `slidr` HN 掲載 (2026-07-12) | 「Markdown でスライドを書く」需要が実証された |
| `voicebox` 44K stars 急上昇 | 「声でコンテンツを作る」民主化が来ている |
| `moonshine-ai` OSSトレンド入り | 低遅延 STT のエージェント組み込みハードルが下がった |
| r/powerpoint 「従来ソフトうんざり」 | 入力ハードル自体を下げたいユーザー層が確実に存在 |

## 差別化

- **Gamma / NotebookLM**: GUI 前提・クラウド保存・ベンダーロックイン
- **slidr**: Markdown を「書く」必要がある
- **voice-deck**: 「話す → Markdown → HTML」を 1 コマンドで完結。出力はローカルファイル

## MVP スコープ

```
voice-deck record         # マイク録音 → STT → Markdown 生成 → HTML 出力
voice-deck build <md>     # 既存 Markdown → HTML（slidr 互換）
voice-deck preview        # ローカルプレビューサーバー起動
```

### 技術スタック

- **STT**: openai-whisper（ローカル）または Whisper API
- **構造化**: Claude API（発話を見出し・箇条書き・コードブロックに整形）
- **スライド生成**: slidr または reveal.js テンプレート出力
- **CLI**: Python + Click
- **スタイル**: 2026 トレンドデフォルトテーマ（dark mode + bold typography）

## ディレクトリ構成（予定）

```
voice-deck/
├── voice_deck/
│   ├── __init__.py
│   ├── cli.py          # Click エントリーポイント
│   ├── record.py       # マイク録音 + STT
│   ├── structure.py    # Claude API で Markdown 構造化
│   └── build.py        # HTML スライド生成
├── templates/
│   └── default.html    # Reveal.js ベーステーマ
├── tests/
├── pyproject.toml
└── README.md
```

## ステージ

- 💡 アイデア（スキャフォールド完了）
- 🔨 実装（66 部隊委譲予定）
- ✅ 完了

## 起案メタ

- 起案: アイデアマン（クローンリーダー）/ 2026-07-21
- 起案チャンネル: #cortana-ideas
