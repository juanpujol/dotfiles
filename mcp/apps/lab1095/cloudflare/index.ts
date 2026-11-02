// Cloudflare MCP for Lab1095: the Lab1095 Cloudflare account.
import { defineApp, defineProvider, oauth2, withApprovals } from "apps";
import { type Approval } from "apps/operations/approval";
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

// No approval prompts. Blocked: `execute` code that sends a DELETE (zones, Workers, DNS, R2 cannot be undone).
const noDelete: Approval = ({ toolInput }) => {
  const code =
    typeof toolInput === "object" && toolInput !== null && "code" in toolInput && typeof toolInput.code === "string"
      ? toolInput.code
      : "";
  return /["'`]DELETE["'`]/i.test(code) ? "denied" : "approved";
};

export default defineApp(requirements, async ({ app, signal }) => {
  const account = app.accounts.cloudflare;
  return {
    tools: withApprovals(await mcpRouter({ url, account, headers: headers(account), signal }), (_tool, name) =>
      name === "execute" ? noDelete : undefined,
    ),
  };
});
