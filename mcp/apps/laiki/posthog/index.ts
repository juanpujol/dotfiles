// PostHog MCP for Laiki: the Laiki PostHog organization.
import { defineApp, defineProvider, oauth2, withApprovals } from "apps";
import { type Approval } from "apps/operations/approval";
import { mcpHealth, mcpRouter } from "apps/mcp";

const url = "https://mcp.posthog.com/mcp";

const headers = (account: { fields: { access_token: string } }) => ({
  Authorization: "Bearer " + account.fields.access_token,
});

const posthog = defineProvider({
  name: "PostHog",
  hosts: ["mcp.posthog.com"],
  auth: { oauth: oauth2({ discover: url }) },
  health: (check) => mcpHealth(check, { url, headers: headers(check.account) }),
});

const requirements = { app: { accounts: { posthog } } };

// No approval prompts. Blocked: `exec` calls with --confirm, PostHog's marker for destructive tools (deletes).
const noDestructive: Approval = ({ toolInput }) => {
  const command =
    typeof toolInput === "object" && toolInput !== null && "command" in toolInput && typeof toolInput.command === "string"
      ? toolInput.command
      : "";
  return command.includes("--confirm") ? "denied" : "approved";
};

export default defineApp(requirements, async ({ app, signal }) => {
  const account = app.accounts.posthog;
  return {
    tools: withApprovals(await mcpRouter({ url, account, headers: headers(account), signal }), (_tool, name) =>
      name === "exec" ? noDestructive : undefined,
    ),
  };
});
