from __future__ import annotations

import hashlib
import re
import unicodedata
from urllib.parse import urldefrag, urljoin, urlparse, urlunparse

from bs4 import BeautifulSoup, Tag

from .models import ExtractedDocument, ExtractedSection

ALLOWED_HOSTS = {"edb.gov.hk", "www.edb.gov.hk"}
CONTENT_SELECTORS = (
    ".generic_page_content",
    "main",
    "[role='main']",
    "article",
    "#content",
    ".content-body",
)
BLOCK_TAGS = ("h1", "h2", "h3", "h4", "p", "li", "td")


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKC", value)
    value = value.replace("\xa0", " ")
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    lines = [line.strip() for line in value.splitlines()]
    return "\n".join(line for line in lines if line).strip()


def canonicalize_url(base_url: str, href: str) -> str | None:
    href = href.strip()
    if not href or href.startswith(("mailto:", "tel:", "javascript:")):
        return None
    absolute, _fragment = urldefrag(urljoin(base_url, href))
    parsed = urlparse(absolute)
    hostname = (parsed.hostname or "").lower()
    if parsed.scheme not in {"http", "https"} or hostname not in ALLOWED_HOSTS:
        return None
    normalized_netloc = "www.edb.gov.hk"
    return urlunparse(("https", normalized_netloc, parsed.path, "", parsed.query, ""))


def _content_root(soup: BeautifulSoup) -> Tag:
    for selector in CONTENT_SELECTORS:
        candidate = soup.select_one(selector)
        if isinstance(candidate, Tag):
            return candidate
    body = soup.body
    if isinstance(body, Tag):
        return body
    return soup


def _title(soup: BeautifulSoup, root: Tag) -> str:
    heading = soup.find("h1") or root.find(["h1", "h2"])
    if heading:
        value = normalize_text(heading.get_text(" ", strip=True))
        if value:
            return value
    if soup.title:
        value = normalize_text(soup.title.get_text(" ", strip=True))
        return re.sub(r"\s*[-–—]\s*教育局\s*$", "", value).strip()
    return "EDB primary education"


def _sections(root: Tag, fallback_title: str) -> list[ExtractedSection]:
    for unwanted in root.select("script, style, noscript, nav, footer, form, svg"):
        unwanted.decompose()

    sections: list[ExtractedSection] = []
    current_heading = fallback_title
    current_lines: list[str] = []
    seen: set[str] = set()

    def flush() -> None:
        nonlocal current_lines
        text = normalize_text("\n".join(current_lines))
        if text:
            sections.append(ExtractedSection(heading=current_heading, text=text))
        current_lines = []

    for element in root.find_all(BLOCK_TAGS):
        if not isinstance(element, Tag):
            continue
        text = normalize_text(element.get_text(" ", strip=True))
        if not text or text in seen:
            continue
        seen.add(text)
        if element.name in {"h1", "h2", "h3", "h4"}:
            flush()
            current_heading = text
        else:
            current_lines.append(text)
    flush()

    if sections:
        return sections

    text = normalize_text(root.get_text("\n", strip=True))
    return [ExtractedSection(heading=fallback_title, text=text)] if text else []


def extract_document(html: str, url: str, *, discover_links: bool = False) -> ExtractedDocument:
    soup = BeautifulSoup(html, "html.parser")
    root = _content_root(soup)
    title = _title(soup, root)
    sections = _sections(root, title)
    normalized_content = normalize_text(
        "\n\n".join(f"{section.heading}\n{section.text}" for section in sections)
    )
    if not normalized_content:
        raise ValueError("No meaningful content could be extracted from the page")

    discovered: list[dict[str, str]] = []
    if discover_links:
        seen_urls: set[str] = set()
        for anchor in root.find_all("a", href=True):
            link = canonicalize_url(url, str(anchor["href"]))
            label = normalize_text(anchor.get_text(" ", strip=True))
            if link and label and link not in seen_urls:
                seen_urls.add(link)
                discovered.append({"url": link, "title": label})

    return ExtractedDocument(
        url=canonicalize_url(url, url) or url,
        title=title,
        normalized_content=normalized_content,
        content_hash=hashlib.sha256(normalized_content.encode("utf-8")).hexdigest(),
        sections=sections,
        discovered_links=discovered,
    )


def build_chunks(document: ExtractedDocument, target_size: int = 900) -> list[dict[str, object]]:
    chunks: list[dict[str, object]] = []
    position = 0
    for section in document.sections:
        paragraphs = [part for part in section.text.split("\n") if part.strip()]
        buffer: list[str] = []
        buffer_size = 0
        for paragraph in paragraphs:
            if buffer and buffer_size + len(paragraph) > target_size:
                text = normalize_text("\n".join(buffer))
                chunk_id = hashlib.sha256(
                    f"{document.url}:{section.heading}:{position}:{text}".encode()
                ).hexdigest()[:24]
                chunks.append(
                    {
                        "chunk_id": chunk_id,
                        "url": document.url,
                        "page_title": document.title,
                        "section_title": section.heading,
                        "text": text,
                        "position": position,
                    }
                )
                position += 1
                buffer = []
                buffer_size = 0
            buffer.append(paragraph)
            buffer_size += len(paragraph)
        if buffer:
            text = normalize_text("\n".join(buffer))
            chunk_id = hashlib.sha256(
                f"{document.url}:{section.heading}:{position}:{text}".encode()
            ).hexdigest()[:24]
            chunks.append(
                {
                    "chunk_id": chunk_id,
                    "url": document.url,
                    "page_title": document.title,
                    "section_title": section.heading,
                    "text": text,
                    "position": position,
                }
            )
            position += 1
    return chunks
