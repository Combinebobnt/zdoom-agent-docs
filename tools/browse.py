#!/usr/bin/env python3
"""Local browser for this doc tree: rendered markdown, section sidebar, and search.

Serves the tree as-is on 127.0.0.1, with URL paths mapped 1:1 to repo paths so every relative
link and #anchor in the docs works natively. maintainer/, sources.local.md and dot-paths are
never served. Stdlib only; the optional `markdown-it-py` + `mdit-py-plugins` packages (plus
`pygments` for highlighting) upgrade the plain-text fallback to rendered HTML.

Usage:
    python3 tools/browse.py [--port N] [--open]   # serve on http://127.0.0.1:8765/
    python3 tools/browse.py --check               # self-test: deny list, links, anchors
    python3 tools/browse.py --build DIR           # static HTML export (needs markdown-it-py)

Optional dependency setup (a project-local venv keeps it out of the system python):
    python3 -m venv .venv
    .venv/bin/pip install markdown-it-py mdit-py-plugins pygments  # Windows: .venv\\Scripts\\pip.exe
    .venv/bin/python tools/browse.py                  # Windows: .venv\\Scripts\\python.exe
"""
import argparse
import errno
import html
import os
import posixpath
import re
import shutil
import subprocess
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path, PurePosixPath
from urllib.parse import parse_qs, quote, unquote, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sections as S  # noqa: E402
import lookup as L  # noqa: E402

ROOT = S.ROOT.resolve()
DEFAULT_PORT = 8765
SEARCH_CAP = 200
INSTALL_HINT = "python3 -m venv .venv && .venv/bin/pip install markdown-it-py mdit-py-plugins pygments"

DENY_TOP = {"maintainer", "sources.local.md"}
DENY_ANY = {"__pycache__"}
DRIVE_RE = re.compile(r"^[A-Za-z]:")
HREF_RE = re.compile(r'(href)="([^"]*)"')
ID_RE = re.compile(r'\b(?:id|name)="([^"]+)"')
H1_RE = re.compile(r"^#\s+(.*\S)\s*$", re.M)
# Code spans are matched first so example links inside backticks stay unlinked.
FALLBACK_LINK_RE = re.compile(r"(`[^`\n]*`)|\[([^\]\n]*)\]\(([^)\s]+)\)")
AGENT_NOTE_RE = re.compile(r"</h1>\s*(<p>)(.*?</p>)", re.S)
SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


# ---------------------------------------------------------------------------
# Access control and path mapping
# ---------------------------------------------------------------------------

def is_public(rel):
    """rel is a repo-relative posix path string; compared lowercase for case-insensitive FSes."""
    parts = [p.lower() for p in PurePosixPath(rel).parts]
    if not parts:
        return True
    if parts[0] in DENY_TOP:
        return False
    return not any(p.startswith(".") or p in DENY_ANY for p in parts)


def is_servable_file(rel):
    low = rel.lower()
    if low.endswith(".md"):
        return True
    if low == "license":
        return True
    return low.startswith("licenses/") and low.endswith(".txt")


def map_url(url_path):
    """URL path -> (repo-relative posix str, absolute Path), or None if it must 404."""
    decoded = unquote(url_path)
    if "\x00" in decoded or "\\" in decoded:
        return None
    segs = [s for s in decoded.split("/") if s not in ("", ".")]
    for s in segs:
        if s == ".." or ":" in s or DRIVE_RE.match(s):
            return None
    rel = PurePosixPath(*segs).as_posix() if segs else ""
    if not is_public(rel):
        return None
    try:
        path = ROOT.joinpath(*segs).resolve()
        real_rel = path.relative_to(ROOT).as_posix()
    except (ValueError, OSError):
        return None
    if real_rel == ".":
        real_rel = ""
    if not is_public(real_rel):
        return None
    return rel, path


def dir_index(path):
    """The directory's INDEX.md, matched by exact entry name so case-insensitive FSes agree."""
    try:
        names = os.listdir(path)
    except OSError:
        return None
    return path / "INDEX.md" if "INDEX.md" in names else None


