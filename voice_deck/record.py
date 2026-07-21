"""マイク録音 → OpenAI Whisper API で文字起こし"""
import io
import os
import sys
import tempfile

import numpy as np
import sounddevice as sd
from scipy.io import wavfile


SAMPLE_RATE = 16000


def record_audio(duration: int | None = None, silence_timeout: float = 2.0) -> np.ndarray:
    """マイクから録音。duration=None なら Enter キーで停止。"""
    print("🎙  録音中... (Enter で停止)", file=sys.stderr)
    chunks: list[np.ndarray] = []

    if duration:
        audio = sd.rec(int(duration * SAMPLE_RATE), samplerate=SAMPLE_RATE,
                       channels=1, dtype="int16")
        sd.wait()
        return audio.flatten()

    # Enter キー停止モード
    import threading
    stop_event = threading.Event()

    def _record():
        with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="int16") as stream:
            while not stop_event.is_set():
                data, _ = stream.read(SAMPLE_RATE // 10)  # 100ms ずつ
                chunks.append(data.flatten())

    t = threading.Thread(target=_record, daemon=True)
    t.start()
    input()  # Enter まで待機
    stop_event.set()
    t.join(timeout=1.0)

    return np.concatenate(chunks) if chunks else np.zeros(0, dtype="int16")


def transcribe(audio: np.ndarray, language: str = "ja") -> str:
    """OpenAI Whisper API で文字起こし。"""
    from openai import OpenAI

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY が設定されていません")

    client = OpenAI(api_key=api_key)

    # WAV バッファに書き出し
    buf = io.BytesIO()
    wavfile.write(buf, SAMPLE_RATE, audio)
    buf.seek(0)
    buf.name = "audio.wav"

    result = client.audio.transcriptions.create(
        model="whisper-1",
        file=buf,
        language=language,
    )
    return result.text


def record_and_transcribe(duration: int | None = None, language: str = "ja") -> str:
    """録音して文字起こしまで一括実行。"""
    audio = record_audio(duration=duration)
    if audio.size == 0:
        return ""
    print("⏳ 文字起こし中...", file=sys.stderr)
    text = transcribe(audio, language=language)
    print(f"📝 文字起こし完了 ({len(text)} 文字)", file=sys.stderr)
    return text
