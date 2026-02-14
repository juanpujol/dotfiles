# Noice.nvim Cmdline Crash Investigation

**Date:** 2026-01-09
**Issue:** Pressing `:` in Neovim closes/exits Neovim immediately
**Status:** INTERMITTENT - Fixed temporarily then broke again
**Related GitHub Issue:** https://github.com/folke/noice.nvim/issues/1184

## Environment

- **OS:** macOS Tahoe 26.01 (Darwin 25.2.0)
- **Neovim:** Started at 0.11.4, upgraded to 0.11.5 during debugging
- **Config:** LazyVim-based setup at `~/.dotfiles/nvim`

## Root Cause

**noice.nvim** is the culprit. Confirmed by:
1. `nvim --clean` works fine
2. Minimal config with just lazy.nvim works fine
3. LazyVim without noice.nvim works fine
4. LazyVim WITH noice.nvim crashes on `:`

The crash occurs during `CmdlineEnter` event - debug logging showed `CmdlineEnter` fired but `CmdlineLeave` never triggered.

## Everything We Tried

### 1. Plugin Configuration Changes

#### blink.lua
- Removed `opts.cmdline = nil` line (didn't fix)
- Tested with `opts.cmdline = { enabled = false }` (didn't fix)

#### noice.lua
- Changed `view = "cmdline_popup"` to `view = "cmdline"` (didn't fix)
- Set `cmdline = { enabled = false }` (fixed `:` but cmdline invisible)
- Set both `cmdline` and `messages` to `enabled = false` with `cmdheight = 1` (worked but ugly)
- Disabled noice entirely with `enabled = false` (worked)

### 2. File/Directory Operations

#### Backed up and removed custom configs:
```bash
mv ~/.dotfiles/nvim/lua/plugins ~/.dotfiles/nvim/lua/plugins.bak
mv ~/.dotfiles/nvim/lua/config/keymaps.lua ~/.dotfiles/nvim/lua/config/keymaps.lua.bak
mv ~/.dotfiles/nvim/lua/config/autocmds.lua ~/.dotfiles/nvim/lua/config/autocmds.lua.bak
mv ~/.dotfiles/nvim/lua/config/options.lua ~/.dotfiles/nvim/lua/config/options.lua.bak
```
**Result:** Still broken - proved issue is in LazyVim core, not user config

#### Emptied lazyvim.json extras:
Changed extras array to `[]` to disable all LazyVim extras.
**Result:** Still broken

#### Cleared nvim state and cache:
```bash
rm -rf ~/.local/state/nvim ~/.cache/nvim
```
**Result:** Didn't fix on its own

#### Nuked all plugins:
```bash
rm -rf ~/.local/share/nvim/lazy
```
**Result:** Didn't fix on its own

### 3. Version Changes

#### Upgraded Neovim:
```bash
brew upgrade neovim  # 0.11.4 -> 0.11.5
```
**Result:** Didn't fix

#### Rolled back LazyVim:
```bash
git -C ~/.local/share/nvim/lazy/LazyVim checkout 70e316d4  # v15.10.0
```
**Result:** Didn't fix

#### Restored plugins from lock file:
```bash
nvim --headless -c "lua require('lazy').restore({wait=true})" -c "qa"
```
**Result:** Didn't fix

### 4. Isolation Tests

#### Test configs at /tmp/nvim-test/init.lua:

**Minimal (no plugins):**
```lua
vim.opt.number = true
```
**Result:** `:` works

**lazy.nvim only (no LazyVim):**
```lua
local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
vim.opt.rtp:prepend(lazypath)
require("lazy").setup({
  { "folke/tokyonight.nvim" },
})
```
**Result:** `:` works

**LazyVim:**
```lua
require("lazy").setup({
  { "LazyVim/LazyVim", import = "lazyvim.plugins" },
})
```
**Result:** `:` CRASHES

**LazyVim + noice disabled:**
```lua
require("lazy").setup({
  { "LazyVim/LazyVim", import = "lazyvim.plugins" },
  { "folke/noice.nvim", enabled = false },
})
```
**Result:** `:` works

**noice.nvim standalone (no LazyVim):**
```lua
require("lazy").setup({
  { "folke/noice.nvim", dependencies = { "MunifTanjim/nui.nvim" } },
})
require("noice").setup({})
```
**Result:** `:` CRASHES - confirms noice is the issue, not LazyVim config

### 5. Debug Logging

Added autocmds to log CmdlineEnter/CmdlineLeave:
```lua
vim.api.nvim_create_autocmd("CmdlineEnter", {
  callback = function()
    local f = io.open("/tmp/noice-debug.log", "a")
    f:write("CmdlineEnter triggered at " .. os.date() .. "\n")
    f:close()
  end,
})
```
**Result:** CmdlineEnter fires, CmdlineLeave never fires - crash happens during noice's cmdline handling

## The Mystery Fix

After doing ALL of the above (clearing cache, reinstalling plugins, upgrading neovim), the user restored the original noice.lua config and **it suddenly worked**.

We don't know exactly what fixed it. Possibilities:
1. Clearing `~/.local/state/nvim` removed corrupted state
2. Clearing `~/.cache/nvim` removed corrupted cache
3. Reinstalling plugins fixed corrupted plugin files
4. Neovim upgrade from 0.11.4 to 0.11.5 fixed it
5. Some combination of the above

**THE ISSUE CAME BACK** after working for a while. This confirms it's intermittent/state-related.

## Workaround

Disable noice cmdline in `nvim/lua/plugins/noice.lua`:

```lua
return {
  "folke/noice.nvim",
  opts = {
    cmdline = {
      enabled = false,
    },
    messages = {
      enabled = false,
    },
  },
  init = function()
    vim.opt.cmdheight = 1
  end,
}
```

Or disable noice entirely:
```lua
return {
  { "folke/noice.nvim", enabled = false },
}
```

## Nuclear Option (Sometimes Works)

```bash
rm -rf ~/.local/state/nvim ~/.cache/nvim ~/.local/share/nvim/lazy
nvim  # reinstalls plugins
```

## Plugin Versions at Time of Issue

- noice.nvim: commit 7bfd942 (2025-11-03)
- nui.nvim: commit de74099 (2025-06-08)
- LazyVim: v15.13.0 (2025-11-01)
- snacks.nvim: commit fe7cfe9 (2025-11-18)
- blink.cmp: v1.8.0

## Relevant Links

- **GitHub Issue:** https://github.com/folke/noice.nvim/issues/1184
- **noice.nvim repo:** https://github.com/folke/noice.nvim
- **LazyVim noice config:** https://www.lazyvim.org/plugins/ui#noicenvim

## THE ACTUAL FIX (macOS)

**Codesign the .so files:**
```bash
find ~/.local/share/nvim -name "*.so" | while read lib; do sudo codesign --force --sign - "$lib"; done
```

This fixes macOS code signature caching issues with treesitter parsers that noice invokes.

## For Future Agents

1. If `:` closes neovim, it's almost certainly noice.nvim
2. **TRY THE CODESIGN FIX FIRST** (see above) - this is the actual solution on macOS
3. If that doesn't work, try the nuclear option (clear state/cache/lazy)
4. If still broken, disable noice cmdline as workaround
5. Check issue #1184 for updates
6. The issue is related to macOS code signature caching, not noice.nvim itself