def route(url_path):
    """Pure routing decision shared by the server and --check: (status, kind, rel, path)."""
    mapped = map_url(url_path)
    if mapped is None:
        return 404, None, None, None
    rel, path = mapped
    if path.is_dir():
        if url_path and not url_path.endswith("/"):
            return 301, "redirect", rel, path
        idx = dir_index(path)
        if idx is not None:
            return 200, "md", (rel + "/INDEX.md").lstrip("/"), idx
        return 200, "listing", rel, path
    if path.is_file() and is_servable_file(rel):
        return 200, ("md" if rel.lower().endswith(".md") else "text"), rel, path
    return 404, None, None, None


def read_text(path):
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def walk_public_md():
    """Yield repo-relative posix paths of every public .md file, pruning denied dirs."""
    for dirpath, dirnames, filenames in os.walk(ROOT):
        rel_dir = Path(dirpath).relative_to(ROOT).as_posix()
        rel_dir = "" if rel_dir == "." else rel_dir
        dirnames[:] = sorted(d for d in dirnames if is_public(posixpath.join(rel_dir, d)))
        for f in sorted(filenames):
            rel = posixpath.join(rel_dir, f)
            if f.lower().endswith(".md") and is_public(rel):
                yield rel


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def github_slug(value):
    return re.sub(r"[^\w\- ]", "", value.strip().lower()).replace(" ", "-")


def _highlighter():
    try:
        from pygments import highlight
        from pygments.formatters import HtmlFormatter
        from pygments.lexers import get_lexer_by_name
        from pygments.util import ClassNotFound
    except ImportError:
        return None, ""
    fmt = HtmlFormatter(nowrap=True)

    def fn(code, lang, _attrs):
        try:
            lexer = get_lexer_by_name(lang) if lang else None
        except ClassNotFound:
            lexer = None
        if lexer is None:
            return ""
        return f'<pre class="codehilite"><code>{highlight(code, lexer, fmt)}</code></pre>'

    return fn, HtmlFormatter().get_style_defs(".codehilite")


_MD_STATE = {}


def markdown_available():
    """The docs are GitHub-flavored, so the renderer is CommonMark (markdown-it-py) plus tables."""
    if "ok" not in _MD_STATE:
        try:
            from markdown_it import MarkdownIt
            from mdit_py_plugins.anchors import anchors_plugin
        except ImportError:
            _MD_STATE["ok"] = False
            return False
        hl, css = _highlighter()
        md = MarkdownIt("commonmark", {"highlight": hl} if hl else None)
        md.enable(["table", "strikethrough"])
        anchors_plugin(md, max_level=6, slug_func=github_slug)
        _MD_STATE.update(ok=True, md=md, css=css)
    return _MD_STATE["ok"]


def _fallback_link(m):
    if m.group(1):
        return m.group(1)
    return f'[{m.group(2)}](<a href="{m.group(3)}">{m.group(3)}</a>)'


def render_md(text):
    if markdown_available():
        return _MD_STATE["md"].render(text)
    esc = html.escape(text, quote=False)
    return f'<pre class="raw">{FALLBACK_LINK_RE.sub(_fallback_link, esc)}</pre>'


def hide_agent_note(rel, body):
    """Hide an INDEX.md's opening agent-routing paragraph; keep it if it carries a bold warning."""
    if PurePosixPath(rel).name != "INDEX.md":
        return body
    m = AGENT_NOTE_RE.search(body)
    if not m or "<strong>" in m.group(2) or not re.search(r"(CLAUDE|AGENTS)\.md", m.group(2)):
        return body
    return body[:m.start(1)] + '<p class="agent-note" hidden>' + body[m.start(2):]


def page_title(text, fallback):
    m = H1_RE.search(text)
    return m.group(1).strip("` ") if m else fallback


# ---------------------------------------------------------------------------
# Page chrome
# ---------------------------------------------------------------------------

