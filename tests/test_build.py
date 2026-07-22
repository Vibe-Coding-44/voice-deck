"""build.py のユニットテスト — APIキー不要"""
import pytest
from voice_deck.build import md_to_slides, slide_to_html, build_html, md_inline


class TestMdToSlides:
    def test_single_slide(self):
        md = "# タイトル\n- 項目1\n- 項目2"
        slides = md_to_slides(md)
        assert len(slides) == 1
        assert "タイトル" in slides[0]

    def test_split_by_separator(self):
        md = "# スライド1\n内容\n\n---\n\n## スライド2\n内容"
        slides = md_to_slides(md)
        assert len(slides) == 2

    def test_empty_slides_skipped(self):
        md = "# A\n---\n\n---\n# B"
        slides = md_to_slides(md)
        assert len(slides) == 2  # 空スライドは除外

    def test_whitespace_separator(self):
        md = "# A\n  ---  \n# B"
        slides = md_to_slides(md)
        assert len(slides) == 2


class TestMdInline:
    def test_bold(self):
        assert "<strong>太字</strong>" in md_inline("**太字**")

    def test_italic(self):
        assert "<em>斜体</em>" in md_inline("*斜体*")

    def test_inline_code(self):
        assert "<code>code</code>" in md_inline("`code`")

    def test_html_escape(self):
        result = md_inline("<script>alert(1)</script>")
        assert "<script>" not in result
        assert "&lt;script&gt;" in result

    def test_plain_text(self):
        assert md_inline("plain") == "plain"


class TestSlideToHtml:
    def test_h1(self):
        html = slide_to_html("# タイトル")
        assert "<h1>" in html and "タイトル" in html

    def test_h2(self):
        html = slide_to_html("## セクション")
        assert "<h2>" in html and "セクション" in html

    def test_h3(self):
        html = slide_to_html("### サブ")
        assert "<h3>" in html and "サブ" in html

    def test_bullet_list(self):
        html = slide_to_html("- 項目A\n- 項目B")
        assert "<ul>" in html
        assert html.count("<li>") == 2
        assert "</ul>" in html

    def test_numbered_list(self):
        html = slide_to_html("1. 一番目\n2. 二番目")
        assert "<ul>" in html
        assert html.count("<li>") == 2

    def test_paragraph(self):
        html = slide_to_html("普通のテキスト")
        assert "<p>" in html and "普通のテキスト" in html

    def test_code_block(self):
        md = "```python\nprint('hello')\n```"
        html = slide_to_html(md)
        assert "<pre>" in html
        assert "language-python" in html
        assert "print" in html

    def test_code_block_html_escaped(self):
        md = "```\n<script>alert(1)</script>\n```"
        html = slide_to_html(md)
        assert "<script>" not in html

    def test_list_closes_before_heading(self):
        md = "- 項目\n## 見出し"
        html = slide_to_html(md)
        ul_pos = html.find("</ul>")
        h2_pos = html.find("<h2>")
        assert ul_pos < h2_pos

    def test_empty_slide(self):
        assert slide_to_html("") == ""


class TestBuildHtml:
    def test_title_injected(self):
        html = build_html("# テスト", title="My Deck")
        assert "My Deck" in html

    def test_title_xss_escaped(self):
        html = build_html("# テスト", title="<script>alert(1)</script>")
        assert "<script>alert(1)</script>" not in html

    def test_revealjs_present(self):
        html = build_html("# テスト")
        assert "reveal.js" in html.lower() or "Reveal" in html

    def test_section_wrapping(self):
        md = "# A\n---\n## B"
        html = build_html(md)
        assert html.count("<section>") == 2
        assert html.count("</section>") == 2

    def test_returns_string(self):
        assert isinstance(build_html("# テスト"), str)

    def test_nonempty(self):
        assert len(build_html("# テスト")) > 100
