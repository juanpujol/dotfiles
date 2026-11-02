// Cloudflare MCP for Laiki: the Laiki Cloudflare account (production and staging live in it).
import { defineApp, defineProvider, oauth2 } from "apps";
import { mcpHealth, mcpRouter } from "apps/mcp";

const url = "https://mcp.cloudflare.com/mcp";

const headers = (account: { fields: { access_token: string } }) => ({
  Authorization: "Bearer " + account.fields.access_token,
});

const cloudflare = defineProvider({
  name: "Cloudflare",
  hosts: ["mcp.cloudflare.com"],
  auth: { oauth: oauth2({ discover: url }) },
  health: (check) => mcpHealth(check, { url, headers: headers(check.account) }),
});

const requirements = { app: { accounts: { cloudflare } } };

// No approval prompts: unattended routines must not stall. Limits come from the login (Cloudflare token is read-only).
export default defineApp(requirements, async ({ app, signal }) => {
  const account = app.accounts.cloudflare;
  return { tools: await mcpRouter({ url, account, headers: headers(account), signal }) };
});