CSS = """
body{margin:0;font:15px/1.5 system-ui,sans-serif;color:#1d1d1f;background:#fff}
header{display:flex;gap:1em;align-items:center;padding:.5em 1em;background:#2b2b33;color:#eee}
header a{color:#fff;font-weight:600;text-decoration:none}
header form{margin-left:auto}
header input{width:22em;padding:.25em .5em}
.wrap{display:flex;min-height:calc(100vh - 2.6em)}
nav{width:16em;flex:none;padding:.75em;background:#f4f4f7;border-right:1px solid #ddd;
  font-size:14px;overflow-y:auto}
nav ul{list-style:none;margin:0;padding-left:1em}
nav>ul{padding-left:0}
nav summary{cursor:pointer}
nav .cur{font-weight:700}
main{flex:1;min-width:0;padding:1em 2em;max-width:60em}
.crumbs{font-size:13px;color:#666;margin-bottom:.5em}
.banner{background:#fff4cc;border:1px solid #e0c060;padding:.4em .7em;margin-bottom:1em}
table{border-collapse:collapse;margin:1em 0;display:block;overflow-x:auto}
th,td{border:1px solid #ccc;padding:.25em .5em;vertical-align:top}
th{background:#f0f0f3}
code{background:#f3f3f6;padding:0 .2em;border-radius:3px}
pre{background:#f6f6f9;padding:.6em;overflow-x:auto;border-radius:4px}
pre code{background:none;padding:0}
pre.raw{white-space:pre-wrap;background:none}
.hit{margin:.6em 0}.hit .snip{color:#555;font-size:13px}
.exact{background:#eef7ee;border:1px solid #9c9;padding:.4em .7em}
"""


class Linker:
    """Turns repo-relative targets into hrefs for the current page (server vs static export)."""

    def __init__(self, page_rel=None, static=False):
        self.static = static
        self.page_dir = posixpath.dirname(page_rel) if page_rel else ""

    def __call__(self, rel, is_dir=False):
        if not self.static:
            return "/" + quote(rel) + ("/" if is_dir and rel else "")
        target = posixpath.join(rel, "INDEX.html") if is_dir else re.sub(r"\.md$", ".html", rel)
        return quote(posixpath.relpath(target, self.page_dir or "."))


def sidebar(link, cur_rel):
    cur_top = cur_rel.split("/", 1)[0] if cur_rel else ""

    def a(rel, label, is_dir=False):
        cls = ' class="cur"' if rel == cur_rel else ""
        return f'<a{cls} href="{link(rel, is_dir)}">{html.escape(label)}</a>'

    out = ["<ul>", f"<li>{a('INDEX.md', 'Home')}</li>", f"<li>{a('README.md', 'README')}</li>"]
    shared_open = " open" if cur_top == "shared" else ""
    out.append(f"<li><details{shared_open}><summary>shared</summary><ul>")
    out.append(f"<li>{a('shared/AUTHORING.md', 'AUTHORING')}</li>")
    out.append(f"<li>{a('shared/ARCHETYPES.md', 'ARCHETYPES')}</li>")
    out.append(f"<li>{a(S.SHARED_CONCEPTS_DIR, 'concepts', True)}</li>")
    out.append("</ul></details></li>")
    for key, sec in S.SECTIONS.items():
        opened = " open" if key == cur_top else ""
        out.append(f"<li><details{opened}><summary>{html.escape(key)}</summary><ul>")
        if (ROOT / sec["index"]).is_file():
            out.append(f"<li>{a(sec['index'], 'INDEX')}</li>")
        for d in sec["dirs"]:
            if (ROOT / d).is_dir():
                out.append(f"<li>{a(d, posixpath.basename(d), True)}</li>")
        out.append("</ul></details></li>")
    out.append("</ul>")
    return "".join(out)


def crumbs(link, rel):
    parts = [p for p in rel.split("/") if p]
    out = [f'<a href="{link("", True)}">root</a>']
    for i, p in enumerate(parts):
        sub = "/".join(parts[: i + 1])
        if i == len(parts) - 1 and not (ROOT / sub).is_dir():
            out.append(html.escape(p))
        else:
            out.append(f'<a href="{link(sub, True)}">{html.escape(p)}</a>')
    return " / ".join(out)


def page(title, body, rel, link, search=True, q=""):
    banner = ""
    if not markdown_available():
        banner = ('<div class="banner">Plain-text mode: <code>markdown-it-py</code> is not installed. '
                  f'For rendered pages: <code>{html.escape(INSTALL_HINT)}</code>, then run '
                  "this tool with the venv's python.</div>")
    form = ""
    if search:
        form = ('<form action="/_search" method="get">'
                f'<input name="q" value="{html.escape(q)}" placeholder="Search docs"></form>')
    return (
        '<!doctype html><html><head><meta charset="utf-8">'
        f"<title>{html.escape(title)} - zdoom-agent-docs</title>"
        f"<style>{CSS}{_MD_STATE.get('css', '')}</style></head><body>"
        f'<header><a href="{link("INDEX.md")}">zdoom-agent-docs</a>{form}</header>'
        f'<div class="wrap"><nav>{sidebar(link, rel)}</nav><main>'
        f'<div class="crumbs">{crumbs(link, rel)}</div>{banner}{body}'
        "</main></div></body></html>"
    )


