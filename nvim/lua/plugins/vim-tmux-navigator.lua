return {
  "christoomey/vim-tmux-navigator",
  -- tmux-only: it drives `tmux select-pane` and checks $TMUX. Inside herdr it
  -- can't cross panes, so disable it there and let keymaps.lua's herdr nav own
  -- ctrl+hjkl instead (see ogulcancelik/herdr#281).
  cond = function()
    return not (vim.env.HERDR_PANE_ID and vim.env.HERDR_PANE_ID ~= "")
  end,
  cmd = {
    "TmuxNavigateLeft",
    "TmuxNavigateDown",
    "TmuxNavigateUp",
    "TmuxNavigateRight",
    "TmuxNavigatePrevious",
  },
  keys = {
    { "<c-h>", "<cmd><C-U>TmuxNavigateLeft<cr>" },
    { "<c-j>", "<cmd><C-U>TmuxNavigateDown<cr>" },
    { "<c-k>", "<cmd><C-U>TmuxNavigateUp<cr>" },
    { "<c-l>", "<cmd><C-U>TmuxNavigateRight<cr>" },
    { "<c-\\>", "<cmd><C-U>TmuxNavigatePrevious<cr>" },
  },
}
