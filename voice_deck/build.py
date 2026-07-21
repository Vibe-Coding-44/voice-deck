"""Markdown → Reveal.js 互換 HTML スライド生成"""
import re
import html
from pathlib import Path


TEMPLATE_PATH = Path(__file__).parent.parent / "templates" / "default.html"


def md_to_slides(markdown: str) -> list[str]:
    """Markdown を --- で分割してスライドリストに変換。"""
    raw_slides = re.split(r"^\s*---\s*$", markdown, flags=re.MULTILINE)
    slides = []
    for raw in raw_slides:
        raw = raw.strip()
        if raw:
            slides.append(raw)
    return slides


def md_inline(text: str) -> str:
    """インライン Markdown を HTML に変換 (bold/italic/code のみ)。"""
    text = html.escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
    return text


def slide_to_html(md: str) -> str:
    """1スライド分の Markdown を HTML に変換。"""
    lines = md.split("\n")
    html_parts: list[str] = []
    in_code = False
    code_lang = ""
    code_lines: list[str] = []
    in_list = False

    def flush_list():
        nonlocal in_list
        if in_list:
            html_parts.append("</ul>")
            in_list = False

    for line in lines:
        # コードブロック
        code_fence = re.match(r"^```(\w*)", line)
        if code_fence and not in_code:
            flush_list()
            in_code = True
            code_lang = code_fence.group(1) or "text"
            code_lines = []
            continue
        if in_code:
            if line.strip() == "```":
                lang_class = f' class="language-{code_lang}"' if code_lang else ""
                escaped = "\n".join(html.escape(l) for l in code_lines)
                html_parts.append(f'<pre><code{lang_class}>{escaped}</code></pre>')
                in_code = False
            else:
                code_lines.append(line)
            continue

        # 見出し
        h1 = re.match(r"^# (.+)", line)
        h2 = re.match(r"^## (.+)", line)
        h3 = re.match(r"^### (.+)", line)
        if h1:
            flush_list()
            html_parts.append(f"<h1>{md_inline(h1.group(1))}</h1>")
            continue
        if h2:
            flush_list()
            html_parts.append(f"<h2>{md_inline(h2.group(1))}</h2>")
            continue
        if h3:
            flush_list()
            html_parts.append(f"<h3>{md_inline(h3.group(1))}</h3>")
            continue

        # 箇条書き
        li = re.match(r"^[-*]\s+(.+)", line)
        if li:
            if not in_list:
                html_parts.append("<ul>")
                in_list = True
            html_parts.append(f"<li>{md_inline(li.group(1))}</li>")
            continue

        # 番号付きリスト
        oli = re.match(r"^\d+\.\s+(.+)", line)
        if oli:
            if not in_list:
                html_parts.append("<ul>")
                in_list = True
            html_parts.append(f"<li>{md_inline(oli.group(1))}</li>")
            continue

        # 空行
        if not line.strip():
            flush_list()
            continue

        # 段落
        flush_list()
        html_parts.append(f"<p>{md_inline(line)}</p>")

    flush_list()
    return "\n".join(html_parts)


def build_html(markdown: str, title: str = "Presentation") -> str:
    """Markdown 全体を Reveal.js HTML に変換して返す。"""
    slides = md_to_slides(markdown)
    sections = "\n".join(
        f'<section>\n{slide_to_html(s)}\n</section>'
        for s in slides
    )
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    return template.replace("{{TITLE}}", html.escape(title)).replace("{{SLIDES}}", sections)
