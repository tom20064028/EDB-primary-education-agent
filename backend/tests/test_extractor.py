from edb_agent.extractor import build_chunks, canonicalize_url, extract_document, normalize_text

HTML = """
<html lang="zh-Hant">
  <head><title>小學教育 - 教育局</title></head>
  <body>
    <nav><a href="/tc/unrelated.html">全站選單</a></nav>
    <h1>小學教育</h1>
    <div class="generic_page_content">
      <h2>概覽</h2>
      <p>香港的小學教育資料。</p>
      <a href="/tc/edu-system/primary-secondary/primary/index.html">概覽及工作重點</a>
      <a href="https://example.com/not-allowed">外部連結</a>
    </div>
    <footer>版權所有</footer>
  </body>
</html>
"""


def test_extracts_primary_content_and_direct_links() -> None:
    document = extract_document(
        HTML,
        "https://www.edb.gov.hk/tc/edu-system/primary-secondary/primary.html",
        discover_links=True,
    )

    assert document.title == "小學教育"
    assert "香港的小學教育資料" in document.normalized_content
    assert "全站選單" not in document.normalized_content
    assert "版權所有" not in document.normalized_content
    assert document.discovered_links == [
        {
            "url": "https://www.edb.gov.hk/tc/edu-system/primary-secondary/primary/index.html",
            "title": "概覽及工作重點",
        }
    ]
    assert build_chunks(document)[0]["section_title"] == "概覽"


def test_url_normalization_rejects_unapproved_hosts() -> None:
    base = "https://www.edb.gov.hk/tc/edu-system/primary-secondary/primary.html"
    assert canonicalize_url(base, "http://edb.gov.hk/tc/page.html#part") == (
        "https://www.edb.gov.hk/tc/page.html"
    )
    assert canonicalize_url(base, "https://example.com/page") is None
    assert canonicalize_url(base, "javascript:alert(1)") is None


def test_text_normalization_is_stable() -> None:
    assert normalize_text("ＡＢＣ\u00a0  小學\n\n\n教育") == "ABC 小學\n教育"
