# Slack through Executor

Checked: 2026-11-02. Done for the LAB1095 workspace; repeat per Slack workspace (Laiki) with its own app.

Sources: [Slack MCP server overview](https://docs.slack.dev/ai/slack-mcp-server/),
[Connect to agent harnesses](https://docs.slack.dev/ai/slack-mcp-server/connect-to-harnesses/).

## How it fits

Slack's official MCP server is `https://mcp.slack.com/mcp` (Streamable HTTP). It acts as the signed-in user (user token)
and only accepts clients backed by a Slack app that is internal to the workspace or published in the Slack Marketplace;
unlisted distributed apps are refused. No dynamic client registration, so each workspace needs its own app and its client
ID and secret are entered once on Executor's connect page. The token endpoint accepts only `client_secret_post`.

One Slack app serves every member of its workspace: each person authorizes it with their own Slack login. In Executor,
one app per person (`apps/<company>/slack-<user>/`); every write asks for approval.

## Steps for a new workspace

1. **Create the app** at api.slack.com/apps: Create New App, From a manifest, pick the workspace. The wizard's editor
   did not keep pasted text in our run (it created "Demo App"); creating it and then fixing the manifest worked.
2. **App Manifest** (app settings, `app.slack.com/app-settings/<team>/<app>/app-manifest`): set the manifest below and
   Save Changes. `is_mcp_enabled: true` is the MCP switch. The description is limited to 140 characters.
3. **Credentials**: Basic Information, App Credentials. Save the **Client ID** and **Client Secret** (click Show; not the
   Signing Secret) to the company's 1Password vault. A wrong value fails the login with `bad_client_secret`.
4. **Executor**: copy `apps/lab1095/slack-juan/` to `apps/<company>/slack-<user>/`, keep its `scopes` equal to the
   manifest's, run `~/dotfiles/mcp/bootstrap.sh`, then Accounts, Connect new account, paste client ID and secret,
   approve in Slack, name the account `[<company>] Slack <user> - full access`. No separate "Install App" step was
   needed.
5. **Connection**: add the app to `<company>-comms`.

Manifest used for LAB1095 (redirect URI: add the mini PC one later):

```json
{
  "display_information": {
    "name": "Lab1095 Agents",
    "description": "Lab1095 AI agents (via Executor) read and post in Slack as you. Every write asks for approval."
  },
  "oauth_config": {
    "redirect_urls": ["http://127.0.0.1:4312/api/oauth/callback"],
    "scopes": {
      "user": [
        "search:read.public", "search:read.private", "search:read.mpim", "search:read.im", "search:read.files",
        "search:read.users", "files:read", "emoji:read", "channels:history", "groups:history", "mpim:history",
        "im:history", "reactions:read", "canvases:read", "users:read", "users:read.email", "channels:read",
        "groups:read", "im:read", "mpim:read", "lists:read",
        "chat:write", "reactions:write", "channels:write", "groups:write", "im:write", "mpim:write",
        "canvases:write", "files:write", "lists:write"
      ]
    },
    "pkce_enabled": false
  },
  "settings": {
    "org_deploy_enabled": false,
    "socket_mode_enabled": false,
    "is_mcp_enabled": true,
    "token_rotation_enabled": false,
    "app_level_token_rotation_enabled": false
  }
}
```

For read-only, drop the nine `:write` scopes in both the manifest and the app folder (a scope change means a new login).

## Lab1095 record

| Item | Value |
| --- | --- |
| Slack app | Lab1095 Agents, App ID `A0CE5TG0Q9Y`, workspace LAB1095 (`T0AQEQS597V`), internal, MCP enabled |
| Scopes | 30 user scopes (read and write) |
| Credential | 1Password, Lab1095 account: `Slack app: Lab1095 Agents (Executor)` |
| Executor app | `[lab1095] Slack juan`, account `[lab1095] Slack juan - full access` |
| Connection | `lab1095-comms`; Orbit uses `executor-lab1095-comms` |
| Verified | 2026-11-02: tool list and a channel listing (23 channels) through Codex in Orbit |

The workspace also has an older Slack app, `hermes` (A0BSW13JH4G), unrelated to this setup.
