#!/usr/bin/env python3
"""Generate the per-harness subagent adapters from the harness-neutral procedure docs.

Each canonical doc at the top level of agents/ (agents/<name>.md) is plain markdown. Its
`## When to delegate` section (one paragraph) becomes every adapter's description; everything
after that section becomes the adapter's body / system prompt. Everything before it (H1 plus the note for humans) is
dropped. HARNESSES below holds each harness's output path and frontmatter/TOML template.

Formats were checked against each harness's own docs on 2026-09-25/26:
  - Claude Code  .claude/agents/*.md          frontmatter name/description/tools
  - Codex CLI    .codex/agents/*.toml         name, description, developer_instructions
  - Gemini CLI   .gemini/agents/*.md          frontmatter name/description/kind/tools list
  - OpenCode     .opencode/agents/*.md        frontmatter description/mode/permission; name = filename
  - Copilot      .github/agents/*.agent.md    frontmatter name/description/tools aliases
Loader behavior (symlinks, read-only enforcement) was checked against Codex, gemini-cli and
opencode source on 2026-09-26; the root AGENTS.md "Subagents" table records the consequences.

Only procedures sit at the top level of agents/; each harness's adapters live in its own
agents/<harness>/ folder, and any other file under agents/ is reported as a stray by --check.
A symlink to the old Claude path agents/<name>.md must be re-pointed to agents/claude/<name>.md.

Usage:
    python3 tools/gen_agents.py            # write every adapter
    python3 tools/gen_agents.py --check    # exit 1 if any adapter differs or a stray file sits under agents/
"""
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sections as S  # noqa: E402

ROOT = S.ROOT
PROCEDURES_DIR = "agents"
DELEGATE_HEADING = "## When to delegate"

# No adapter pins a model, so every subagent inherits the caller's (decided 2026-09-29).


def _note(name, comment):
    src = f"{PROCEDURES_DIR}/{name}.md"
    text = f"Generated from {src} by tools/gen_agents.py. Edit that file instead, then rerun the script."
    return f"# {text}" if comment == "toml" else f"<!-- {text} -->"


def _md(frontmatter_lines, name, body):
    return "---\n" + "\n".join(frontmatter_lines) + "\n---\n\n" + _note(name, "md") + "\n\n" + body


def _claude(name, desc, body):
    fm = [f"name: {name}", f"description: {desc}", "tools: Read, Grep, Glob"]
    return _md(fm, name, body)


def _codex(name, desc, body):
    if "'''" in body:
        raise ValueError(f"{name}: body contains ''' and can't be a TOML literal string")
    # json.dumps output is a valid TOML basic string (same escapes, non-ASCII passed through).
    # No sandbox_mode: role files can't set it (Codex PR #39299), the parent's sandbox applies.
    return (_note(name, "toml") + "\n"
            + f"name = {json.dumps(name)}\n"
            + f"description = {json.dumps(desc, ensure_ascii=False)}\n"
            + "developer_instructions = '''\n" + body + "'''\n")


def _gemini(name, desc, body):
    # read_many_files passes name validation but isn't registered as a callable tool.
    tools = ["read_file", "list_directory", "glob", "grep_search"]
    fm = [f"name: {name}", f"description: {desc}", "kind: local", "tools:"]
    fm += [f"  - {t}" for t in tools]
    return _md(fm, name, body)


def _opencode(name, desc, body):
    # Agent defaults are allow-all (MCP tools included), so deny everything first; last match wins.
    fm = [f"description: {desc}", "mode: subagent", "permission:",
          '  "*": deny', "  read: allow", "  grep: allow", "  glob: allow", "  list: allow",
          "  external_directory: ask"]
    return _md(fm, name, body)


def _copilot(name, desc, body):
    fm = [f"name: {name}", f"description: {desc}", 'tools: ["read", "search"]']
    return _md(fm, name, body)


# (harness, output path template, renderer)
HARNESSES = [
    ("claude", "agents/claude/{name}.md", _claude),
    ("codex", "agents/codex/{name}.toml", _codex),
    ("gemini", "agents/gemini/{name}.md", _gemini),
    ("opencode", "agents/opencode/{name}.md", _opencode),
    ("copilot", "agents/copilot/{name}.agent.md", _copilot),
]


