# Symlinks and References Map

This document maps all places that would need to be updated if renaming `.dotfiles` to `dotfiles`.

## Symlinks (15 total)

All these symlinks point to `/Users/juan/.dotfiles` and would need to be recreated:

1. `~/.config/nvim` → `/Users/juan/.dotfiles/nvim`
2. `~/.config/lazygit` → `/Users/juan/.dotfiles/lazygit`
3. `~/.config/starship.toml` → `/Users/juan/.dotfiles/starship.toml`
4. `~/.config/raycast` → `/Users/juan/.dotfiles/raycast`
5. `~/.config/zellij` → `/Users/juan/.dotfiles/zellij`
6. `~/.config/kitty` → `/Users/juan/.dotfiles/kitty`
7. `~/.config/ghostty` → `/Users/juan/.dotfiles/ghostty`
8. `~/.opencommit` → `/Users/juan/.dotfiles/opencommit`
9. `~/.vim` → `/Users/juan/.dotfiles/vim`
10. `~/.tmux.conf` → `/Users/juan/.dotfiles/tmux.conf`
11. `~/.zshrc` → `/Users/juan/.dotfiles/zshrc`
12. `~/.aerospace.toml` → `/Users/juan/.dotfiles/aerospace.toml`
13. `~/.tmux` → `/Users/juan/.dotfiles/tmux`
14. `~/.oh-my-zsh` → `/Users/juan/.dotfiles/oh-my-zsh`
15. `~/.gitconfig` → `/Users/juan/.dotfiles/gitconfig`

## Files Containing `.dotfiles` References

These files contain the string `.dotfiles` but are mostly in submodules/documentation:

1. `/Users/juan/.dotfiles/tmux.conf` - May contain self-references
2. `/Users/juan/.dotfiles/AGENTS.md` - Documentation
3. `/Users/juan/.dotfiles/oh-my-zsh/README.md` - Submodule documentation
4. `/Users/juan/.dotfiles/oh-my-zsh/plugins/shell-proxy/README.md` - Submodule
5. `/Users/juan/.dotfiles/oh-my-zsh/plugins/rake-fast/README.md` - Submodule
6. `/Users/juan/.dotfiles/oh-my-zsh/plugins/mix-fast/README.md` - Submodule

## Shell Configuration

No direct `.dotfiles` references found in:
- `~/.zshrc` (symlinked, so no hardcoded paths)
- `~/.zprofile`
- `~/.bashrc`
- `~/.bash_profile`

## Steps to Rename

1. **Backup current setup**: `cp -r ~/.dotfiles ~/dotfiles-backup`
2. **Rename directory**: `mv ~/.dotfiles ~/dotfiles`
3. **Remove all 14 symlinks**: `rm ~/.config/nvim ~/.config/lazygit ...` (list above)
4. **Recreate symlinks** with new path: `ln -s ~/dotfiles/nvim ~/.config/nvim` (etc)
5. **Update git remote** if needed
6. **Test all configurations** (nvim, tmux, zsh, etc)

## Notes

- No shell aliases reference `.dotfiles` directly
- Most configurations use symlinks, so they automatically point to the right place once recreated
- The oh-my-zsh submodule references are internal and won't affect the rename
- Git repository will remain intact during the rename