-- Keymaps are automatically loaded on the VeryLazy event
-- Default keymaps that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/keymaps.lua
-- Add any additional keymaps here

-- Move lines up/down with Alt+Shift+j/k
vim.keymap.set("n", "<M-S-j>", "<cmd>m .+1<cr>==", { desc = "Move Line Down" })
vim.keymap.set("n", "<M-S-k>", "<cmd>m .-2<cr>==", { desc = "Move Line Up" })
vim.keymap.set("v", "<M-S-j>", ":m '>+1<cr>gv=gv", { desc = "Move Selection Down" })
vim.keymap.set("v", "<M-S-k>", ":m '<-2<cr>gv=gv", { desc = "Move Selection Up" })
vim.keymap.set("i", "<M-S-j>", "<esc><cmd>m .+1<cr>==gi", { desc = "Move Line Down" })
vim.keymap.set("i", "<M-S-k>", "<esc><cmd>m .-2<cr>==gi", { desc = "Move Line Up" })