def listing_body(rel, path):
    names = sorted(n for n in os.listdir(path)
                   if n.lower().endswith(".md") and is_public(posixpath.join(rel, n)))
    items = "".join(f'<li><a href="{quote(n)}">{html.escape(n)}</a></li>' for n in names)
    return f"<h1>{html.escape(rel or 'root')}/</h1><ul>{items}</ul>"


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

class Corpus:
    def __init__(self):
        self._lock = threading.Lock()
        self._cache = {}

    def docs(self):
        """(rel, text) for every public .md, re-reading files whose mtime changed."""
        with self._lock:
            fresh = {}
            for rel in walk_public_md():
                p = ROOT / rel
                try:
                    mtime = p.stat().st_mtime
                except OSError:
                    continue
                old = self._cache.get(rel)
                if old and old[0] == mtime:
                    fresh[rel] = old
                else:
                    try:
                        fresh[rel] = (mtime, read_text(p))
                    except (OSError, UnicodeDecodeError):
                        continue
            self._cache = fresh
            return [(rel, v[1]) for rel, v in fresh.items()]


CORPUS = Corpus()


def _exact_hit(q):
    try:
        result, key = L.resolve(q)
    except Exception as e:  # lookup.py reads with the platform encoding; don't let it kill search
        return None, f"exact lookup failed: {e}"
    if result is None:
        return None, None
    target = getattr(result, "notes_file", None) or result.file
    if target is None:
        target = ROOT / S.SECTIONS[key]["index"]
    rel = Path(target).resolve().relative_to(ROOT).as_posix()
    if isinstance(result, L.InventoryResult):
        desc = f"inventory row in {Path(result.file).relative_to(ROOT).as_posix()}"
    else:
        desc = result.signature.text if result.signature else result.kind
    return (rel, desc, key), None


def search(q):
    """(exact, hits, suggestions, error); hits are (rank, rel, snippet), capped at SEARCH_CAP."""
    q = q.strip()
    if not q:
        return None, [], [], None
    exact, err = _exact_hit(q)
    ql = q.lower()
    hits = []
    for rel, text in CORPUS.docs():
        stem = PurePosixPath(rel).stem.lower()
        h1 = page_title(text, "")
        if ql in stem:
            rank, snip = 0, h1
        elif ql in h1.lower():
            rank, snip = 1, h1
        elif ql in text.lower():
            rank = 2
            snip = next((ln.strip() for ln in text.split("\n") if ql in ln.lower()), "")
        else:
            continue
        hits.append((rank, rel, snip))
    hits.sort(key=lambda h: (h[0], h[1]))
    hits = hits[:SEARCH_CAP]
    suggestions = []
    if not hits and exact is None:
        try:
            suggestions = L.suggest(q, None)
        except Exception:
            suggestions = []
    return exact, hits, suggestions, err


def search_body(q, link):
    exact, hits, suggestions, err = search(q)
    out = [f"<h1>Search: {html.escape(q)}</h1>"]
    if err:
        out.append(f'<p class="banner">{html.escape(err)}</p>')
    if exact:
        rel, desc, key = exact
        out.append(f'<div class="exact">Exact match ({html.escape(key)}): '
                   f'<a href="{link(rel)}">{html.escape(rel)}</a> '
                   f"<code>{html.escape(desc)}</code></div>")
    if hits:
        more = f" (first {SEARCH_CAP})" if len(hits) == SEARCH_CAP else ""
        out.append(f"<p>{len(hits)} matching files{more}</p>")
        for _, rel, snip in hits:
            out.append(f'<div class="hit"><a href="{link(rel)}">{html.escape(rel)}</a>'
                       f'<div class="snip">{html.escape(snip[:240])}</div></div>')
    elif not exact:
        out.append("<p>No matches.</p>")
        if suggestions:
            opts = ", ".join(f'<a href="/_search?q={quote(s)}">{html.escape(s)}</a>'
                             for s in suggestions)
            out.append(f"<p>Did you mean: {opts}?</p>")
    return "".join(out)


# ---------------------------------------------------------------------------
# HTTP server
# ---------------------------------------------------------------------------

