"""マイク録音 → OpenAI Whisper API で文字起こし"""
import io
import os
import sys
import time
from pathlib import Path

import numpy as np
import sounddevice as sd
from scipy.io import wavfile


SAMPLE_RATE = 16000
ARTIFACTS_DIR = Path.home() / ".voice-deck" / "artifacts"
MAX_RETRIES = 2
RETRY_WAIT = 5.0


def _artifacts_dir() -> Path:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    return ARTIFACTS_DIR


def save_audio(audio: np.ndarray, stem: str) -> Path:
    """WAVファイルとして保存。APIが失敗しても音声を保全する。"""
    path = _artifacts_dir() / f"{stem}.wav"
    wavfile.write(str(path), SAMPLE_RATE, audio)
    return path


def record_audio(duration: int | None = None) -> np.ndarray:
    """マイクから録音。duration=None なら Enter キーで停止。"""
    print("🎙  録音中... (Enter で停止)", file=sys.stderr)
    chunks: list[np.ndarray] = []

    if duration:
        audio = sd.rec(int(duration * SAMPLE_RATE), samplerate=SAMPLE_RATE,
                       channels=1, dtype="int16")
        sd.wait()
        return audio.flatten()

    import threading
    stop_event = threading.Event()

    def _record():
        with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="int16") as stream:
            while not stop_event.is_set():
                data, _ = stream.read(SAMPLE_RATE // 10)
                chunks.append(data.flatten())

    t = threading.Thread(target=_record, daemon=True)
    t.start()
    input()
    stop_event.set()
    t.join(timeout=1.0)

    return np.concatenate(chunks) if chunks else np.zeros(0, dtype="int16")


def transcribe(audio: np.ndarray, language: str = "ja") -> str:
    """OpenAI Whisper API で文字起こし。一時的な失敗はリトライする。"""
    from openai import OpenAI, APIError, AuthenticationError, RateLimitError

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY が未設定です。export OPENAI_API_KEY=sk-... を実行してください。"
        )

    client = OpenAI(api_key=api_key)

    buf = io.BytesIO()
    wavfile.write(buf, SAMPLE_RATE, audio)
    buf.seek(0)
    buf.name = "audio.wav"

    last_err: Exception | None = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            result = client.audio.transcriptions.create(
                model="whisper-1",
                file=buf,
                language=language,
            )
            return result.text
        except AuthenticationError as e:
            raise RuntimeError(
                "OpenAI APIキーが無効です。OPENAI_API_KEY を確認してください。"
            ) from e
        except RateLimitError as e:
            last_err = e
            if attempt < MAX_RETRIES:
                print(f"⚠️  レート制限 — {RETRY_WAIT}秒後にリトライ ({attempt+1}/{MAX_RETRIES})", file=sys.stderr)
                time.sleep(RETRY_WAIT)
                buf.seek(0)
            continue
        except APIError as e:
            last_err = e
            if "insufficient_quota" in str(e) or "billing" in str(e).lower():
                raise RuntimeError(
                    "OpenAI クレジット不足です。platform.openai.com で残高を確認してください。"
                ) from e
            if attempt < MAX_RETRIES:
                print(f"⚠️  API エラー — {RETRY_WAIT}秒後にリトライ ({attempt+1}/{MAX_RETRIES})", file=sys.stderr)
                time.sleep(RETRY_WAIT)
                buf.seek(0)

    raise RuntimeError(f"文字起こし失敗 (リトライ上限): {last_err}") from last_err


def transcribe_file(wav_path: Path, language: str = "ja") -> str:
    """保存済み WAV ファイルから文字起こし（リカバリ用）。"""
    audio, _ = wavfile.read(str(wav_path))
    if audio.dtype != np.int16:
        audio = (audio * 32767).astype(np.int16)
    return transcribe(audio, language=language)


def record_and_transcribe(
    duration: int | None = None,
    language: str = "ja",
    stem: str | None = None,
) -> tuple[str, Path]:
    """録音→保存→文字起こしまで一括実行。(text, wav_path) を返す。"""
    import datetime
    if stem is None:
        stem = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    audio = record_audio(duration=duration)
    if audio.size == 0:
        return "", Path("/dev/null")

    wav_path = save_audio(audio, stem)
    print(f"💾 音声保存: {wav_path}", file=sys.stderr)

    print("⏳ 文字起こし中...", file=sys.stderr)
    text = transcribe(audio, language=language)
    print(f"📝 文字起こし完了 ({len(text)} 文字)", file=sys.stderr)
    return text, wav_path
