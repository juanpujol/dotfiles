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

-- Enable access to the system clipboard
vim.opt.clipboard = "unnamed,unnamedplus"

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
