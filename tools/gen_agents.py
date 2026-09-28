#!/usr/bin/env python3
"""Generate the per-harness subagent adapters from the harness-neutral procedure docs.

Each canonical doc under agents/procedures/<name>.md is plain markdown. Its `## When to delegate`
section (one paragraph) becomes every adapter's description; everything after that section
becomes the adapter's body / system prompt. Everything before it (H1 plus the note for humans) is
dropped. HARNESSES below holds each harness's output path and frontmatter/TOML template.

Formats were checked against each harness's own docs on 2026-09-25/26:
  - Claude Code  .claude/agents/*.md          frontmatter name/description/tools(/model)
  - Codex CLI    .codex/agents/*.toml         name, description, developer_instructions
  - Gemini CLI   .gemini/agents/*.md          frontmatter name/description/kind/tools list
  - OpenCode     .opencode/agents/*.md        frontmatter description/mode/permission; name = filename
  - Copilot      .github/agents/*.agent.md    frontmatter name/description/tools aliases
Loader behavior (symlinks, read-only enforcement) was checked against Codex, gemini-cli and
opencode source on 2026-09-26; the root AGENTS.md "Subagents" table records the consequences.

agents/<name>.md (the Claude Code adapter) keeps its historical path, since machines symlink
~/.claude/agents/ straight to it.

Usage:
    python3 tools/gen_agents.py            # write every adapter
    python3 tools/gen_agents.py --check    # exit 1 if any committed adapter differs
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sections as S  # noqa: E402

ROOT = S.ROOT
PROCEDURES_DIR = "agents/procedures"
DELEGATE_HEADING = "## When to delegate"

# Only Claude pins a model, carried over from the pre-generator adapter; model IDs don't port.
CLAUDE_MODELS = {"zdoom-docs-lookup": "haiku"}


def _note(name, comment):
    src = f"{PROCEDURES_DIR}/{name}.md"
    text = f"Generated from {src} by tools/gen_agents.py. Edit that file instead, then rerun the script."
    return f"# {text}" if comment == "toml" else f"<!-- {text} -->"


def _md(frontmatter_lines, name, body):
    return "---\n" + "\n".join(frontmatter_lines) + "\n---\n\n" + _note(name, "md") + "\n\n" + body


def _claude(name, desc, body):
    fm = [f"name: {name}", f"description: {desc}", "tools: Read, Grep, Glob"]
    if name in CLAUDE_MODELS:
        fm.append(f"model: {CLAUDE_MODELS[name]}")
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
    ("claude", "agents/{name}.md", _claude),
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


def render_all(root=ROOT):
    rendered = {}
    for src in sorted((root / PROCEDURES_DIR).glob("*.md")):
        rendered.update(render(src.stem, src.read_text()))
    return rendered


def check(root=ROOT):
    """Return a list of drift/error messages for the whole tree; empty means clean."""
    try:
        rendered = render_all(root)
        actual = {rel: (root / rel).read_text() if (root / rel).is_file() else None for rel in rendered}
        return drift(rendered, actual)
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
