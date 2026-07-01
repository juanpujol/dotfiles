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

## Migration Notes

The repository used to live at `~/.dotfiles`. The canonical path is now `~/dotfiles`, with `~/.dotfiles` retained as a compatibility symlink.
