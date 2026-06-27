-- Keymaps are automatically loaded on the VeryLazy event
-- Default keymaps that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/keymaps.lua
-- Add any additional keymaps here

-- Delete without yanking
vim.keymap.set({ "n", "v" }, "d", '"_d', { desc = "Delete without yank" })
vim.keymap.set({ "n", "v" }, "D", '"_D', { desc = "Delete to EOL without yank" })

-- Move lines up/down with Alt+Shift+j/k
vim.keymap.set("n", "<M-S-j>", "<cmd>m .+1<cr>==", { desc = "Move Line Down" })
vim.keymap.set("n", "<M-S-k>", "<cmd>m .-2<cr>==", { desc = "Move Line Up" })
vim.keymap.set("v", "<M-S-j>", ":m '>+1<cr>gv=gv", { desc = "Move Selection Down" })
vim.keymap.set("v", "<M-S-k>", ":m '<-2<cr>gv=gv", { desc = "Move Selection Up" })
vim.keymap.set("i", "<M-S-j>", "<esc><cmd>m .+1<cr>==gi", { desc = "Move Line Down" })
vim.keymap.set("i", "<M-S-k>", "<esc><cmd>m .-2<cr>==gi", { desc = "Move Line Up" })

-- Seamless ctrl-hjkl navigation between nvim splits and herdr panes.
-- Only active inside a herdr pane; christoomey/vim-tmux-navigator handles tmux.
-- Moves the nvim split, and at an edge hands focus off to the herdr pane in
-- that direction (the nvim half of ogulcancelik/herdr#281).
if vim.env.HERDR_PANE_ID and vim.env.HERDR_PANE_ID ~= "" then
  local herdr = vim.env.HERDR_BIN_PATH
  if herdr == nil or herdr == "" then
    herdr = "herdr"
  end
  local function nav(wincmd, dir)
    local prev = vim.api.nvim_get_current_win()
    vim.cmd("wincmd " .. wincmd)
    if vim.api.nvim_get_current_win() ~= prev then
      return -- moved within nvim
    end
    -- At a split edge: cross into the neighbouring herdr pane.
    vim.fn.system({ herdr, "pane", "focus", "--direction", dir, "--current" })
  end
  local dirs = { h = "left", j = "down", k = "up", l = "right" }
  for key, dir in pairs(dirs) do
    vim.keymap.set("n", "<C-" .. key .. ">", function()
      nav(key, dir)
    end, { silent = true, noremap = true, desc = "Navigate split / herdr pane " .. dir })
  end
end
