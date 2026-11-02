#!/usr/bin/env bash
# Create the Executor apps defined in ~/dotfiles/mcp/apps/<company>/<service>/.
#
#   bootstrap.sh            create apps that are missing, leave existing ones alone
#   bootstrap.sh --update   also commit and deploy every existing app from its folder
#
# App names follow "[company] Service env" (apps/laiki/supabase-prod -> "[laiki] Supabase prod"); the slug is derived
# from the name the way Executor does it ("laiki-supabase-prod"). A folder may carry an email, e.g. google-contact@juanpujol.com. Logins and connections stay manual: see README.md.
# Changing a provider (name, scopes, hosts) in a folder means that app needs a new login after --update.
set -euo pipefail

root="$(cd "$(dirname "$0")" && pwd)/apps"
update=false
case "${1:-}" in
  "") ;;
  --update) update=true ;;
  *) echo "Usage: $0 [--update]" >&2; exit 2 ;;
esac

command -v executor >/dev/null || { echo "executor not on PATH (mise install?)" >&2; exit 1; }
command -v jq >/dev/null || { echo "jq is required" >&2; exit 1; }

service_name() {
  case "$1" in
    cloudflare) echo "Cloudflare" ;;
    posthog) echo "PostHog" ;;
    vercel) echo "Vercel" ;;
    supabase-*) echo "Supabase ${1#supabase-}" ;;
    google-*) echo "Google ${1#google-}" ;;
    slack-*) echo "Slack ${1#slack-}" ;;
    *) echo "$(tr '[:lower:]' '[:upper:]' <<<"${1:0:1}")${1:1}" ;;
  esac
}

framework="$(executor apps framework | jq -r .version)"
apps="$(executor apps list)"

for dir in "$root"/*/*/; do
  dir="${dir%/}"
  service="$(basename "$dir")"
  company="$(basename "$(dirname "$dir")")"
  name="[$company] $(service_name "$service")"
  # Executor derives the slug from the name: lowercase, every run of other characters becomes "-".
  slug="$(tr '[:upper:]' '[:lower:]' <<<"$name" | sed -E 's/[^a-z0-9]+/-/g; s/^-+//; s/-+$//')"

  pinned="$(jq -r '.dependencies.apps' "$dir/package.json")"
  if [ "$pinned" != "$framework" ]; then
    echo "warn  $slug pins apps@$pinned, host runs $framework"
  fi

  id="$(jq -r --arg slug "$slug" '.[] | select(.slug == $slug) | .id' <<<"$apps")"
  if [ -z "$id" ]; then
    id="$(executor apps create --name "$name" --files "$dir" | jq -r .id)"
    commit="$(executor apps source --app "$id" | jq -r .revision.commit)"
    executor apps deploy --app "$id" --commit "$commit" >/dev/null
    echo "new   $slug ($name), link its account in the dashboard"
  elif $update; then
    expected="$(executor apps source --app "$id" | jq -r .revision.commit)"
    commit="$(executor apps commit --app "$id" --files "$dir" --expected "$expected" \
      --message "Sync from dotfiles mcp/apps/$company/$service" | jq -r .revision.commit)"
    executor apps deploy --app "$id" --commit "$commit" >/dev/null
    echo "sync  $slug"
  else
    echo "ok    $slug"
  fi
done
