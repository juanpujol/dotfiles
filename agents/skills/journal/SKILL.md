---
name: journal
description: Consolidate one day of Juan's agent work across all projects (Claude Code, Codex, pi, OpenCode transcripts, memories, git, GitHub, tsk) into the agents vault at ~/Vault/agents, writing the journal day and updating work, project and "Working with agents" notes. Use when Juan says /journal, "journal today", "write the journal", or asks to backfill journal days. Invoked as `/journal [YYYY-MM-DD | YYYY-MM-DD..YYYY-MM-DD]`, default today.
---

# journal: daily consolidation pass into the agents vault

Vault: `~/Vault/agents` (git, Obsidian, plain Markdown). Start at `Home.md`; templates in `Templates/`.
This is a consolidation pass across all projects, not only a journal entry. One day per run; a range
`A..B` runs each day in order, one commit per day.

## Hard rules
- Never copy secrets, tokens, API keys, passwords, connection strings or cookies, even if the digest shows one.
- No em dashes. No markdown blockquotes (no line starting with `>`). English only (Portuguese only when quoting product UI).
- Always leave one blank line after every heading before its content.
- Write only inside `~/Vault/agents`. Never write to a repo: technical facts become proposed `docs/` additions in the work note.
- Idempotent: if the day already has entries anywhere, update them in place. Never add a second log line, cursing row, frustration bullet or index line for the same date.
- Project folder = repo name (main repo basename). Worktree `~/.herdr/worktrees/laiki2/i860` belongs to `laiki2`. The digest already resolves this.
- Records are long and complete: full story in order. Never squeeze a day into three lines. Other notes stay short and link to the day as evidence.

## 1. Gather
```sh
python3 ~/.agents/skills/journal/extract.py YYYY-MM-DD --out /tmp/journal-YYYY-MM-DD.md
```
- Read the Coverage header first: counts per source, per-project table, and "Problems while reading sources". Name missing or failed sources in the day's `Source note:`.
- Read the whole digest, in chunks (about 400 lines per read) when large. Do not skim past sessions.
- Roles: `Juan` is typed by Juan in Claude Code. `User` in Codex, pi and OpenCode is often an orchestrator brief sent through herdr; treat it as Juan's words only when it reads like him (typos, short, first person to the agent). `Event` lines are harness events.
- Collapsed "automated session batches" (evals, heartbeats) get one line each in the day.
- If a detail is unclear, open the raw transcript named by the session id; read only what you need.

## 2. Read the vault state
`Home.md`, `Journal/Journal.md`, the day note if it exists, `Projects/Projects.md`, each touched project's `<repo>.md`, `Working here.md` and `Work/` notes, and every note in `Working with agents/`. Find existing work notes by worktree, branch or issue (`grep -ril i860 ~/Vault/agents/Projects`).

## 3. Write the journal day
`Journal/YYYY/MM/YYYY-MM-DD.md` from `Templates/Journal day.md`. Use `Journal/2026/10/2026-10-18.md` as the depth reference.
- Title `# YYYY-MM-DD (Ddd)`; `Up: [[Journal]] · Work touched: [[...]]`; `Source note:` lists sources used and gaps (e.g. "written from extract.py digest: Claude, Codex, git, GitHub, tsk; pi and OpenCode had no sessions").
- Summary: 3 to 6 sentences on the whole day.
- One `## <repo>: [[work note]]` section per project (or per work note when a project has several). Inside:
  - "What Juan asked, and what happened, in order": numbered, each item starts with **Juan's ask in his words** (bold, quoted when short), then what agents did, what went wrong, the result.
  - Decisions (who, why). Agents (role: tool, model, pane or worktree). Evidence (commits with short sha, PRs, issues, files).
- Sessions with no meaningful user interaction (pure workers, automations, evals): one line each under the project.
- Learnings: each links to the note where it now lives, `[[Preferences#Ask versus act]]`.
- Frustrations: Juan's words edited for grammar and spelling, meaning kept, profanity removed; then trigger, resolution, and `Pattern: [[Frustrations#<pattern>]]`.
- `Cursing: N swears, N insults. See [[Cursing log]].` (0 and 0 is a valid line).
- Open threads: what is waiting, and on whom.

## 4. Work notes
`Projects/<repo>/Work/<id> <short name>.md`, one per worktree or issue, spanning many days (`<id>` = issue or worktree id, e.g. `i860`). Create from `Templates/Work note.md` when new.
- Status: current state, issue, PR, branch, agents and panes, tsk board.
- Log: one line for this day, `- [[YYYY-MM-DD]]: ...`, replaced (not duplicated) on rerun; keep lines in date order.
- Decisions with `([[YYYY-MM-DD]], who)`. Open threads current as of this day; remove ones that closed.
- "Technical learnings (candidates for repo docs/)": codebase facts with code paths and the proposed doc, e.g. "propose `docs/lessons/mcp-timeouts.md`". Never write them into the repo.

## 5. Project notes
- `Projects/<repo>/<repo>.md` from `Templates/Project.md` if new: what it is, repo, local path, worktrees; "Where the real docs are"; product rules Juan set (with `[[day]]`); `## Work` list of work notes with status.
- `Projects/<repo>/Working here.md`: how Juan wants agents to work in this repo (lessons, traps, commands), each with the day. Create if new, with purpose line, `Up: [[<repo>]]` and Related.
- Add new repos to `Projects/Projects.md`.

## 6. Working with agents
Update only with new evidence from this day; link the day on every addition.
- `Frustrations.md`: add the occurrence under its pattern (new `##` pattern if none fits), grammar-edited quote.
- `Cursing log.md`: one Totals row for the day and an `### [[YYYY-MM-DD]]` entry listing each raw swear or insult (exact words, raw, only here) with its trigger and pattern link. Count only Juan's own words, not quoted text or agent output. Swear = profanity (fuck, shit, wtf, af, damn, hell as a curse, Portuguese equivalents). Insult = aimed at the agent (stupid, idiot, useless, dumb).
- `Preferences.md`: new or sharpened rules Juan stated.
- `Orchestration.md`: roles, briefs, review loop lessons. `Tools.md`: tool setup and quirks (herdr, tsk, Claude Code, Codex, pi, OpenCode). `Models.md`: which model did which job, strengths and failures.

## 7. Indexes
- `Journal/Journal.md`: one line per day under `## YYYY` / `### Month`, `- [[YYYY-MM-DD]]: short themes`, in date order; replace the line on rerun.
- `Projects/Projects.md`: every repo folder listed with one line.

## 8. Links and check
- Every note: a one-line purpose under the title, an `Up:` link, and `Related:` links each with a reason in parentheses.
- Links both ways: the day links each work note and learning target; each work note's Log links the day; each Working-with-agents addition links the day.
- Note names are unique vault-wide (Obsidian resolves `[[name]]` by file name). Before creating a note, check that the name is free.
- Run the checker and fix everything it reports before committing:
```sh
python3 ~/.agents/skills/journal/check_links.py ~/Vault/agents
```
It reports broken links, missing `#heading` targets, orphans, notes without `Up:`, em dashes and blockquotes.

## 9. Commit
```sh
git -C ~/Vault/agents add -A && git -C ~/Vault/agents commit -m "journal: YYYY-MM-DD"
```
Vault commits are part of this skill; no extra approval needed. Never push (no remote yet unless Juan adds one).

## Report to Juan
Short: day written or updated, notes created and updated, cursing count, checker result, commit sha, and any source the digest could not read.
