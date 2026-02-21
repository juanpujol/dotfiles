#!/usr/bin/env bash
url="$1"

if [[ "$(uname)" == "Darwin" ]]; then
    open "$url"
elif command -v xdg-open &>/dev/null && xdg-open "$url" 2>/dev/null; then
    true
elif command -v xclip &>/dev/null; then
    echo -n "$url" | xclip -selection clipboard
    tmux display-message "Copied: $url"
elif command -v xsel &>/dev/null; then
    echo -n "$url" | xsel -ib
    tmux display-message "Copied: $url"
elif command -v wl-copy &>/dev/null; then
    echo -n "$url" | wl-copy
    tmux display-message "Copied: $url"
else
    tmux set-buffer "$url"
    tmux display-message "Copied to tmux buffer: $url"
fi
