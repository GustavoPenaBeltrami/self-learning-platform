#!/usr/bin/env python3
import pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "server"))
from text import html_to_md, md_to_html, slug, split_by_h1


def stable(html):
    md = html_to_md(html)
    assert html_to_md(md_to_html(md)) == md, (html, md, md_to_html(md))
    return md


def test_round_trip():
    h = ('<h1>Fundamentals</h1><p>Text with <b>bold</b> and <i>italic</i> and <s>struck</s>.</p>'
         '<h2>Coupling</h2><ul><li>One</li><li>Two</li></ul>'
         '<p>See <a class="ref" href="#styles">Styles</a> too.</p>'
         '<p>A <mark class="mk mk-highlight" style="--c: #D9C46A" title="careful">highlight</mark> here.</p>')
    md = stable(h)
    assert "# Fundamentals" in md and "## Coupling" in md and "- One\n- Two" in md and "[[Styles]]" in md, md
    assert "**bold**" in md and "*italic*" in md and "~~struck~~" in md, md
    assert '<mark class="mk mk-highlight" style="--c: #D9C46A" title="careful">highlight</mark>' in md, md
    back = md_to_html(md)
    assert "<h1>Fundamentals</h1>" in back and "<b>bold</b>" in back and "<i>italic</i>" in back, back
    assert '<a class="ref" href="#styles">Styles</a>' in back and "<li>One</li>" in back, back
    for given in ('<p>one</p><p><br></p><p>two</p>', '<h2>T</h2><div><br></div><p>x</p>',
                  '<p>a</p><div></div><p>b</p>', '<p>one<br>two</p>'):
        assert "<br>" in stable(given), given
    md_num = "1. one\n2. two\n\n- a\n- b\n"
    assert "<ol>" in md_to_html(md_num) and html_to_md(md_to_html(md_num)) == md_num


def test_viz_fences():
    md = ("# Ch\n\ntext\n\n```mermaid\ngraph TD\n  A[Package] --> B{Order}\n"
          "```\n\nmore text\n\n```math\np_{99} = \\frac{x}{y}\n```\n")
    h = md_to_html(md)
    assert '<figure class="viz" data-kind="mermaid"' in h and "A[Package] --&gt; B{Order}" in h, h
    assert html_to_md(h) == md
    painted = h.replace('<div class="view"></div>', '<div class="view"><svg><g>junk</g></svg></div>', 1)
    assert html_to_md(painted) == md
    assert "<figcaption>caption</figcaption>" in html_to_md('<figure><img src="x.png"><figcaption>caption</figcaption></figure>')
    md_list = "- one\n- two\n\n```mermaid\ngraph LR\n  A --> B\n```\n"
    assert md_to_html(md_list).count("</ul>") == 1 and html_to_md(md_to_html(md_list)) == md_list


def test_unclosed_fence_stays_text():
    h = md_to_html("```mermaid\ngraph\n\nlater paragraph\n")
    assert "<figure" not in h and "<p>later paragraph</p>" in h, h


def test_escaping():
    md = stable('<p>use a &lt;div&gt; here &amp; there</p>')
    assert md_to_html(md) == '<p>use a &lt;div&gt; here &amp; there</p>'
    assert "<img" not in md_to_html(stable('<p>&lt;img src=x onerror=alert(1)&gt;</p>'))
    md = stable('<p><mark class="mk" data-comment="he said &quot;hi&quot; &amp; left">x</mark></p>')
    assert 'data-comment="he said &quot;hi&quot; &amp; left"' in md_to_html(md)
    for text in ("# not heading", "- not list", "1. not a list", "| not a table", "```mermaid"):
        h = md_to_html(stable(f"<p>{text}</p>"))
        assert h.startswith("<p>") and h.count("<p>") == 1, (text, h)
    assert "<a" not in md_to_html(stable("<p>see [[not a ref]] literally</p>"))
    assert "<i>" not in md_to_html(stable("<p>price 2 * 3 * 4 and *stars*</p>"))
    assert "<i>" not in md_to_html("price 2 * 3 * 4"), "a lone star with spaces is not italics"


def test_links_code_pre_sub_sup():
    for h in ('<p><a href="https://x.com">link</a> text</p>', '<p>x <code>foo()</code> y</p>',
              '<p>H<sub>2</sub>O and x<sup>2</sup></p>'):
        md = stable(h)
        assert all(t in md for t in ("https://x.com",) if "href" in h), md
        assert ("<code>" in md) == ("<code>" in h) and ("<sub>" in md) == ("<sub>" in h), md
    md = stable('<p>a</p><pre>code\n  block *x*</pre>')
    assert "<pre>" in md and "\n  block" in md_to_html(md).replace("&#10;", "\n"), md


def test_tables():
    h = ('<table><thead><tr><th>Code</th><th>Meaning</th></tr></thead>'
         '<tbody><tr><td><b>200</b></td><td>OK | fine</td></tr><tr><td>404</td></tr></tbody></table>')
    md = stable(h)
    assert "| Code | Meaning |\n| --- | --- |\n| **200** | OK &#124; fine |\n| 404 |  |" in md, md
    back = md_to_html(md)
    assert "<th>Code</th>" in back and "<td><b>200</b></td>" in back, back
    agent = "| a | b |\n|:--|--:|\n| x \\| y | z |\n"
    assert "<td>x | y</td>" in md_to_html(agent), md_to_html(agent)


def test_sanitize_raw_lines():
    h = md_to_html('<aside class="card" onclick="x()"><img src=x onerror=alert(1)></aside>\n'
                   '<script>alert(1)</script>\n<iframe srcdoc="x"></iframe>\n<a href="javascript:alert(1)">x</a>\n'
                   'the onset = 5 stays')
    assert "onclick" not in h and "onerror" not in h and "<script" not in h and "<iframe" not in h, h
    assert "javascript:" not in h and "the onset = 5 stays" in h, h


def test_slugs_and_split():
    two = split_by_h1("<h1>One</h1><p>a</p><h1>Two</h1><p>b</p>")
    assert [t for t, _ in two] == ["One", "Two"]
    assert slug("Cap 1 — Introducción") == "cap-1-introduccion"
    assert slug(split_by_h1("<h1>Q&amp;A</h1>")[0][0]) == "q-a"


if __name__ == "__main__":
    test_round_trip()
    test_viz_fences()
    test_unclosed_fence_stays_text()
    test_escaping()
    test_links_code_pre_sub_sup()
    test_tables()
    test_sanitize_raw_lines()
    test_slugs_and_split()
    print("ok")
