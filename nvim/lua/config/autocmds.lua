-- Autocmds are automatically loaded on the VeryLazy event
-- Default autocmds that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/autocmds.lua
--
-- Add any additional autocmds here
-- with `vim.api.nvim_create_autocmd`
--
-- Or remove existing autocmds by their group name (which is prefixed with `lazyvim_` for the defaults)
-- e.g. vim.api.nvim_del_augroup_by_name("lazyvim_wrap_spell")

-- Auto-restart Copilot when the LSP exits and sets is_disabled = true.
-- Without this, the suggestion module fires "copilot is disabled" on every keystroke
-- until the user manually runs :Copilot enable.
local _copilot_restarting = false
vim.api.nvim_create_autocmd("BufEnter", {
  callback = function()
    if _copilot_restarting then
      return
    end
    local ok, c = pcall(require, "copilot.client")
    if ok and c.is_disabled() then
      _copilot_restarting = true
      vim.defer_fn(function()
        _copilot_restarting = false
        pcall(require("copilot.command").enable)
      end, 1000)
    end
  end,
  desc = "Auto-restart Copilot when disabled",
})

vim.api.nvim_create_autocmd("FileType", {
  pattern = { "sh" },
  callback = function()
    if vim.fn.expand("%:t"):match("^%.env") then
      vim.diagnostic.enable(false, { bufnr = 0 })
    end
  end,
})
