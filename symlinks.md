# Symlinks and References Map

This document maps the live symlinks for the canonical `~/dotfiles` checkout.

## Compatibility

`~/.dotfiles` is kept as a compatibility symlink to `~/dotfiles`. This lets old generated files, caches, shell history, or external app references keep working while the canonical path is `~/dotfiles`.

## Symlinks

These symlinks should point to `/Users/juan/dotfiles`:

1. `~/.config/nvim` -> `/Users/juan/dotfiles/nvim`
2. `~/.config/lazygit` -> `/Users/juan/dotfiles/lazygit`
3. `~/.config/starship.toml` -> `/Users/juan/dotfiles/starship.toml`
4. `~/.config/herdr/config.toml` -> `/Users/juan/dotfiles/herdr/config.toml` (file-only symlink; the dir stays real so herdr logs/sockets do not enter the repo)
5. `~/.config/raycast` -> `/Users/juan/dotfiles/raycast`
6. `~/.config/zellij` -> `/Users/juan/dotfiles/zellij`
7. `~/.config/ghostty` -> `/Users/juan/dotfiles/ghostty`
8. `~/.vim` -> `/Users/juan/dotfiles/vim`
9. `~/.tmux.conf` -> `/Users/juan/dotfiles/tmux.conf`
10. `~/.zshrc` -> `/Users/juan/dotfiles/zshrc`
11. `~/.tmux` -> `/Users/juan/dotfiles/tmux`
12. `~/.oh-my-zsh` -> `/Users/juan/dotfiles/oh-my-zsh`
13. `~/.gitconfig` -> `/Users/juan/dotfiles/gitconfig`
14. `~/.gnhf/config.yml` -> `/Users/juan/dotfiles/gnhf/config.yml` (file-only symlink; the dir stays real so gnhf runs/logs do not enter the repo)
15. `~/.config/opencode/opencode.jsonc` -> `/Users/juan/dotfiles/opencode/opencode.jsonc` (OpenCode V2 config)
16. `~/.config/opencode/cli.json` -> `/Users/juan/dotfiles/opencode/cli.json` (OpenCode V2 CLI/TUI config)
17. `~/.config/opencode/plugins/tab-management/tui.ts` -> `/Users/juan/dotfiles/opencode/plugins/tab-management/tui.ts` (session-tab shortcuts)
18. `~/.config/opencode/plugins/session-shortcuts/tui.ts` -> `/Users/juan/dotfiles/opencode/plugins/session-shortcuts/tui.ts` (Ctrl+G session-picker scope toggle)
19. `~/.pi/agent/settings.json` -> `/Users/juan/dotfiles/pi/settings.json` (pi; file-only links, the dir stays real so auth, trust, sessions and the managed install do not enter the repo)
20. `~/.pi/agent/keybindings.json` -> `/Users/juan/dotfiles/pi/keybindings.json`
21. `~/.pi/agent/mcp.json` -> `/Users/juan/dotfiles/pi/mcp.json` (user-level MCP servers)
22. `~/.pi/agent/prompts` -> `/Users/juan/dotfiles/pi/prompts`
23. `~/.pi/agent/extensions/herdr-agent-state.ts` -> `/Users/juan/dotfiles/pi/extensions/herdr-agent-state.ts`
24. `~/.agents` -> `/Users/juan/dotfiles/agents` (canonical global skills and installer lock file)

## Global agent skills

All user-installed global skills live in `agents/skills/`. See `agents/README.md` for setup and maintenance.

Existing skill entries under Claude, Codex, Cursor, Windsurf (both legacy and current paths), Cline, OpenCode (both paths), and Crush are symlinks to `~/.agents/skills/<name>`. Their parent directories remain real; Codex's `.system` and app-managed runtime directories stay outside dotfiles.

Pi and OMP discover `~/.agents/skills` directly. Do not also install or link these skills under `~/.pi/agent/skills`, `~/.omp/agent/skills`, or `~/.local/share/omp/skills`: redundant discovery paths can produce skill-name collisions.

The consolidation backup is `~/.local/share/dotfiles-backups/agent-skills-20261010-222538/`. It preserves all original directories, including older differing Windsurf/OpenCode copies. Existing `~/.agents` skills took precedence; otherwise the current Claude bundle was used. Built-in skills, plugin caches, and vendor imports were not migrated.

## Pi session configuration

`pi/settings.json` is the source of truth for new Pi instances: `openai-codex/gpt-6.1-sol`, `medium` thinking, the dark theme, and `@llblab/pi-codex-usage@0.13.0`. `zshrc` sets `PI_CODING_AGENT_DIR="$HOME/.pi/agent"`, whose settings file is linked into this repository. The Herdr extension symlink is retained but disabled in settings to match the preserved session's extension setup.

The original session directory at `~/.local/share/omp` is preserved unchanged. This is legacy storage, not an OMP installation; running sessions using it do not need to restart. Credentials, caches, trust, and sessions stay outside git. Existing sessions in the legacy directory can still be opened with `pi --session /absolute/path/to/session.jsonl`.

The conflicting default configuration was backed up to `~/.local/share/dotfiles-backups/pi-session-config-20261011-183923/` before migration.

## Saved Pi permission configuration (inactive)

Permission packages are not enabled in `pi/settings.json`, matching the preserved session's no-per-command-approval behavior. Their configuration is retained in `pi/extensions/` for reference; do not reinstall these packages unless you want permission gates again. Link only the config files, not the extension directories, so review logs stay outside git:

```sh
for extension in pi-permission-system pi-permission-classifier; do
  mkdir -p "$HOME/.pi/agent/extensions/$extension"
  ln -s "$HOME/dotfiles/pi/extensions/$extension/config.json" \
    "$HOME/.pi/agent/extensions/$extension/config.json"
done
```

Run this on each machine after linking `pi/settings.json`. Existing destination files must be reviewed and moved aside before creating the links. Restart Pi after setup. Use the default Pi agent directory; a custom `PI_CODING_AGENT_DIR` changes where Pi looks for these links.

If re-enabled, the classifier must load before the permission system. The saved policy enables it through `authorizerChain`, uses the session model with a 15-second timeout, and keeps YOLO off. These rules, including sensitive-path blocks, are not enforced while the permission packages are inactive.

## Outbound shortcuts

These point *out* of the repo. They are convenience shortcuts, not config links, and they are gitignored rather than tracked, so recreate them by hand on a new machine.

1. `obsidian` -> `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/JP` (Obsidian vault "JP", synced via iCloud)

## Migration Notes

The repository used to live at `~/.dotfiles`. The canonical path is now `~/dotfiles`, with `~/.dotfiles` retained as a compatibility symlink.