def split_canonical(name, text):
    """Return (description, body) from a canonical procedure doc."""
    m = re.search(r'^' + re.escape(DELEGATE_HEADING) + r'[ \t]*\n(.*?)(?=^## )', text, re.M | re.S)
    if not m:
        raise ValueError(f"{name}: no '{DELEGATE_HEADING}' section followed by another ## section")
    para = m.group(1).strip()
    if not para or "\n\n" in para:
        raise ValueError(f"{name}: '{DELEGATE_HEADING}' must be exactly one paragraph")
    desc = " ".join(line.strip() for line in para.splitlines())
    # Kept a plain YAML scalar in every markdown adapter, so refuse anything that would need quoting.
    if ": " in desc or " #" in desc or desc.endswith(":") or desc[0] in "!&*-?|>'\"%@`{[,#":
        raise ValueError(f"{name}: description would need YAML quoting; reword it")
    body = text[m.end():].strip("\n") + "\n"
    return desc, body


def render(name, canonical_text):
    """Pure: map each adapter's repo-relative path to its full generated text."""
    desc, body = split_canonical(name, canonical_text)
    return {tmpl.format(name=name): fn(name, desc, body) for _, tmpl, fn in HARNESSES}


def drift(rendered, actual):
    """Pure: one message per adapter whose `actual` text (None if absent) differs from `rendered`."""
    msgs = []
    for rel, text in sorted(rendered.items()):
        if actual.get(rel) is None:
            msgs.append(f"{rel} is missing; run tools/gen_agents.py")
        elif actual[rel] != text:
            msgs.append(f"{rel} differs from a fresh generation; edit {PROCEDURES_DIR}/ and rerun tools/gen_agents.py")
    return msgs


def strays(rendered, procedures, present):
    """Pure: one message per `present` path that is neither a procedure nor a rendered adapter."""
    known = set(rendered) | set(procedures)
    return [f"{rel} is neither a procedure nor a generated adapter; remove it, adapters are regenerated from {PROCEDURES_DIR}/<name>.md"
            for rel in sorted(present) if rel not in known]


def _agent_files(root):
    """Repo-relative files under agents/: git's tracked + untracked-unignored, else a plain walk."""
    try:
        out = subprocess.run(["git", "ls-files", "-co", "--exclude-standard", "-z", "--", PROCEDURES_DIR],
                             cwd=root, capture_output=True, check=True).stdout.decode()
        rels = [r for r in out.split("\0") if r and (root / r).is_file()]
    except (OSError, subprocess.CalledProcessError):
        rels = [p.relative_to(root).as_posix() for p in (root / PROCEDURES_DIR).rglob("*") if p.is_file()]
    # Editor/OS junk (.DS_Store, .swp, backup~) is never a procedure or an adapter.
    return sorted(r for r in rels if not r.rsplit("/", 1)[-1].startswith(".") and not r.endswith("~"))


def _procedures(root):
    return [root / r for r in _agent_files(root) if r.count("/") == 1 and r.endswith(".md")]


def render_all(root=ROOT):
    rendered = {}
    for src in _procedures(root):
        try:
            rendered.update(render(src.stem, src.read_text()))
        except ValueError as e:
            rel = src.relative_to(root).as_posix()
            raise ValueError(f"{rel}: {e} (only procedures belong at the top level of {PROCEDURES_DIR}/)") from e
    return rendered


def check(root=ROOT):
    """Return a list of drift/stray/error messages for the whole tree; empty means clean."""
    try:
        rendered = render_all(root)
        actual = {rel: (root / rel).read_text() if (root / rel).is_file() else None for rel in rendered}
        procedures = [p.relative_to(root).as_posix() for p in _procedures(root)]
        return drift(rendered, actual) + strays(rendered, procedures, _agent_files(root))
    except ValueError as e:
        return [str(e)]


def main():
    if "--check" in sys.argv[1:]:
        msgs = check()
        for msg in msgs:
            print(f"CHECK FAILED: {msg}", file=sys.stderr)
        if not msgs:
            print("gen_agents.py --check: clean", file=sys.stderr)
        sys.exit(1 if msgs else 0)
    for rel, text in render_all().items():
        path = ROOT / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        print(f"wrote {rel}", file=sys.stderr)


if __name__ == "__main__":
    main()
