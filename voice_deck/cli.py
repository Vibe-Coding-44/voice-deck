"""voice-deck CLI エントリーポイント"""
import os
import sys
from pathlib import Path
import datetime

import click


def _stem(title: str | None) -> str:
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    if title:
        safe = title.replace(" ", "_").replace("/", "-")[:40]
        return f"{safe}_{ts}"
    return ts


@click.group()
def cli():
    """声で話してMarkdownスライドを作るCLIツール。"""


@cli.command()
@click.option("--title", "-t", default=None, help="スライドタイトル")
@click.option("--lang", "-l", default="ja", show_default=True, help="発話言語 (ja/en/...)")
@click.option("--duration", "-d", default=None, type=int, help="録音秒数 (省略=Enterで停止)")
@click.option("--out", "-o", default=None, help="出力ファイル名 (省略=タイトルから自動生成)")
@click.option("--md-only", is_flag=True, help="Markdownのみ出力 (HTMLビルドしない)")
def record(title, lang, duration, out, md_only):
    """マイクで話してスライドを生成する。"""
    from .record import record_and_transcribe
    from .structure import structure
    from .build import build_html

    stem = _stem(title)

    # 1. 録音 + STT (音声は自動保存)
    try:
        text, wav_path = record_and_transcribe(duration=duration, language=lang, stem=stem)
    except RuntimeError as e:
        click.echo(f"❌ 録音/文字起こしエラー: {e}", err=True)
        sys.exit(1)

    if not text.strip():
        click.echo("⚠️  音声が検出されませんでした。", err=True)
        sys.exit(1)

    click.echo(f"\n--- 文字起こし ---\n{text}\n---\n", err=True)

    # 2. Markdown 構造化 (文字起こしは自動保存済み)
    click.echo("🤖 Markdown 構造化中...", err=True)
    try:
        md = structure(text, title=title, stem=stem)
    except RuntimeError as e:
        click.echo(f"❌ 構造化エラー: {e}", err=True)
        click.echo(f"💡 voice-deck from-transcript {stem} で再試行できます。", err=True)
        sys.exit(1)

    # 3. 出力
    slide_title = title or "presentation"
    safe_name = slide_title.replace(" ", "_").replace("/", "-")

    md_path = Path(f"{safe_name}.md")
    md_path.write_text(md, encoding="utf-8")
    click.echo(f"✅ Markdown: {md_path}", err=True)

    if not md_only:
        html_content = build_html(md, title=slide_title)
        html_path = Path(out) if out else Path(f"{safe_name}.html")
        html_path.write_text(html_content, encoding="utf-8")
        click.echo(f"✅ HTML:     {html_path}", err=True)
        click.echo(f"\n👉 open {html_path}", err=True)


@cli.command()
@click.argument("md_file", type=click.Path(exists=True))
@click.option("--out", "-o", default=None, help="出力 HTML ファイル名")
@click.option("--title", "-t", default=None, help="スライドタイトル")
def build(md_file, out, title):
    """既存の Markdown ファイルから HTML スライドを生成する。"""
    from .build import build_html

    md_path = Path(md_file)
    md = md_path.read_text(encoding="utf-8")
    slide_title = title or md_path.stem

    html_content = build_html(md, title=slide_title)
    html_path = Path(out) if out else md_path.with_suffix(".html")
    html_path.write_text(html_content, encoding="utf-8")
    click.echo(f"✅ {html_path}")


