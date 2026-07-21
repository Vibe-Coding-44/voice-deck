"""voice-deck CLI エントリーポイント"""
import sys
from pathlib import Path

import click


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

    # 1. 録音 + STT
    text = record_and_transcribe(duration=duration, language=lang)
    if not text.strip():
        click.echo("⚠️  音声が検出されませんでした。", err=True)
        sys.exit(1)

    click.echo(f"\n--- 文字起こし ---\n{text}\n---\n", err=True)

    # 2. Markdown 構造化
    click.echo("🤖 Markdown 構造化中...", err=True)
    md = structure(text, title=title)

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


# preview コマンドで os が必要
import os