class Handler(BaseHTTPRequestHandler):
    server_version = "zdoom-docs-browse"

    def _send(self, status, body, ctype="text/html; charset=utf-8", extra=None):
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(data)

    def _not_found(self):
        self._send(404, "<!doctype html><title>404</title><h1>404 Not Found</h1>")

    def do_GET(self):
        parts = urlsplit(self.path)
        link = Linker()
        if parts.path == "/_search":
            q = parse_qs(parts.query).get("q", [""])[0]
            return self._send(200, page(f"Search: {q}", search_body(q, link), "", link, q=q))
        status, kind, rel, path = route(parts.path)
        try:
            if status == 404:
                return self._not_found()
            if kind == "redirect":
                return self._send(301, "", extra={"Location": parts.path + "/"})
            if kind == "text":
                return self._send(200, read_text(path), "text/plain; charset=utf-8")
            if kind == "listing":
                return self._send(200, page(rel or "root", listing_body(rel, path), rel, link))
            text = read_text(path)
            body = hide_agent_note(rel, render_md(text))
            self._send(200, page(page_title(text, rel), body, rel, link))
        except (OSError, UnicodeDecodeError):
            self._not_found()

    do_HEAD = do_GET


def serve(port, open_browser):
    try:
        httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    except OSError as e:
        if e.errno != errno.EADDRINUSE:
            raise
        sys.exit(f"browse.py: port {port} is already in use (another browse.py still running?). "
                 f"Stop it, or pass --port {port + 1}.")
    url = f"http://127.0.0.1:{port}/"
    mode = "rendered" if markdown_available() else f"plain-text; for rendering: {INSTALL_HINT}"
    print(f"Serving {ROOT} at {url} [{mode}]. Ctrl+C to stop.", flush=True)
    if open_browser:
        webbrowser.open(url)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


# ---------------------------------------------------------------------------
# --check
# ---------------------------------------------------------------------------

DENY_CASES = [
    "/maintainer/TODO.md", "/MAINTAINER/todo.md", "/maintainer/", "/sources.local.md",
    "/Sources.Local.md", "/../../etc/passwd", "/%2e%2e/", "/%2e%2e/%2e%2e/etc/passwd",
    "/..%5c..%5cx", "/acs%5c..%5c..%5cx", "/C:/x", "/c:%5cwindows", "/.git/config",
    "/.venv/", "/tools/lookup.py", "/tools/__pycache__/", "/acs/INDEX.md%00.txt",
]
ALLOW_CASES = ["/", "/INDEX.md", "/acs/INDEX.md", "/LICENSE", "/acs/concepts/", "/shared/concepts/"]


def _ids_for(rel, cache):
    if rel not in cache:
        cache[rel] = set(ID_RE.findall(render_md(read_text(ROOT / rel))))
    return cache[rel]


def check():
    failures = 0
    for u in DENY_CASES:
        if route(u)[0] != 404:
            print(f"DENY FAIL: {u} -> {route(u)[:3]}")
            failures += 1
    for u in ALLOW_CASES:
        if route(u)[0] != 200:
            print(f"ALLOW FAIL: {u} -> {route(u)[:3]}")
            failures += 1
    print(f"access control: {len(DENY_CASES)} deny + {len(ALLOW_CASES)} allow cases, "
          f"{failures} failed")

    rendered = markdown_available()
    if not rendered:
        print("markdown-it-py not installed: link targets only, no #anchors, and example links "
              f"inside multi-line code are over-reported ({INSTALL_HINT})")
    ids, broken, n_links, n_files = {}, [], 0, 0
    for rel in walk_public_md():
        n_files += 1
        body = render_md(read_text(ROOT / rel))
        if rendered:
            ids[rel] = set(ID_RE.findall(body))
        for _, href in HREF_RE.findall(body):
            href = html.unescape(href)
            if not href or SCHEME_RE.match(href) or href.startswith("//"):
                continue
            n_links += 1
            path_part, _, frag = href.partition("#")
            if path_part:
                joined = posixpath.normpath(posixpath.join(posixpath.dirname(rel), unquote(path_part)))
                if joined.startswith(".."):
                    broken.append((rel, href, "escapes the repo root"))
                    continue
                url = "/" + ("" if joined == "." else joined) + ("/" if path_part.endswith("/") else "")
                status, kind, trel, _ = route(url)
                if status == 301:
                    status, kind, trel, _ = route(url + "/")
                if status != 200:
                    broken.append((rel, href, "target not servable"))
                    continue
            else:
                kind, trel = "md", rel
            if frag and rendered:
                if kind != "md":
                    broken.append((rel, href, f"anchor on a non-markdown target ({kind})"))
                elif unquote(frag) not in _ids_for(trel, ids):
                    broken.append((rel, href, "anchor not found"))
    for rel, href, why in broken:
        print(f"BROKEN: {rel}: {href} ({why})")
    print(f"links: {n_links} relative links in {n_files} files, {len(broken)} broken")
    return 1 if failures or broken else 0


