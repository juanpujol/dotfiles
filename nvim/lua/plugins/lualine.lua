return {
  "nvim-lualine/lualine.nvim",
  opts = function(_, opts)
    opts.options = opts.options or {}
    opts.options.component_separators = { left = "", right = "" }
    opts.options.section_separators = { left = "", right = "" }

    opts.sections = opts.sections or {}
    -- opts.sections.lualine_z = opts.sections.lualine_z or {}

    local function mode_color()
      local colors = {
        n = "#89b4fa",
        i = "#a6e3a1",
        v = "#caa6f8",
        V = "#caa6f8",
        ["\22"] = "#caa6f8",
        c = "#fab387",
        R = "#f38ba8",
        t = "#a6e3a1",
      }
      return { fg = colors[vim.fn.mode()] or "#89b4fa", bg = "NONE" }
    end

    -- Add rounded cap to the far LEFT (beginning of lualine_a)
    table.insert(opts.sections.lualine_a, 1, {
      function()
        return ""
      end,
      padding = 0,
      color = mode_color,
    })
    -- Add rounded cap to the far RIGHT (end of lualine_z)
    table.insert(opts.sections.lualine_z, {
      function()
        return ""
      end,
      padding = 0,
      color = mode_color,
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
            color = mode_color,
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
