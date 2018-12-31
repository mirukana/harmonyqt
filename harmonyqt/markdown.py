# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

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
    # Allow usinbg a `markdown="1"` attribute in block HTML tags to process the
    # text inside as markdown.
    # The Markdown cannot be on the same line as the block HTML element.
    "markdown-in-html",
    # Parse lines starting with `>>>` as Python interpreter code:
    "pyshell",
    # Parse lines starting with `>!` as spoilers, similar to Stack Overflow:
    # FIXME: not working very well, also need an inline version.
    "spoiler",
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

_TO_MARKDOWN = markdown2.Markdown(extras=CONVERT_TO_MD_EXTRAS)


def from_html(html: str) -> str:
    return markdownify(html)


def to_html(markdown: str) -> str:
    # Prevent parsing anything as HTML tags
    markdown = markdown.replace("<", "&lt;").replace(">", "&gt;")
    return _TO_MARKDOWN.convert(markdown)
