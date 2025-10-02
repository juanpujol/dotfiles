# Dotfiles Recommendations

## Git Enhancements

- Add GPG signing: `[commit] gpgsign = true` and `[user] signingkey = YOUR_KEY_ID` in gitconfig for secure commits.
- ✅ Add global .gitignore: Created `~/gitignore_global` with common ignores (e.g., .DS_Store, node_modules) and set `core.excludesfile = ~/gitignore_global`.
- Add git aliases: `[alias] co = checkout`, `st = status`, `lg = log --oneline --graph --decorate`.

## Zsh Improvements

- Organize zshrc: Move aliases and paths to separate files (e.g., `~/.zsh/aliases.zsh`, `~/.zsh/paths.zsh`) and source them.
- Add history settings: `HISTSIZE=10000`, `SAVEHIST=10000`, `setopt hist_ignore_dups`, `setopt share_history`.
- Add more completions: Install `zsh-completions` plugin and enable for tools like docker, kubectl.
- Add safety aliases: `alias rm='rm -i'`, `alias cp='cp -i'`, `alias mv='mv -i'`.

## Tmux Additions

- Add more plugins: `tmux-yank` for clipboard integration, `tmux-open` for opening files/URLs.
- Customize status bar: Add battery, CPU, or weather modules via scripts.
- Add session management: Bindings for renaming sessions, killing panes.

## Neovim (LazyVim)

- Review plugins: Ensure essentials like telescope, treesitter, lsp-config are active; add nvim-tree or neo-tree if needed.
- Add custom keymaps: In `config/keymaps.lua`, add shortcuts for common actions (e.g., `<leader>ff` for find files).
- Enable auto-save or format on save for better workflow.

## Tools to Add (Brewfile)

- `jq` for JSON processing.
- `htop` or `btop` (already have btop, good).
- `tree` or enhance eza usage.
- `thefuck` for command correction.
- `tldr` (already have tlrc, similar).
- `direnv` (already sourced, good).

## Starship Enhancements

- Add battery module: `[battery] disabled = false` for laptops.
- Add command duration: `[cmd_duration] disabled = false`.
- Customize more symbols or add hostname for remote sessions.

## General

- Add global scripts: Create `~/.local/bin/` for custom scripts (e.g., backup, update tools).
- Security: Add `umask 022` in zshrc; consider keychain for SSH/GPG.
- Backup/sync: Use chezmoi or stow for better dotfile management across machines.
- Test configs: Run `zsh -c 'source ~/.zshrc'` to check for errors; lint tmux.conf with `tmux source ~/.tmux.conf`.
