#!/usr/bin/env python3
"""Check the agents vault: broken wikilinks, missing headings, orphans, Up: lines, style.

Usage: check_links.py [VAULT]   (default ~/Vault/agents). Exit 1 when problems exist.
Templates/ is skipped (its links are placeholders).
"""

import os
import re
import sys

LINK = re.compile(r"\[\[([^\]|#]*)(?:#([^\]|]*))?(?:\|[^\]]*)?\]\]")
CODE = re.compile(r"```[\s\S]*?```|`[^`\n]*`")


def slug(text):
    return re.sub(r"\s+", " ", text.strip()).lower()


def main():
    root = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else "~/Vault/agents")
    notes = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not d.startswith(".") and d != "Templates"]
        for name in filenames:
            if name.endswith(".md"):
                notes.setdefault(name[:-3], []).append(os.path.join(dirpath, name))
    problems = []
    for name, paths in notes.items():
        if len(paths) > 1:
            problems.append(f"duplicate note name '{name}': {', '.join(os.path.relpath(p, root) for p in paths)}")
    headings = {}
    texts = {}
    for name, paths in notes.items():
        with open(paths[0], encoding="utf-8") as handle:
            text = handle.read()
        texts[name] = text
        headings[name] = {slug(h) for h in re.findall(r"^#{1,6}\s+(.+)$", text, re.M)}
    incoming = {name: set() for name in notes}
    for name, text in texts.items():
        rel = os.path.relpath(notes[name][0], root)
        body = CODE.sub("", text)
        for target, section in LINK.findall(body):
            target = target.strip() or name
            if target not in notes:
                problems.append(f"{rel}: broken link [[{target}]]")
                continue
            if target != name:
                incoming[target].add(name)
            if section and slug(section) not in headings[target]:
                problems.append(f"{rel}: missing heading [[{target}#{section}]]")
        if name != "Home" and not re.search(r"^Up:\s*\[\[", text, re.M):
            problems.append(f"{rel}: no 'Up:' line")
        if "—" in text:
            problems.append(f"{rel}: contains an em dash")
        if re.search(r"^\s*>", CODE.sub("", text), re.M):
            problems.append(f"{rel}: contains a blockquote line")
    for name, sources in incoming.items():
        if name != "Home" and not sources:
            problems.append(f"{os.path.relpath(notes[name][0], root)}: orphan (no incoming links)")
    for line in sorted(problems):
        print(line)
    print(f"{len(notes)} notes, {len(problems)} problems")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
