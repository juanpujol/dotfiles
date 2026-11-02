// Supabase MCP for Laiki production, read-only.
// Three layers: the token only gets read scopes (no secrets:read, which exposes the service-role key),
// the server runs with read_only=true, and every tool not marked read-only asks for approval.
import { defineApp, defineProvider, oauth2 } from "apps";
import { mcpHealth, mcpRouter } from "apps/mcp";

const url = "https://mcp.supabase.com/mcp?project_ref=jidsaaopsvaslsapgldm&read_only=true";

const headers = (account: { fields: { access_token: string } }) => ({
  Authorization: "Bearer " + account.fields.access_token,
});

const supabase = defineProvider({
  name: "Supabase (read-only)",
  hosts: ["mcp.supabase.com"],
  auth: {
    oauth: oauth2({
      discover: "https://mcp.supabase.com/mcp",
      scopes: [
        "organizations:read",
        "projects:read",
        "database:read",
        "analytics:read",
        "edge_functions:read",
        "environment:read",
        "storage:read",
      ],
    }),
  },
  health: (check) => mcpHealth(check, { url, headers: headers(check.account) }),
});

const requirements = { app: { accounts: { supabase } } };

// No approval prompts: unattended routines must not stall. Limits come from the login (read scopes) and the server (read_only=true).
export default defineApp(requirements, async ({ app, signal }) => {
  const account = app.accounts.supabase;
  return { tools: await mcpRouter({ url, account, headers: headers(account), signal }) };
});
