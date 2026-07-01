#!/usr/bin/env bash
# vim-nav — herdr side. Invoked by a plugin_action as: navigate.sh <left|down|up|right>
#
# Vim-aware herdr pane navigation — the herdr equivalent of vim-tmux-navigator.
# If the focused pane runs Vim/Neovim in the foreground, forward the matching
# ctrl+<hjkl> chord *into* the pane so Vim moves its own splits (and hands focus
# back to herdr at an edge split — see nvim/lua/config/keymaps.lua). Otherwise
# move herdr's pane focus directly.
#
# Bound via type="plugin_action" (NOT type="shell"): herdr reaps plugin-action
# children but leaks shell-command children as zombies (one per keypress), which
# eventually fills the process table (os error 35). See herdr-plugin.toml.
#
# Requires jq; without it, detection is skipped and every key just moves herdr
# pane focus (no Vim awareness).
set -euo pipefail
export PATH="/opt/homebrew/bin:$PATH"

dir="${1:?usage: navigate.sh <left|down|up|right>}"
herdr="${HERDR_BIN_PATH:-herdr}"

case "$dir" in
  left)  key="ctrl+h" ;;
  down)  key="ctrl+j" ;;
  up)    key="ctrl+k" ;;
  right) key="ctrl+l" ;;
  *) echo "navigate.sh: unknown direction: $dir" >&2; exit 2 ;;
esac

# Foreground process names meaning "Vim is in control": vi, vim, nvim, view,
# gvim, vimdiff, ... (the same matcher vim-tmux-navigator uses).
vim_re='^g?(view|l?n?vim?x?)(diff)?$'

pane=""
is_vim=0
if command -v jq >/dev/null 2>&1; then
  info=$("$herdr" pane process-info --current 2>/dev/null || true)
  if [ -n "$info" ]; then
    pane=$(jq -r '.result.process_info.pane_id // empty' <<<"$info")
    if jq -e --arg re "$vim_re" \
        '.result.process_info.foreground_processes[]?.name
         | ascii_downcase | select(test($re))' >/dev/null 2>&1 <<<"$info"; then
      is_vim=1
    fi
  fi
fi

if [ "$is_vim" -eq 1 ] && [ -n "$pane" ]; then
  exec "$herdr" pane send-keys "$pane" "$key"
else
  exec "$herdr" pane focus --direction "$dir" --current
fi
