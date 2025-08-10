if true then
  return {}
end

return {
  {
    "neovim/nvim-lspconfig",
    opts = {
      servers = {
        eslint = {
          filetypes = {
            "javascript",
            "javascriptreact",
            "javascript.jsx",
            "typescript",
            "typescriptreact",
            "typescript.tsx",
            "vue",
            "html",
            "markdown",
            "json",
            "jsonc",
            "yaml",
            "toml",
            "xml",
            "gql",
            "graphql",
            "astro",
            "svelte",
            "css",
            "less",
            "scss",
            "pcss",
            "postcss",
          },
          settings = {
            -- Add working directory mode
            workingDirectory = { mode = "location" },
            -- Increase timeouts
            implicitProjectConfig = {
              checkJs = true,
            },
            rulesCustomizations = {
              { rule = "style/*", severity = "off", fixable = true },
              { rule = "format/*", severity = "off", fixable = true },
              { rule = "*-indent", severity = "off", fixable = true },
              { rule = "*-spacing", severity = "off", fixable = true },
              { rule = "*-spaces", severity = "off", fixable = true },
              { rule = "*-order", severity = "off", fixable = true },
              { rule = "*-dangle", severity = "off", fixable = true },
              { rule = "*-newline", severity = "off", fixable = true },
              { rule = "*quotes", severity = "off", fixable = true },
              { rule = "*semi", severity = "off", fixable = true },
            },
          },
          on_attach = function(client, bufnr)
            -- Enable formatting
            client.server_capabilities.documentFormattingProvider = true

            -- Increase LSP timeout
            client.config.flags = {
              debounce_text_changes = 150,
              allow_incremental_sync = true,
            }

            -- Format on save with longer timeout
            vim.api.nvim_create_autocmd("BufWritePre", {
              buffer = bufnr,
              callback = function()
                -- Set a longer timeout (10 seconds)
                vim.lsp.buf_request_sync(
                  bufnr,
                  "textDocument/formatting",
                  vim.lsp.util.make_formatting_params({}),
                  10000
                )
                vim.cmd("EslintFixAll")
              end,
            })
          end,
        },
      },
    },
  },
}
