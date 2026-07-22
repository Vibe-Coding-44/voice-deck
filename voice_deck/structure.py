"""発話テキスト → Markdown スライド構造化 (Claude API)"""
import os
import time
from pathlib import Path


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

ARTIFACTS_DIR = Path.home() / ".voice-deck" / "artifacts"
MAX_RETRIES = 2
RETRY_WAIT = 5.0


def save_transcript(text: str, stem: str) -> Path:
    """文字起こしテキストを保存。Claude API失敗時のリカバリ用。"""
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    path = ARTIFACTS_DIR / f"{stem}.txt"
    path.write_text(text, encoding="utf-8")
    return path


def structure(transcription: str, title: str | None = None, stem: str | None = None) -> str:
    """発話テキストを Markdown スライドに変換する。一時的な失敗はリトライする。"""
    import anthropic

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY が未設定です。export ANTHROPIC_API_KEY=sk-ant-... を実行してください。"
        )

    if stem:
        saved = save_transcript(transcription, stem)
        print(f"💾 文字起こし保存: {saved}", file=__import__("sys").stderr)

    client = anthropic.Anthropic(api_key=api_key)

    user_content = transcription
    if title:
        user_content = f"タイトル: {title}\n\n発話内容:\n{transcription}"

    last_err: Exception | None = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            message = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_content}],
            )
            return message.content[0].text
        except anthropic.AuthenticationError as e:
            raise RuntimeError(
                "Anthropic APIキーが無効です。ANTHROPIC_API_KEY を確認してください。"
            ) from e
        except anthropic.RateLimitError as e:
            last_err = e
            if attempt < MAX_RETRIES:
                print(f"⚠️  レート制限 — {RETRY_WAIT}秒後にリトライ ({attempt+1}/{MAX_RETRIES})", file=__import__("sys").stderr)
                time.sleep(RETRY_WAIT)
            continue
        except anthropic.APIError as e:
            last_err = e
            if "credit" in str(e).lower() or "billing" in str(e).lower():
                raise RuntimeError(
                    "Anthropic クレジット不足です。console.anthropic.com で残高を確認してください。"
                    + (f"\n文字起こしは {ARTIFACTS_DIR / (stem or 'transcription')}.txt に保存済みです。" if stem else "")
                ) from e
            if attempt < MAX_RETRIES:
                print(f"⚠️  API エラー — {RETRY_WAIT}秒後にリトライ ({attempt+1}/{MAX_RETRIES})", file=__import__("sys").stderr)
                time.sleep(RETRY_WAIT)

    raise RuntimeError(
        f"構造化失敗 (リトライ上限): {last_err}"
        + (f"\n文字起こしは {ARTIFACTS_DIR / (stem or 'transcription')}.txt に保存済みです。" if stem else "")
    ) from last_err