# ---------------------------------------------------------------------------
# --build
# ---------------------------------------------------------------------------

def _static_href(href, page_rel):
    if not href or SCHEME_RE.match(href) or href.startswith("//") or href.startswith("#"):
        return href
    path_part, sep, frag = href.partition("#")
    target = posixpath.normpath(posixpath.join(posixpath.dirname(page_rel), unquote(path_part)))
    if path_part.endswith("/") or (ROOT / target).is_dir():
        new = path_part.rstrip("/") + "/INDEX.html"
    elif path_part.lower().endswith(".md"):
        new = path_part[:-3] + ".html"
    else:
        new = path_part
    return new + sep + frag


def build(out_dir):
    if not markdown_available():
        print(f"--build needs markdown-it-py: {INSTALL_HINT}", file=sys.stderr)
        return 2
    out = Path(out_dir).resolve()
    if out == ROOT or ROOT in out.parents:
        print(f"refusing to build inside the repo: {out}", file=sys.stderr)
        return 2
    try:
        res = subprocess.run(["git", "ls-files", "-z", "--", "*.md", "LICENSE", "licenses/"],
                             cwd=ROOT, capture_output=True, check=True)
    except FileNotFoundError:
        print("--build needs git on PATH (it exports only tracked files)", file=sys.stderr)
        return 2
    except subprocess.CalledProcessError as e:
        print(f"git ls-files failed: {e.stderr.decode(errors='replace')}", file=sys.stderr)
        return 2
    files = [f for f in res.stdout.decode("utf-8").split("\0") if f and is_public(f)]
    dirs_with_md = set()
    for rel in files:
        src = ROOT / rel
        if not src.is_file():
            continue
        if rel.lower().endswith(".md"):
            link = Linker(rel, static=True)
            text = read_text(src)
            body = HREF_RE.sub(lambda m: f'href="{_static_href(html.unescape(m.group(2)), rel)}"',
                               hide_agent_note(rel, render_md(text)))
            dst = out / (rel[:-3] + ".html")
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(page(page_title(text, rel), body, rel, link, search=False),
                           encoding="utf-8")
            dirs_with_md.add(posixpath.dirname(rel))
        else:
            dst = out / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)
    # Every sidebar dir and bare dir link needs an INDEX.html; generate listings where missing.
    for d in sorted(dirs_with_md | {S.SHARED_CONCEPTS_DIR}):
        dst = out / d / "INDEX.html"
        if dst.exists():
            continue
        names = sorted(posixpath.basename(f)[:-3] for f in files
                       if f.lower().endswith(".md") and posixpath.dirname(f) == d)
        items = "".join(f'<li><a href="{quote(n)}.html">{html.escape(n)}.md</a></li>'
                        for n in names)
        rel = posixpath.join(d, "INDEX.html") if d else "INDEX.html"
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(page(d or "root", f"<h1>{html.escape(d)}/</h1><ul>{items}</ul>", rel,
                            Linker(rel, static=True), search=False), encoding="utf-8")
    print(f"exported {len(files)} files to {out} (open {out / 'INDEX.html'})")
    return 0


def main():
    ap = argparse.ArgumentParser(prog="browse.py", description=__doc__.split("\n")[0])
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--open", action="store_true", help="open the default browser")
    ap.add_argument("--check", action="store_true", help="self-test access control and links")
    ap.add_argument("--build", metavar="DIR", help="static HTML export to DIR (outside the repo)")
    args = ap.parse_args()
    if args.check:
        sys.exit(check())
    if args.build:
        sys.exit(build(args.build))
    serve(args.port, args.open)


if __name__ == "__main__":
    main()
