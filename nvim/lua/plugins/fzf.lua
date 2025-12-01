return {
  "ibhagwan/fzf-lua",
  opts = {
    files = {
      -- Show hidden files, ignore .git but not .gitignore patterns
      fd_opts = [[--color=never --type f --hidden --follow --no-ignore --exclude .git]],
      rg_opts = [[--color=never --files --hidden --follow --no-ignore -g "!.git"]],
    },
    git = {
      files = {
        -- Include ignored files (like .env) along with tracked and untracked
        cmd = "git ls-files --exclude-standard --cached --others; git ls-files --ignored --exclude-standard",
      },
    },
  },
}
