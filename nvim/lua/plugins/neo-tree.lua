return {
  "nvim-neo-tree/neo-tree.nvim",
  opts = {
    window = {
      position = "right",
    },
    log_level = "warn",
    filesystem = {
      filtered_items = {
        visible = false, -- when true, they will just be displayed differently than normal items
        hide_dotfiles = true,
        hide_gitignored = true,
        never_show_by_pattern = {},
        -- Files/folders to always show even when hidden
        always_show = {
          ".env",
          ".env.local",
          ".env.development",
          ".env.production",
          ".env.test",
          ".mise.toml",
        },
        -- Use patterns for any .env* file
        always_show_by_pattern = {
          ".env*",
        },
      },
    },
  },
}
