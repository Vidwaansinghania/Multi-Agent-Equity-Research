"""Markdown parsing shared by the Method 2 export builders.

Turns a run's markdown into a flat list of typed blocks that the DOCX and PDF
builders both render. Deliberately small: it handles the subset of Obsidian
markdown the agents actually write, and raises on nothing, because a builder
that dies on an unexpected line loses a whole run's artefact.

Block shapes
    {"type": "heading",  "level": 1..6, "text": str}
    {"type": "para",     "text": str}
    {"type": "list",     "ordered": bool, "items": [(indent:int, text:str)]}
    {"type": "table",    "header": [str], "rows": [[str]], "align": [str]}
    {"type": "code",     "lang": str, "text": str}
    {"type": "quote",    "text": str}
    {"type": "rule"}
    {"type": "callout",  "kind": str, "title": str, "text": str}

Front-matter is parsed out separately by read_note() and never rendered as body.
"""

import re

# Sentences naming local plumbing. Stripped from anything that reaches a
# published artefact. Matched and removed by sentence, not by paragraph,
# because a plumbing clause often sits at the end of a paragraph worth keeping.
PLUMBING = re.compile(
    r"(build_scripts?|build_report|build_workbook|build_workpapers|\.py\b|"
    r"scratchpad|re-?run the (script|build)|rebuild the (export|PDF|DOCX)|"
    r"local python|vault python|\.claude[/\\]|statements\.csv|model\.py|run folder|"
    r"Method 2/build)",
    re.I)

_SENT = re.compile(r"(?<=[.!?])\s+")

# Every sentence drop_plumbing removed this process. Read it back after a build:
# the first IREN pass over-removed a whole paragraph and the diff is what caught
# it, so a silent strip is not good enough.
DROPPED = []


def drop_plumbing(text):
    """Drop sentences naming local plumbing, keeping the rest of the paragraph."""
    parts = _SENT.split(text)
    kept = []
    for p in parts:
        if PLUMBING.search(p):
            DROPPED.append(p.strip())
        else:
            kept.append(p)
    return " ".join(kept).strip()


# --------------------------------------------------------------- inline text --

_WIKI = re.compile(r"\[\[([^\]]+)\]\]")
_MDLINK = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
_IMG = re.compile(r"!\[[^\]]*\]\([^)]*\)")


def _clean_wikilink(m):
    inner = m.group(1)
    # [[path/to/note|Label]] -> Label ; [[note]] -> note
    if "|" in inner:
        return inner.split("|", 1)[1]
    return inner.rsplit("/", 1)[-1]


def plain(text):
    """Inline markdown to readable plain text."""
    text = _IMG.sub("", text)
    text = _WIKI.sub(_clean_wikilink, text)
    text = _MDLINK.sub(r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"~~([^~]+)~~", r"\1", text)
    return text.strip()


_RUN = re.compile(r"(\*\*[^*]+\*\*|(?<!\*)\*[^*]+\*(?!\*)|`[^`]+`)")


def inline_runs(text):
    """Split inline markdown into (text, bold, italic, mono) tuples."""
    text = _IMG.sub("", text)
    text = _WIKI.sub(_clean_wikilink, text)
    text = _MDLINK.sub(r"\1", text)
    out = []
    for piece in _RUN.split(text):
        if not piece:
            continue
        if piece.startswith("**") and piece.endswith("**") and len(piece) > 4:
            out.append((piece[2:-2], True, False, False))
        elif piece.startswith("`") and piece.endswith("`") and len(piece) > 2:
            out.append((piece[1:-1], False, False, True))
        elif piece.startswith("*") and piece.endswith("*") and len(piece) > 2:
            out.append((piece[1:-1], False, True, False))
        else:
            out.append((piece, False, False, False))
    return out or [(text, False, False, False)]


# ------------------------------------------------------------- front-matter --

def split_frontmatter(text):
    """Return (frontmatter_text_or_None, body). Does not parse the YAML."""
    if not text.startswith("---"):
        return None, text
    end = text.find("\n---", 3)
    if end == -1:
        return None, text
    fm = text[3:end].strip("\n")
    body = text[end + 4:].lstrip("\n")
    return fm, body


_SCALAR = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$")


def parse_frontmatter(fm):
    """Flat scalar YAML only — enough for decision.md's typed fields.

    Nested blocks (scenarios, position, models) are returned as raw text under
    their key so a caller can show them without a YAML dependency.
    """
    data, key, buf = {}, None, []
    for line in (fm or "").splitlines():
        if not line.strip():
            continue
        if line[0] in " \t":
            buf.append(line.strip())
            continue
        if key and buf:
            data[key] = "\n".join(buf)
            buf = []
        m = _SCALAR.match(line)
        if not m:
            continue
        key, val = m.group(1), m.group(2).strip()
        if val in (">", "|", ""):
            buf = []
            continue
        data[key] = val.strip('"\'')
        key = None
    if key and buf:
        data[key] = "\n".join(buf)
    return data


def num(data, key, default=None):
    """Read a numeric front-matter field without trusting its formatting."""
    try:
        return float(str(data[key]).replace(",", "").replace("%", "").strip())
    except (KeyError, ValueError, TypeError):
        return default


