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
    # Allow usinbg a `markdown="1"` attribute in block HTML tags to process the
    # text inside as markdown.
    # The Markdown cannot be on the same line as the block HTML element.
    "markdown-in-html",
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

HTML_TAGS = [
    "!––", "!DOCTYPE", "a", "abbr", "address", "area", "article", "aside",
    "audio", "b", "base", "bdi", "bdo", "blockquote", "body", "br", "button",
    "canvas", "caption", "cite", "code", "col", "colgroup", "data", "datalist",
    "dd", "del", "details", "dfn", "dialog", "div", "dl", "dt", "em", "embed",
    "fieldset", "figure", "footer", "form", "h1", "h2", "h3", "h4", "h5", "h6",
    "head", "header", "hgroup", "hr", "html", "i", "iframe", "img", "input",
    "ins", "kbd", "keygen", "label", "legend", "li", "link", "main", "map",
    "mark", "menu", "menuitem", "meta", "meter", "nav", "noscript", "object",
    "ol", "optgroup", "option", "output", "p", "param", "pre", "progress",
    "q", "rb", "rp", "rt", "rtc", "ruby", "s", "samp", "script", "section",
    "select", "small", "source", "span", "strong", "style", "sub", "summary",
    "sup", "table", "tbody", "td", "template", "textarea", "tfoot", "th",
    "thead", "time", "title", "tr", "track", "u", "ul", "var", "video", "wbr",
]

_TO_MARKDOWN = markdown2.Markdown(extras=CONVERT_TO_MD_EXTRAS)


def from_html(html: str) -> str:
    return markdownify(html)


def to_html(markdown: str) -> str:
    rep = lambda m: "%s%s" % (m.group(1),
                              "".join(("&gt;" for _ in m.group(2))))
    # Prevent parsing anything as HTML tags, but make >quotes work
    markdown = re.sub(r"(^.*[^\s>].*)(>+)", rep, markdown, flags=re.MULTILINE)\
               .replace("<", "&lt;")

    return _TO_MARKDOWN.convert(markdown)