@cli.command("from-wav")
@click.argument("wav_file", type=click.Path(exists=True))
@click.option("--title", "-t", default=None, help="スライドタイトル")
@click.option("--lang", "-l", default="ja", show_default=True)
@click.option("--out", "-o", default=None)
@click.option("--md-only", is_flag=True)
def from_wav(wav_file, title, lang, out, md_only):
    """保存済みWAVから再開 — STT失敗時のリカバリ用。"""
    from .record import transcribe_file
    from .structure import structure
    from .build import build_html

    wav_path = Path(wav_file)
    stem = wav_path.stem

    click.echo("⏳ 文字起こし中...", err=True)
    try:
        text = transcribe_file(wav_path, language=lang)
    except RuntimeError as e:
        click.echo(f"❌ 文字起こしエラー: {e}", err=True)
        sys.exit(1)

    click.echo(f"📝 文字起こし完了 ({len(text)} 文字)", err=True)

    try:
        md = structure(text, title=title, stem=stem)
    except RuntimeError as e:
        click.echo(f"❌ 構造化エラー: {e}", err=True)
        sys.exit(1)

    slide_title = title or stem
    safe_name = slide_title.replace(" ", "_").replace("/", "-")
    md_path = Path(f"{safe_name}.md")
    md_path.write_text(md, encoding="utf-8")
    click.echo(f"✅ Markdown: {md_path}", err=True)

    if not md_only:
        html_content = build_html(md, title=slide_title)
        html_path = Path(out) if out else Path(f"{safe_name}.html")
        html_path.write_text(html_content, encoding="utf-8")
        click.echo(f"✅ HTML:     {html_path}", err=True)
        click.echo(f"\n👉 open {html_path}", err=True)


@cli.command("from-transcript")
@click.argument("stem_or_file")
@click.option("--title", "-t", default=None)
@click.option("--out", "-o", default=None)
@click.option("--md-only", is_flag=True)
def from_transcript(stem_or_file, title, out, md_only):
    """保存済み文字起こしから再開 — Claude API失敗時のリカバリ用。"""
    from .structure import structure, ARTIFACTS_DIR
    from .build import build_html

    p = Path(stem_or_file)
    if not p.exists():
        p = ARTIFACTS_DIR / f"{stem_or_file}.txt"
    if not p.exists():
        click.echo(f"❌ ファイルが見つかりません: {p}", err=True)
        sys.exit(1)

    text = p.read_text(encoding="utf-8")
    stem = p.stem

    click.echo("🤖 Markdown 構造化中...", err=True)
    try:
        md = structure(text, title=title, stem=stem)
    except RuntimeError as e:
        click.echo(f"❌ 構造化エラー: {e}", err=True)
        sys.exit(1)

    slide_title = title or stem
    safe_name = slide_title.replace(" ", "_").replace("/", "-")
    md_path = Path(f"{safe_name}.md")
    md_path.write_text(md, encoding="utf-8")
    click.echo(f"✅ Markdown: {md_path}", err=True)

    if not md_only:
        html_content = build_html(md, title=slide_title)
        html_path = Path(out) if out else Path(f"{safe_name}.html")
        html_path.write_text(html_content, encoding="utf-8")
        click.echo(f"✅ HTML:     {html_path}", err=True)
        click.echo(f"\n👉 open {html_path}", err=True)


@cli.command()
@click.argument("html_file", type=click.Path(exists=True))
@click.option("--port", "-p", default=8765, show_default=True)
def preview(html_file, port):
    """HTML スライドをローカルサーバーでプレビューする。"""
    import http.server
    import webbrowser
    from functools import partial

    html_path = Path(html_file).resolve()
    os.chdir(html_path.parent)

    Handler = partial(http.server.SimpleHTTPRequestHandler, directory=str(html_path.parent))
    with http.server.HTTPServer(("", port), Handler) as httpd:
        url = f"http://localhost:{port}/{html_path.name}"
        click.echo(f"🌐 {url}")
        webbrowser.open(url)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            click.echo("\n停止しました。")


@cli.command("artifacts")
def artifacts():
    """保存済みの音声・文字起こしファイル一覧を表示する。"""
    from .record import ARTIFACTS_DIR

    if not ARTIFACTS_DIR.exists():
        click.echo("保存済みファイルはありません。")
        return

    files = sorted(ARTIFACTS_DIR.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        click.echo("保存済みファイルはありません。")
        return

    click.echo(f"📁 {ARTIFACTS_DIR}\n")
    for f in files:
        size = f.stat().st_size
        click.echo(f"  {f.name}  ({size // 1024}KB)")
