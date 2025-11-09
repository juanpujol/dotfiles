return {
  "folke/snacks.nvim",
  opts = {
    scratch = {
      win = {
        keys = {
          ["delete"] = {
            "D",
            function(self)
              local buf = self.buf
              local bufname = vim.api.nvim_buf_get_name(buf)

              -- Check if this is a scratch buffer
              if not bufname:match(vim.fn.stdpath("data") .. "/scratch/") then
                vim.notify("Not a scratch buffer", vim.log.levels.WARN)
                return
              end

              -- Ask for confirmation
              local confirm = vim.fn.confirm("Delete scratch buffer permanently?", "&Yes\n&No", 2)
              if confirm ~= 1 then
                return
              end

              -- Get the base file path and meta file path
              local file_path = bufname
              local meta_path = bufname .. ".meta"

              -- Close the window first
              self:close()

              -- Delete the buffer
              if vim.api.nvim_buf_is_valid(buf) then
                vim.api.nvim_buf_delete(buf, { force = true })
              end

              -- Delete the files
              local success = true
              if vim.fn.filereadable(file_path) == 1 then
                local result = vim.fn.delete(file_path)
                if result ~= 0 then
                  success = false
                end
              end

              if vim.fn.filereadable(meta_path) == 1 then
                local result = vim.fn.delete(meta_path)
                if result ~= 0 then
                  success = false
                end
              end

              if success then
                vim.notify("Scratch buffer deleted", vim.log.levels.INFO)
              else
                vim.notify("Failed to delete scratch buffer files", vim.log.levels.ERROR)
              end
            end,
            desc = "delete",
          },
        },
      },
    },
  },
}
