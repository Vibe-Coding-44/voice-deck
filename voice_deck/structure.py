"""発話テキスト → Markdown スライド構造化 (Claude API)"""
import os


SYSTEM_PROMPT = """\
あなたは発話テキストをプレゼンテーション用 Markdown に変換するアシスタントです。

ルール:
- スライド区切りは `---` (水平線)
- 各スライドの1行目が見出し (## タイトル)
- 箇条書きは最大3〜5項目/スライド
- コードは ```言語 ブロック で囲む
- 1スライド1メッセージ原則 (詰め込まない)
- 最初のスライドはタイトルスライド (# タイトル + サブタイトル)
- 最後のスライドは「まとめ」または「Next Steps」
- 出力は Markdown のみ。説明文・前置きは不要。
"""


def structure(transcription: str, title: str | None = None) -> str:
    """発話テキストを Markdown スライドに変換する。"""
    import anthropic

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY が設定されていません")

    client = anthropic.Anthropic(api_key=api_key)

    user_content = transcription
    if title:
        user_content = f"タイトル: {title}\n\n発話内容:\n{transcription}"

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
    )
    return message.content[0].text
