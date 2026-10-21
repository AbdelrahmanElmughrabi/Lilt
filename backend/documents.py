"""Turn Markdown into ordered, reviewable narration sections."""
from __future__ import annotations

import re
from html.parser import HTMLParser
from markdown_it import MarkdownIt

from .speech_text import normalize_symbols
from .limits import markdown_text

DEFAULT_OPTIONS = {"include_code": False, "heading_pause": 0.6, "paragraph_pause": 0.3}


class PlainHTML(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.hidden += 1
        if tag in {"p", "br", "div", "li", "h1", "h2", "h3"}:
            self.parts.append(" ")

    def handle_endtag(self, tag):
        if tag in {"script", "style"}:
            self.hidden = max(0, self.hidden - 1)
        if tag in {"p", "br", "div", "li", "h1", "h2", "h3"}:
            self.parts.append(" ")

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def html_text(value):
    parser = PlainHTML()
    parser.feed(value)
    return " ".join("".join(parser.parts).split())


def inline_text(tokens):
    parts = []
    autolink = False
    hidden = 0
    for token in tokens or []:
        if token.type == "html_inline":
            if re.match(r"<\s*(?:script|style)\b", token.content, re.I):
                hidden += 1
            elif re.match(r"<\s*/\s*(?:script|style)\b", token.content, re.I):
                hidden = max(0, hidden - 1)
            elif not hidden:
                parts.append(html_text(token.content))
            continue
        if hidden:
            continue
        if token.type == "link_open":
            autolink = token.markup == "autolink"
        elif token.type == "link_close":
            autolink = False
        elif not autolink:
            if token.type in {"text", "code_inline"}:
                parts.append(token.content)
            elif token.type in {"softbreak", "hardbreak"}:
                parts.append(" ")
            elif token.type == "image":
                parts.append(inline_text(token.children) or token.content)
    return " ".join("".join(parts).split())


def section_text(text, limit=420):
    """Split at sentence/word boundaries without dropping any words."""
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z0-9“"\'])', text)
    result, current = [], ""
    for sentence in sentences:
        for word in sentence.split():
            if current and len(current) + len(word) + 1 > limit:
                result.append(current)
                current = ""
            current = f"{current} {word}".strip()
        if len(current) >= limit * 0.65:
            result.append(current)
            current = ""
    if current:
        result.append(current)
    return result


def prepare(markdown: str, options: dict | None = None, fallback_title="Untitled reading"):
    markdown_text(markdown)
    if options is not None and not isinstance(options, dict):
        raise ValueError('Reading options must be an object.')
    from .settings import validate_settings
    validate_settings({key: value for key, value in (options or {}).items() if key in DEFAULT_OPTIONS})
    settings = DEFAULT_OPTIONS | {key: value for key, value in (options or {}).items() if key in DEFAULT_OPTIONS}
    for key in ("heading_pause", "paragraph_pause"):
        settings[key] = max(0.0, min(2.0, float(settings[key])))
    omissions = {"code_blocks": 0, "metadata": 0}
    frontmatter = re.match(r"\A\ufeff?---\s*\n.*?\n(?:---|\.\.\.)\s*(?:\n|$)", markdown, re.S)
    if frontmatter:
        markdown = markdown[frontmatter.end():]
        omissions["metadata"] = 1
    tokens = MarkdownIt("commonmark", {"html": True}).enable("table").parse(markdown)
    blocks, title = [], ""
    kind = "paragraph"
    in_table, cells = False, []
    for token in tokens:
        if token.type == "heading_open":
            kind = "heading"
        elif token.type == "heading_close":
            kind = "paragraph"
        elif token.type == "table_open":
            in_table = True
        elif token.type == "table_close":
            in_table = False
        elif token.type == "tr_open":
            cells = []
        elif token.type == "tr_close":
            if cells:
                blocks.append({"kind": "table", "text": "; ".join(cells) + "."})
        elif token.type == "inline":
            content = inline_text(token.children)
            if content:
                if in_table:
                    cells.append(content)
                else:
                    blocks.append({"kind": kind, "text": content})
                    if kind == "heading" and not title:
                        title = content
        elif token.type in {"fence", "code_block"}:
            if settings["include_code"]:
                content = " ".join(token.content.split())
                if content:
                    blocks.append({"kind": "code", "text": content})
            else:
                omissions["code_blocks"] += 1
        elif token.type == "html_block":
            content = html_text(token.content)
            if content:
                blocks.append({"kind": "paragraph", "text": content})
    unread_symbols = []
    for block in blocks:
        block['text'], unread = normalize_symbols(block['text'])
        unread_symbols.extend(unread)
    chunks = []
    for block_index, block in enumerate(blocks):
        sections = section_text(block["text"])
        pause = settings["heading_pause"] if block["kind"] == "heading" else settings["paragraph_pause"]
        for index, text in enumerate(sections):
            chunks.append({"text": text, "block": block_index, "pause": pause if index == len(sections) - 1 else 0.12})
    spoken = "\n\n".join(block["text"] for block in blocks if block['text'])
    return {"title": title or fallback_title, "text": spoken, "blocks": blocks, "chunks": chunks,
            "words": len(spoken.split()), "omissions": omissions, "options": settings,
            "unread_symbols": unread_symbols, "unread_count": len(unread_symbols)}
