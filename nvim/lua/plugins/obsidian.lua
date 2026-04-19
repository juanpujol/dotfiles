return {
  "epwalsh/obsidian.nvim",
  version = "*",
  lazy = true,
  ft = "markdown",
  dependencies = {
    "nvim-lua/plenary.nvim",
  },
  opts = {
    workspaces = {
      {
        name = "JP",
        path = "/Users/juan/Library/Mobile Documents/iCloud~md~obsidian/Documents/JP",
      },
    },
    -- Use fzf-lua for pickers
    picker = {
      name = "fzf-lua",
    },
    completion = {
      nvim_cmp = false,
      blink = true,
      min_chars = 2,
    },
    ui = {
      enable = true,
    },
    -- Open daily notes in current window
    daily_notes = {
      folder = "daily",
      date_format = "%Y-%m-%d",
    },
  },
}
