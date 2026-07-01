# Dotfiles Improvement Backlog

Date: 2026-07-01

This is a deferred cleanup/improvement list from the dotfiles audit. The repo now lives at `~/dotfiles`, with `~/.dotfiles` kept as a compatibility symlink.

## High Impact

1. Add a root `README.md` or bootstrap guide.
   - Document fresh-machine setup: clone location, symlink creation, `brew bundle`, `mise install`, TPM install, Herdr plugin linking, and verification commands.
   - Include the compatibility note for `~/.dotfiles -> ~/dotfiles`.

2. Add a small bootstrap/check script.
   - Check required parent dirs exist.
   - Create/update symlinks idempotently.
   - Print warnings for missing optional targets instead of failing hard.
   - Avoid destructive behavior unless explicitly confirmed.

3. Clean up `zshrc` structure.
   - Split paths, aliases, completions, and tool init into smaller sourced files.
   - Remove duplicate setup, especially repeated `PNPM_HOME` handling and the duplicated mise executable check.
   - Keep `xterm-kitty` compatibility unless there is a confirmed reason to remove it.

4. Align `Brewfile` with actual config dependencies.
   - Add tools referenced by configs/scripts but missing from `Brewfile`, such as `jq`, `coreutils`, `chafa`, and `supabase/tap/supabase` if still used.
   - Review whether old Python/OpenSSL versions are still needed.
   - Consider trimming the large VS Code extension list if it is just a generated snapshot.

## Medium Impact

1. Replace the stock LazyVim `nvim/README.md`.
   - Document the actual Neovim setup, important plugins, custom keymaps, known issues, and recovery steps.

2. Remove or archive disabled Neovim experiments.
   - `nvim/lua/plugins/example.lua` is still the starter example.
   - `nvim/lua/plugins/antfu-eslint.lua` is disabled with `if true then return {} end`.
   - Decide whether to delete them or move useful notes into docs.

3. Remove tracked local artifacts.
   - `vim/.netrwhist` contains local path history and should probably be untracked/ignored.
   - `nvim/lua/plugins/lsp.lua.bak` and `zellij/config.kdl.bak` look like backup files rather than source config.

4. Improve macOS portability in tmux popups.
   - `xargs -r` is GNU-specific and can fail on default macOS `xargs`.
   - Replace with a portable pattern or explicitly depend on GNU findutils/coreutils if preferred.

5. Make machine-specific paths intentional.
   - `gitconfig` still has absolute `/Users/juan/...` paths for signing and allowed signers.
   - This is fine for one Mac, but should be documented or templated if portability matters.

## Lower Impact

1. Add lightweight validation commands.
   - `zsh -i -c 'exit'`
   - `tmux -f ~/.tmux.conf start-server \; source-file ~/.tmux.conf \; kill-server`
   - `nvim --headless '+qa'`
   - `git -C ~/dotfiles status --short`

2. Keep `symlinks.md` current.
   - Treat it as the source of truth for live links.
   - Update it whenever new config directories are added or removed.

3. Consider a repo hygiene pass.
   - Remove `.DS_Store` files from the working tree.
   - Confirm ignored generated directories like `raycast/extensions/` and `tmux/plugins/` are intentionally local-only.

## Completed During Rename Cleanup

1. Renamed the repo from `~/.dotfiles` to `~/dotfiles`.
2. Kept `~/.dotfiles -> ~/dotfiles` as a compatibility symlink.
3. Retargeted live config symlinks to `~/dotfiles`.
4. Removed stale Kitty and AeroSpace symlinks.
5. Uninstalled the unused Kitty cask.
6. Updated tracked references and `symlinks.md` for the new canonical path.
