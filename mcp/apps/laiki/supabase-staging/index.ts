// Supabase MCP for Laiki staging, read-write (database features only).
// Asks for approval only before tools the server marks destructive.
// Its own Supabase login with full scopes; prod uses a separate read-only login.
import { defineApp, defineProvider, oauth2 } from "apps";
import { mcpHealth, mcpRouter } from "apps/mcp";

const url = "https://mcp.supabase.com/mcp?project_ref=prwlocjhamjsbfnvjctq&features=database";

const headers = (account: { fields: { access_token: string } }) => ({
  Authorization: "Bearer " + account.fields.access_token,
});

const supabase = defineProvider({
  name: "Supabase",
  hosts: ["mcp.supabase.com"],
  auth: { oauth: oauth2({ discover: "https://mcp.supabase.com/mcp" }) },
  health: (check) => mcpHealth(check, { url, headers: headers(check.account) }),
});

const requirements = { app: { accounts: { supabase } } };

// No approval prompts: unattended routines must not stall. Limits come from the login.
export default defineApp(requirements, async ({ app, signal }) => {
  const account = app.accounts.supabase;
  return { tools: await mcpRouter({ url, account, headers: headers(account), signal }) };
});
