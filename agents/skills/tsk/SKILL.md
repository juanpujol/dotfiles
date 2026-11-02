---
name: tsk
description: Manage delivery of an issue or project through the shared tsk task board. Use for /tsk, ongoing task ownership, multi-agent progress logs and handoffs, closing verified work, or reconciling issue/PR checklists. Complements tsk-cli's command reference; does not itself authorize starting agents or publishing changes.
---

# tsk: shared delivery tracker

Use tsk as the shared plan, ownership record, progress log, and handoff surface for the work the user assigns. Keep it current as work happens; another agent must be able to continue from the board without this chat. New work goes on the same board before it begins.

## Establish scope

- Read [tsk-cli](../tsk-cli/SKILL.md) for command/status mechanics. Installed `tsk --help` and `tsk help <command>` are the syntax authority. Use CLI JSON for agent reads and CLI mutations for updates; do not edit the store directly or use a separate `--state-dir`.
- Collection JSON omits notes and steps. Use `tsk list T12 --json` to read a task's full brief/log before claiming, editing, or handing it off.
- Use the exact checkout/project and an issue thread such as `i863`; do not mix sibling worktrees, unrelated projects, or desk tasks. Use the absolute project path when creating a new destination. Inspect existing live and done tasks before adding duplicates.
- Read the current issue/spec and repository instructions. Capture the issue URL, worktree, branch, and relevant PR URL in task notes. Track the user's actual scope, including later corrections; do not replace it with an older recommendation.
- If asked to open the board in Herdr, use the [herdr skill](../herdr/SKILL.md). Verify `HERDR_ENV=1`, resolve the caller's workspace, reuse its matching `tsk` tab or create one with the same cwd, and run bare `tsk` in its shell pane. This user-requested TUI is the human view; agent task operations remain CLI-based. Do not start a duplicate TUI or seize a pane running another process. Preserve focus unless asked to switch.

## Build and maintain the plan

- Split work into independently finishable outcomes. Include implementation, necessary security/compatibility work, meaningful validation, and final review/checklist reconciliation. Use steps when a task has useful substeps; avoid duplicate tracking of the same work.
- Make notes self-contained: intended result and boundaries, dependencies by task ID, relevant files/contracts, verification needed, owner, and a dated progress log. Link acceptance criteria to the tasks/evidence that satisfy them. Record completed work already proven in this conversation rather than inventing new work to reproduce it.
- Under delegated task management, creating tasks, adding new in-scope findings, logging progress, and maintaining notes are authorized routine work. Do not repeatedly ask approval for these updates. A broader product/scope change still needs the user's decision.
- Keep one authoritative mutable work plan in tsk. Issues/PRs remain the specification and delivery evidence; do not create competing private task lists for different agents.

### Write readable Markdown

Task notes must use Markdown formatted for the human reading tsk. Use short headings, blank lines between sections, and concise bullets with one point each. Use **bold labels** for metadata, inline code for paths/commands/task IDs, and descriptive issue/PR links. Keep titles short and plain.

Avoid dense paragraphs, semicolon-packed metadata, raw `Context: ...` dumps, and pipe-delimited logs. Do not wrap the entire note in a code fence; fences are for actual commands/code. Split verification and progress into scannable points. Preserve decisions, evidence, ownership, and history when improving formatting.

Suggested note shape; omit empty sections and adapt headings to the task:

```markdown
## Outcome

One short statement of the result.

## Scope

- Behavior or contract to change.
- Boundary to preserve.

## Verification

- Meaningful check and evidence required.

## Coordination

- **Issue:** [#123](https://github.com/owner/repo/issues/123)
- **Worktree:** `/absolute/checkout`
- **Branch / thread:** `issue-123`
- **Depends on:** `T12`, `T15`
- **Owner:** agent name and pane/session, or unassigned

## Progress log

**Timestamp — agent**

- What changed or was decided.
- Evidence, blocker, or next action.
```

## Coordinate through the board

- Before starting, reread the task, its dependencies, and current owner. Claim it in notes, set `started`, and verify the stored state. Do not take over another agent's active task without an agreed handoff.
- Log material decisions, completed increments, exact validation results, failures, blockers, changed files/commits, and the next action. Update before handing off, pausing, or finishing. Never log secrets.
- Use `ready` for work selected to run next; `blocked` with the actual unmet dependency or question; `review` when implementation awaits verification/review. Notes must identify what unblocks or closes it. Blocked work stays visible.
- The TUI groups `review` and `blocked` under **IT NEEDS YOU**. Name who must act. During delegated agent review, the managing agent promptly claims the handoff, sets `started`, and records the active reviewer; keep it `started` while that agent works. Do not leave ongoing agent work looking like a user request. Actual user review/decisions or blockers must identify the required action explicitly.
- Other agents use these same task IDs, notes, and statuses. Record the owner and explicit handoff instead of relying on transient chat or terminal output. This skill does not automatically spawn agents or send messages.
- `tsk edit --notes` replaces the whole note. Read the latest complete task, preserve existing decisions/log entries, append the update, then write and verify. Coordinate a single writer per active task; no claim of atomic locking or safe concurrent append. If another agent changed it, reconcile before continuing.
- Check command exit/refusal codes. After an indeterminate write, reread the board before retrying. Step toggles are not idempotent: inspect the current step value and ID before toggling, including retries.

## Finish truthfully

- When the user delegates closing tasks, the managing agent marks a task `done` once its outcome and required checks are verified. That delegation avoids asking the user to close every task. Without delegated closure, preserve tsk-cli's normal `review` handback.
- In a multi-agent flow, an implementing agent normally records evidence and sets `review`; the managing agent verifies and closes it. A task may close directly when that agent also has closure authority and the required review is satisfied. Never close because an agent merely says it is done, a command was launched, or time ran out.
- Tick task steps only after their result is proved. Log what passed and any relevant limits. Documentation/setup work uses appropriate lightweight verification; obey repository limits on tests, builds, hooks, and type-checking.
- Keep discovered defects/follow-ups visible as tasks. Do not archive, drop scope, mark blocked work done, or weaken validation merely to get an empty board. A deliberate scope change needs a recorded user decision.
- Before final handoff, inspect every live task in the issue thread, completed tasks, unresolved review findings, and the actual issue/PR acceptance boxes. Map each checked box to evidence, and update the authorized issue/PR checklists to match reality. Do not tick unproved work or a merge/deploy check that never happened.
- The intended finish is all agreed tasks done and all applicable issue/PR boxes checked. If anything remains incomplete, report that exact remainder; do not manufacture completion. Task closure/checklist updates do not grant permission to create or merge PRs, publish releases, or perform other external actions.

## Refine this skill

Canonical home: `~/dotfiles/agents/skills/tsk/SKILL.md`. Keep tool discovery entries as links to that source. Improve this skill as the user requests or delegates learning: record narrow changes supported by actual usage, preserve the workflow above, and validate the updated skill. Do not rewrite memories or unrelated skills/configuration as part of refinement.
