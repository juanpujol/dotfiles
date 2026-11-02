// Slack MCP for the LAB1095 workspace, acting as one user: juan@ (user token).
// Slack app "Lab1095 Agents" (A0CE5TG0Q9Y, internal to LAB1095, MCP enabled), read and write user scopes.
// Another teammate: copy this folder to slack-<user>; the same Slack app and client serve everyone in the workspace.
import { defineApp, defineProvider, oauth2 } from "apps";
import { mcpHealth, mcpRouter } from "apps/mcp";

const url = "https://mcp.slack.com/mcp";

const headers = (account: { fields: { access_token: string } }) => ({
  Authorization: "Bearer " + account.fields.access_token,
});

const slack = defineProvider({
  name: "Slack",
  hosts: ["mcp.slack.com"],
  auth: {
    oauth: oauth2({
      discover: url,
      // Must match the user scopes in the Slack app's manifest.
      scopes: [
        "search:read.public",
        "search:read.private",
        "search:read.mpim",
        "search:read.im",
        "search:read.files",
        "search:read.users",
        "files:read",
        "emoji:read",
        "channels:history",
        "groups:history",
        "mpim:history",
        "im:history",
        "reactions:read",
        "canvases:read",
        "users:read",
        "users:read.email",
        "channels:read",
        "groups:read",
        "im:read",
        "mpim:read",
        "lists:read",
        "chat:write",
        "reactions:write",
        "channels:write",
        "groups:write",
        "im:write",
        "mpim:write",
        "canvases:write",
        "files:write",
        "lists:write",
      ],
    }),
  },
  health: (check) => mcpHealth(check, { url, headers: headers(check.account) }),
});

const requirements = { app: { accounts: { slack } } };

// No approval prompts: unattended routines must not stall. Limits come from the login.
export default defineApp(requirements, async ({ app, signal }) => {
  const account = app.accounts.slack;
  return { tools: await mcpRouter({ url, account, headers: headers(account), signal }) };
});
