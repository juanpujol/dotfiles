-- Keymaps are automatically loaded on the VeryLazy event
-- Default keymaps that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/keymaps.lua
-- Add any additional keymaps here

local map = LazyVim.safe_keymap_set

-- Move line up and down with arrows to mitigate Kitty issue with Cmd+K
map("n", "<A-down>", ":m .+1<CR>==") -- move line up(n)
map("n", "<A-up>", ":m .-2<CR>==") -- move line down(n)
map("v", "<A-down>", ":m '>+1<CR>gv=gv") -- move line up(v)
map("v", "<A-up>", ":m '<-2<CR>gv=gv") -- move line down(v)
