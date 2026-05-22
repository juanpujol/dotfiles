-- Options are automatically loaded before lazy.nvim startup
-- Default options that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/options.lua
-- Add any additional options here

-- Enable relative lines
vim.opt.nu = true
vim.opt.rnu = true

-- No wrap
vim.opt.wrap = false

-- Always keep 8 lines above and below cursor
vim.opt.scrolloff = 8

-- Set completeopt to have a better completion experience
vim.opt.completeopt = { "menuone", "noselect" }

-- Enable persistent undo
vim.opt.undofile = true

-- Enable system clipboard only when a compatible provider exists.
local function executable(cmd)
  return vim.fn.executable(cmd) == 1
end

if executable("pbcopy") and executable("pbpaste") then
  vim.g.clipboard = {
    name = "pbcopy",
    copy = {
      ["+"] = "pbcopy",
      ["*"] = "pbcopy",
    },
    paste = {
      ["+"] = "pbpaste",
      ["*"] = "pbpaste",
    },
    cache_enabled = 0,
  }
  vim.opt.clipboard = "unnamedplus"
elseif executable("wl-copy") and executable("wl-paste") then
  vim.g.clipboard = {
    name = "wl-clipboard",
    copy = {
      ["+"] = "wl-copy --foreground --type text/plain",
      ["*"] = "wl-copy --foreground --primary --type text/plain",
    },
    paste = {
      ["+"] = "wl-paste --no-newline",
      ["*"] = "wl-paste --primary --no-newline",
    },
    cache_enabled = 0,
  }
  vim.opt.clipboard = "unnamedplus"
elseif executable("xclip") then
  vim.g.clipboard = {
    name = "xclip",
    copy = {
      ["+"] = "xclip -selection clipboard",
      ["*"] = "xclip -selection primary",
    },
    paste = {
      ["+"] = "xclip -selection clipboard -o",
      ["*"] = "xclip -selection primary -o",
    },
    cache_enabled = 0,
  }
  vim.opt.clipboard = "unnamedplus"
elseif executable("xsel") then
  vim.g.clipboard = {
    name = "xsel",
    copy = {
      ["+"] = "xsel --clipboard --input",
      ["*"] = "xsel --primary --input",
    },
    paste = {
      ["+"] = "xsel --clipboard --output",
      ["*"] = "xsel --primary --output",
    },
    cache_enabled = 0,
  }
  vim.opt.clipboard = "unnamedplus"
else
  vim.opt.clipboard = ""
end

-- Set column line
vim.opt.colorcolumn = "80"

-- Spell checking
vim.opt.spell = true
vim.opt.spelllang = "en_us,pt_br"

-- Set eslint
vim.g.eslint_on_type = false

-- Set LSP logging to warn level to prevent large log files
-- Use "debug" or "trace" only when troubleshooting LSP issues
vim.lsp.set_log_level("warn")