# -------------------------------------------------------------- block parse --

_H = re.compile(r"^(#{1,6})\s+(.*)$")
_UL = re.compile(r"^(\s*)[-*+]\s+(.*)$")
_OL = re.compile(r"^(\s*)\d+[.)]\s+(.*)$")
_RULE = re.compile(r"^\s*([-*_])\s*(\1\s*){2,}$")
_ROW = re.compile(r"^\s*\|(.+)\|\s*$")
_SEP = re.compile(r"^\s*\|[\s:|-]+\|\s*$")
_CALLOUT = re.compile(r"^>\s*\[!(\w+)\]\s*(.*)$")


def _cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def parse_blocks(body, strip_plumbing=False):
    """Markdown body to a flat block list."""
    lines = body.replace("\r\n", "\n").split("\n")
    blocks, i, n = [], 0, len(lines)

    def flush_para(buf):
        if not buf:
            return
        text = " ".join(x.strip() for x in buf).strip()
        if strip_plumbing:
            text = drop_plumbing(text)
        if text:
            blocks.append({"type": "para", "text": text})

    para = []
    while i < n:
        line = lines[i]

        if not line.strip():
            flush_para(para); para = []
            i += 1
            continue

        if line.lstrip().startswith("```"):
            flush_para(para); para = []
            lang = line.lstrip()[3:].strip()
            i += 1
            buf = []
            while i < n and not lines[i].lstrip().startswith("```"):
                buf.append(lines[i]); i += 1
            i += 1
            blocks.append({"type": "code", "lang": lang, "text": "\n".join(buf)})
            continue

        if _RULE.match(line):
            flush_para(para); para = []
            blocks.append({"type": "rule"})
            i += 1
            continue

        m = _H.match(line)
        if m:
            flush_para(para); para = []
            txt = plain(m.group(2))
            if not (strip_plumbing and PLUMBING.search(txt)):
                blocks.append({"type": "heading", "level": len(m.group(1)),
                               "text": txt})
            i += 1
            continue

        # table: a pipe row followed by a separator row
        if _ROW.match(line) and i + 1 < n and _SEP.match(lines[i + 1]):
            flush_para(para); para = []
            header = _cells(line)
            align = []
            for spec in _cells(lines[i + 1]):
                if spec.startswith(":") and spec.endswith(":"):
                    align.append("center")
                elif spec.endswith(":"):
                    align.append("right")
                else:
                    align.append("left")
            i += 2
            rows = []
            while i < n and _ROW.match(lines[i]):
                cells = _cells(lines[i])
                cells += [""] * (len(header) - len(cells))
                rows.append([plain(c) for c in cells[:len(header)]])
                i += 1
            blocks.append({"type": "table", "header": [plain(h) for h in header],
                           "rows": rows, "align": align})
            continue

        if line.lstrip().startswith(">"):
            flush_para(para); para = []
            co = _CALLOUT.match(line.lstrip())
            buf, kind, title = [], None, ""
            if co:
                kind, title = co.group(1).lower(), plain(co.group(2))
                i += 1
            while i < n and lines[i].lstrip().startswith(">"):
                buf.append(lines[i].lstrip()[1:].strip())
                i += 1
            text = " ".join(x for x in buf if x).strip()
            if strip_plumbing:
                text = drop_plumbing(text)
            if kind:
                blocks.append({"type": "callout", "kind": kind, "title": title,
                               "text": text})
            elif text:
                blocks.append({"type": "quote", "text": text})
            continue

        mu, mo = _UL.match(line), _OL.match(line)
        if mu or mo:
            flush_para(para); para = []
            ordered = bool(mo)
            items = []
            while i < n:
                m2 = _OL.match(lines[i]) if ordered else _UL.match(lines[i])
                if not m2:
                    # a wrapped continuation line belongs to the last item
                    if items and lines[i].startswith(("  ", "\t")) \
                            and not _UL.match(lines[i]) and not _OL.match(lines[i]) \
                            and lines[i].strip():
                        ind, txt = items[-1]
                        items[-1] = (ind, txt + " " + lines[i].strip())
                        i += 1
                        continue
                    break
                indent = len(m2.group(1).replace("\t", "    ")) // 2
                txt = m2.group(2).strip()
                if strip_plumbing:
                    txt = drop_plumbing(txt)
                if txt:
                    items.append((indent, txt))
                i += 1
            if items:
                blocks.append({"type": "list", "ordered": ordered, "items": items})
            continue

        para.append(line)
        i += 1

    flush_para(para)
    return blocks


def read_note(path, strip_plumbing=False):
    """Read a markdown file to (frontmatter_dict, blocks). Missing file -> ({}, [])."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return {}, []
    fm, body = split_frontmatter(text)
    return parse_frontmatter(fm), parse_blocks(body, strip_plumbing=strip_plumbing)


def first_heading(blocks, default=""):
    for b in blocks:
        if b["type"] == "heading":
            return b["text"]
    return default


# Kept so an older call site keeps working.
strip_vault = drop_plumbing
