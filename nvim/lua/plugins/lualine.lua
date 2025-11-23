return {
  "nvim-lualine/lualine.nvim",
  opts = function(_, opts)
    opts.options = opts.options or {}
    opts.options.component_separators = { left = "", right = "" }
    opts.options.section_separators = { left = "", right = "" }

    opts.sections = opts.sections or {}
    -- opts.sections.lualine_z = opts.sections.lualine_z or {}

    -- Add rounded cap to the far LEFT (beginning of lualine_a)
    table.insert(opts.sections.lualine_a, 1, {
      function()
        return ""
      end,
      padding = 0,
      color = { fg = "#89b4fa", bg = "NONE" }, -- match your lualine_a bg color
    })
    -- Add rounded cap to the far RIGHT (end of lualine_z)
    table.insert(opts.sections.lualine_z, {
      function()
        return ""
      end,
      padding = 0,
      color = { fg = "#89b4fa", bg = "NONE" }, -- match your lualine_z bg color
    })

    -- Create CUSTOM neo-tree extension with rounded cap
    local neo_tree_extension = {
      sections = {
        lualine_a = {
          {
            function()
              return ""
            end,
            padding = 0,
            color = { fg = "#89b4fa", bg = "NONE" },
          },
          {
            function()
              return vim.fn.fnamemodify(vim.fn.getcwd(), ":~")
            end,
          },
        },
      },
      filetypes = { "neo-tree" }, -- This tells lualine when to use this extension
    }
    -- Remove built-in "neo-tree" string and add our custom table
    local filtered_extensions = {}
    for _, ext in ipairs(opts.extensions or {}) do
      if ext ~= "neo-tree" then
        table.insert(filtered_extensions, ext)
      end
    end
    table.insert(filtered_extensions, neo_tree_extension)
    opts.extensions = filtered_extensions
  end,
}
