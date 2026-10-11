# Global agent skills

`~/dotfiles/agents/skills/<name>/SKILL.md` is the canonical home for user-installed global skills. Keep supporting scripts, references, and assets in the same skill directory. `agents/.skill-lock.json` preserves the shared installer metadata.

## Setup

On a new machine:

```sh
ln -s "$HOME/dotfiles/agents" "$HOME/.agents"
```

If `~/.agents` already exists, review and back it up outside any skills discovery directory first. Do not overwrite it blindly.

Pi and OMP discover `~/.agents/skills` directly. Leave their native skill directories free of duplicate copies or links.

For tools that need a tool-specific entry, link the individual skill rather than copying it. For example:

```sh
mkdir -p "$HOME/.claude/skills"
ln -s "$HOME/.agents/skills/tsk-cli" "$HOME/.claude/skills/tsk-cli"
```

Only add tool-specific links when needed. Keep tool-managed built-ins and runtime state outside this repository; in particular, do not replace the entire `~/.codex/skills` directory because it contains `.system`.

## Maintenance

- Add or edit skills in `agents/skills`, not in separate tool directories.
- Configure installers to use `~/.agents/skills`; avoid installing additional copies in Pi/OMP native skill directories.
- Review installer changes and supporting files before committing them.
- Restart the agent or use its reload command after changing skills.

See `../symlinks.md` for the live paths and the original-directory backup location.
