#!/usr/bin/env python3
"""CFP+ content pipeline: content/pages/<ID>.md  ->  <ID>/index.html

Purpose
    Let editors add or update a page by writing ONE Markdown file, without
    touching HTML, CSS, nginx or the Dockerfile.

Safety rules (enforced, build fails otherwise)
    1. File name must be <ID>.md and front matter `id` must equal <ID>
       (numeric digits only, leading zeros preserved).
    2. `parent` must already exist (a hand-written <parent>/index.html or
       another content page). This tool never creates or changes Registry,
       Canonical ID or Parent data; it only renders what the editor wrote.
    3. An existing hand-written <ID>/index.html is NEVER overwritten.
       Only files carrying GENERATED_MARK may be replaced.
    4. Legacy namespace 66666 is rejected (PUBLIC_CURRENT_SYSTEM.md rule 7).
    5. Markdown is rendered with HTML escaped: raw HTML / <script> in content
       cannot reach the page. Only http(s), mailto and site-relative links.
    6. `draft: true` pages are validated but not published.

Usage
    python3 tools/build_pages.py              # render into the repo root
    python3 tools/build_pages.py --out DIR    # render into another root
    python3 tools/build_pages.py --check      # validate only, write nothing
Standard library only (no pip install needed).
"""
from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = ROOT / "content" / "pages"
GENERATED_MARK = "<!-- cfp-generated: tools/build_pages.py -->"
ID_RE = re.compile(r"^[0-9]{1,24}$")
LEGACY_PREFIXES = ("66666",)
REQUIRED = ("id", "title", "parent")
ALLOWED_KEYS = {"id", "title", "description", "parent", "lang", "status", "draft", "updated"}
ALLOWED_LANGS = {"vi", "en", "fr", "de", "es", "ja", "ko", "zh", "ru", "ar", "hi", "pt", "it", "th", "id"}


class ContentError(Exception):
    pass


