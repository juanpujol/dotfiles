// Vercel MCP for Laiki: the Laiki Vercel account (production and staging live in it).
import { defineApp, defineProvider, oauth2, withApprovals } from "apps";
import { type Approval } from "apps/operations/approval";
import { mcpHealth, mcpRouter } from "apps/mcp";

const url = "https://mcp.vercel.com";

const headers = (account: { fields: { access_token: string } }) => ({
  Authorization: "Bearer " + account.fields.access_token,
});

const vercel = defineProvider({
  name: "Vercel",
  hosts: ["mcp.vercel.com"],
  auth: { oauth: oauth2({ discover: url }) },
  health: (check) => mcpHealth(check, { url, headers: headers(check.account) }),
});

const requirements = { app: { accounts: { vercel } } };

// No approval prompts. Blocked: tools that spend money, move projects or domains, replace whole DNS or firewall
// configs in one call, or revoke keys.
const blocked = new Set([
  "buy_domain",
  "create_or_transfer_domain",
  "accept_project_transfer_request",
  "replace_domain_dns_records",
  "put_firewall_config",
  "revoke_kms_signing_key",
]);

const denied: Approval = () => "denied";

export default defineApp(requirements, async ({ app, signal }) => {
  const account = app.accounts.vercel;
  return {
    tools: withApprovals(await mcpRouter({ url, account, headers: headers(account), signal }), (_tool, name) =>
      blocked.has(name) ? denied : undefined,
    ),
  };
});
