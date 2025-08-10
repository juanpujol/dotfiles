# Agent Guidelines for .dotfiles Repository

## Build/Test/Lint Commands
- **Raycast Extensions**: `npm run lint`, `npm run fix-lint`, `npm run build`, `npm run dev`
- **Neovim**: Use stylua for Lua formatting (config in `nvim/stylua.toml`)
- **No global test suite** - this is a dotfiles repository with individual tool configurations

## Code Style Guidelines
- **Lua (Neovim)**: 2 spaces, 120 column width (stylua.toml)
- **JavaScript/TypeScript**: Prettier with 110 print width, prose wrap always (.prettierrc)
- **Shell Scripts**: Follow existing zsh/bash patterns in dotfiles
- **JSON**: 2-space indentation for consistency

## Repository Structure
- `nvim/` - Neovim configuration with LazyVim
- `raycast/extensions/` - Raycast extension packages
- `oh-my-zsh/` - Oh My Zsh framework and plugins
- `tmux/` - Tmux configuration and plugins
- Root config files: `zshrc`, `tmux.conf`, `gitconfig`, `Brewfile`, etc.

## Development Notes
- This is a personal dotfiles repository - avoid breaking existing configurations
- Test changes in isolated environments before modifying core configs
- Raycast extensions have individual package.json files with their own scripts
- Use existing tools: bat, eza, fzf, lazygit, gh, nvim