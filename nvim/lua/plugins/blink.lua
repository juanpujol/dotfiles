return {
  {
    "saghen/blink.cmp",
    version = "v1.*",
    opts = function(_, opts)
      -- Remove any cmdline configuration to prevent the error
      opts.cmdline = nil
      
      -- Configure keymap
      opts.keymap = opts.keymap or {}
      opts.keymap.preset = "default"
      opts.keymap["<S-j>"] = { "select_next", "fallback" }
      opts.keymap["<S-k>"] = { "select_prev", "fallback" }
      opts.keymap["<CR>"] = { "accept", "fallback" }
      
      -- Force Lua implementation to avoid Rust binary issues
      opts.fuzzy = opts.fuzzy or {}
      opts.fuzzy.implementation = "lua"
      
      return opts
    end,
  },
}
