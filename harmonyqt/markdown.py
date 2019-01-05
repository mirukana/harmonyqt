# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import re

import markdown2
from markdownify import markdownify

CONVERT_TO_MD_EXTRAS = [
    # Insert line break on \n instead of required two spaces at line end:
    "break-on-newline",
    # Disable _ and __ for italic/bold, only leave * and **:
    "code-friendly",
    # Allow lists to be after a paragraph without an empty line between them:
    "cuddled-lists",
    # Support GitHub ``` code blocks (needs pygments for syntax highlighting):
    "fenced-code-blocks",
    # Parse lines starting with `>>>` as Python interpreter code:
    "pyshell",
    # Parse ~~text~~ as strikethrough
    "strike",
    # Allow GitHub tables syntax, e.g. `a | b | c\n--- | --- | ---\nx | y | z`:
    "tables",
    # Require `# Titles` to have a space between the # and text:
    "tag-friendly",
    # Allow GitHub-style task lists, e.g. `- [x] thing`:
    "task_list",
    # Allow Google Code Wiki tables syntax, e.g. `a || b || c\nx || y || z`:
    "wiki-tables",
]

CONVERT_TO_MD_DISABLED_EXTRAS = [
    # Allow usinbg a `markdown="1"` attribute in block HTML tags to process the
    # text inside as markdown.
    # The Markdown cannot be on the same line as the block HTML element.
    "markdown-in-html",
    # Parse lines starting with `>!` as spoilers, similar to Stack Overflow:
    # Impossible to make it cross-client since Riot doesn't parse span style
    "spoiler",
    # Support foot notes, e.g. `Some text, see [^other-thing]`;
    # (bottom) `[^other-thing]: Description`:
    "footnotes",
    # Generate id attributes for titles,
    # e.g. `# My Title` → `<h1 id="my-title">My Title</h1>`:
    "header-ids",
    # Enable metadata parsing,
    # see https://github.com/trentm/python-markdown2/wiki/metadata
    "metadata",
    # See https://github.com/trentm/python-markdown2/wiki/numbering
    "numbering",
    # Generate a table of content for titles, experimental:
    "toc",
]

_TO_MARKDOWN = markdown2.Markdown(extras    = CONVERT_TO_MD_EXTRAS,
                                  safe_mode = "escape")


def from_html(html: str) -> str:
    return markdownify(html)


def to_html(markdown: str) -> str:
    html = _TO_MARKDOWN.convert(markdown)

    # Apply a class to \> escaped quotes
    html = re.sub(r"(<p>|<br */?>\s*)(>.*?)(?=\s*</p>|<br */?>)",
                  r"\1<span class=escaped-quote>\2</span>",
                  html,
                  flags=re.DOTALL)

    # Qt only knows <s> for striketrough, replace <del> and <strike>
    html = re.sub(r"(</?)\s*(del|strike)>", r"\1s>", html)
    return html