# ---------------------------------------------------------------- front matter
def parse_page(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    if not text.startswith("---\n"):
        raise ContentError(f"{path.name}: missing front matter (must start with ---)")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ContentError(f"{path.name}: front matter not closed with ---")
    meta: dict[str, str] = {}
    for n, line in enumerate(text[4:end].split("\n"), start=2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            raise ContentError(f"{path.name}:{n}: expected 'key: value'")
        k, v = line.split(":", 1)
        k, v = k.strip(), v.strip()
        if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
            v = v[1:-1]
        if k not in ALLOWED_KEYS:
            raise ContentError(f"{path.name}:{n}: unknown key '{k}' (allowed: {', '.join(sorted(ALLOWED_KEYS))})")
        meta[k] = v
    return meta, text[end + 5:]


# ---------------------------------------------------------------- markdown (safe subset)
def _safe_href(url: str) -> str | None:
    u = url.strip()
    if re.match(r"^(https?://|mailto:)", u, re.I) or u.startswith("/") or u.startswith("#"):
        return u
    return None  # javascript:, data:, relative tricks -> dropped


def inline(s: str) -> str:
    out, pos = [], 0
    code_re = re.compile(r"`([^`]+)`")
    for m in code_re.finditer(s):
        out.append(_inline_text(s[pos:m.start()]))
        out.append(f"<code>{html.escape(m.group(1))}</code>")
        pos = m.end()
    out.append(_inline_text(s[pos:]))
    return "".join(out)


def _inline_text(s: str) -> str:
    links: list[str] = []

    def link(m: re.Match) -> str:
        label, href = m.group(1), _safe_href(m.group(2))
        label_html = _emph(html.escape(label))
        if href is None:
            links.append(label_html)
        else:
            ext = href.lower().startswith(("http://", "https://"))
            rel = ' target="_blank" rel="noopener noreferrer"' if ext else ""
            links.append(f'<a href="{html.escape(href, quote=True)}"{rel}>{label_html}</a>')
        return f"\x00{len(links) - 1}\x00"

    s = re.sub(r"\[([^\]]+)\]\(((?:[^()\s]|\([^()\s]*\))+)\)", link, s)
    s = _emph(html.escape(s))
    return re.sub(r"\x00(\d+)\x00", lambda m: links[int(m.group(1))], s)


def _emph(s: str) -> str:
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", s)
    return s


def render_markdown(md: str) -> str:
    lines = md.split("\n")
    out: list[str] = []
    para: list[str] = []
    i = 0

    def flush():
        if para:
            out.append("<p>" + "<br>".join(inline(p) for p in para) + "</p>")
            para.clear()

    while i < len(lines):
        line = lines[i]
        st = line.strip()
        if st.startswith("```"):
            flush()
            i += 1
            buf = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            out.append("<pre><code>" + html.escape("\n".join(buf)) + "</code></pre>")
        elif not st:
            flush()
        elif m := re.match(r"^(#{1,4})\s+(.*)$", st):
            flush()
            lvl = max(2, len(m.group(1)) + 1)  # page <h1> is the title
            out.append(f"<h{lvl}>{inline(m.group(2))}</h{lvl}>")
        elif re.match(r"^(-{3,}|\*{3,})$", st):
            flush()
            out.append("<hr>")
        elif st.startswith(">"):
            flush()
            buf = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip()[1:].strip())
                i += 1
            out.append("<blockquote><p>" + "<br>".join(inline(b) for b in buf) + "</p></blockquote>")
            continue
        elif re.match(r"^([-*]|\d+\.)\s+", st):
            flush()
            ordered = bool(re.match(r"^\d+\.", st))
            tag = "ol" if ordered else "ul"
            items = []
            while i < len(lines) and re.match(r"^([-*]|\d+\.)\s+", lines[i].strip()):
                items.append("<li>" + inline(re.sub(r"^([-*]|\d+\.)\s+", "", lines[i].strip())) + "</li>")
                i += 1
            out.append(f"<{tag}>" + "".join(items) + f"</{tag}>")
            continue
        else:
            para.append(st)
        i += 1
    flush()
    return "\n".join(out)


# ---------------------------------------------------------------- page template
NAV = ('<nav aria-label="Điều hướng CFP+"><a href="/000/">Giới Thiệu</a>'
       '<a href="/0123456789/">10 Chương</a><a href="/69/">HUB 69</a>'
       '<a href="/6/">AI 🤖</a><a href="/28882/">CTTTC</a></nav>')


def page_html(meta: dict, body_html: str, crumbs: list[tuple[str, str]], children: list[tuple[str, str]]) -> str:
    e = html.escape
    title, pid = meta["title"], meta["id"]
    desc = meta.get("description") or title
    crumb_html = " • ".join(f'<a href="/{e(c)}/">{e(t)}</a>' for c, t in crumbs)
    status = meta.get("status", "").strip()
    status_html = (f'<div class="status"><span class="status-dot"></span><strong>{e(status)}</strong></div>'
                   if status else "")
    child_html = ""
    if children:
        cards = "".join(f'<a class="chapter-card" href="/{e(c)}/"><span class="chapter-id">{e(c)}</span>'
                        f"<strong>{e(t)}</strong></a>" for c, t in children)
        child_html = f'<section class="section"><h2>Trang Con</h2><div class="chapter-grid">{cards}</div></section>'
    updated = f" • Cập nhật {e(meta['updated'])}" if meta.get("updated") else ""
    return f"""<!doctype html>
{GENERATED_MARK}
<!-- source: content/pages/{e(pid)}.md — edit that file, not this one -->
<html lang="{e(meta.get('lang', 'vi'))}">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="{e(desc, quote=True)}"><meta property="og:title" content="{e(title, quote=True)}"><meta property="og:description" content="{e(desc, quote=True)}"><meta property="og:url" content="https://cfp.plus/{e(pid)}/"><link rel="canonical" href="https://cfp.plus/{e(pid)}/"><title>{e(pid)} • {e(title)}</title><link rel="stylesheet" href="/styles.css"></head>
<body>
<header class="site-header"><a class="brand" href="/">CFP+</a>{NAV}</header>
<main><article>
<section class="hero"><p class="eyebrow">{crumb_html}</p><p class="eyebrow">ID {e(pid)}</p><h1>{e(title)}</h1>{status_html}</section>
<section class="section">
{body_html}
</section>
{child_html}
</article></main>
<footer><p>CFP+ • Only Plus+ For Life</p><p>ID {e(pid)}{updated}</p><p><a href="mailto:contact@cfp.plus">contact@cfp.plus</a></p></footer>
</body></html>
"""


# ---------------------------------------------------------------- build
def existing_title(page_dir: Path) -> str | None:
    f = page_dir / "index.html"
    if not f.is_file():
        return None
    m = re.search(r"<title>(.*?)</title>", f.read_text(encoding="utf-8", errors="replace"), re.S)
    return html.unescape(m.group(1)).strip() if m else page_dir.name


def build(out_root: Path, check_only: bool, content_dir: Path = CONTENT_DIR, site_root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    pages: dict[str, tuple[dict, str]] = {}
    files = sorted(content_dir.glob("*.md")) if content_dir.is_dir() else []
    for f in files:
        if f.name.startswith("_") or f.name.upper() == "README.MD":
            continue
        try:
            meta, body = parse_page(f)
            for k in REQUIRED:
                if not meta.get(k):
                    raise ContentError(f"{f.name}: required key '{k}' is missing or empty")
            pid, parent = meta["id"], meta["parent"]
            if f.stem != pid:
                raise ContentError(f"{f.name}: file name must equal id ({pid}.md)")
            for label, v in (("id", pid), ("parent", parent)):
                if not ID_RE.match(v):
                    raise ContentError(f"{f.name}: {label} '{v}' must be digits only")
                if v.startswith(LEGACY_PREFIXES):
                    raise ContentError(f"{f.name}: {label} '{v}' uses legacy namespace 66666 (not allowed)")
            if parent == pid:
                raise ContentError(f"{f.name}: parent cannot equal id")
            if meta.get("lang", "vi") not in ALLOWED_LANGS:
                raise ContentError(f"{f.name}: lang '{meta['lang']}' not in {sorted(ALLOWED_LANGS)}")
            if pid in pages:
                raise ContentError(f"{f.name}: duplicate id {pid}")
            pages[pid] = (meta, body)
        except ContentError as ex:
            errors.append(str(ex))

    published = {k: v for k, v in pages.items() if v[0].get("draft", "false").lower() != "true"}

    for pid, (meta, _) in pages.items():
        target = site_root / pid / "index.html"
        if target.is_file() and GENERATED_MARK not in target.read_text(encoding="utf-8", errors="replace"):
            errors.append(f"{pid}.md: {pid}/index.html is a hand-written page; refusing to overwrite "
                          f"(migrate it explicitly by deleting the HTML in the same reviewed PR)")
        parent = meta["parent"]
        if parent not in published and existing_title(site_root / parent) is None:
            errors.append(f"{pid}.md: parent {parent} does not exist (no {parent}/index.html and no published {parent}.md)")

    # cycle check
    for pid in published:
        seen, cur = set(), pid
        while cur in published:
            if cur in seen:
                errors.append(f"{pid}.md: parent chain forms a cycle")
                break
            seen.add(cur)
            cur = published[cur][0]["parent"]

    if errors:
        return errors

    def title_of(x: str) -> str:
        if x in published:
            return published[x][0]["title"]
        t = existing_title(site_root / x) or x
        return t

    for pid, (meta, body) in published.items():
        crumbs, cur, guard = [], meta["parent"], 0
        while cur and guard < 12:
            crumbs.append((cur, title_of(cur)))
            cur = published[cur][0]["parent"] if cur in published else ""
            guard += 1
        crumbs.reverse()
        children = sorted(((c, m["title"]) for c, (m, _) in published.items() if m["parent"] == pid),
                          key=lambda t: (len(t[0]), t[0]))
        doc = page_html(meta, render_markdown(body), crumbs, children)
        if not check_only:
            dest = out_root / pid / "index.html"
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(doc, encoding="utf-8")
        print(f"{'OK  ' if check_only else 'WROTE'} /{pid}/  <- content/pages/{pid}.md")
    drafts = sorted(set(pages) - set(published))
    if drafts:
        print("draft (validated, not published): " + ", ".join(drafts))
    return []


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=ROOT, help="site root to write into (default: repo root)")
    ap.add_argument("--check", action="store_true", help="validate only; write nothing")
    a = ap.parse_args(argv)
    errs = build(a.out.resolve(), a.check)
    if errs:
        print("CONTENT ERRORS — nothing was published:", file=sys.stderr)
        for e in errs:
            print("  - " + e, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
