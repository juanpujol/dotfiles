// Google Workspace MCP (Gmail, Calendar, Drive) for one juanpujol.com account: contact@.
// Same code as apps/lab1095/google-juan except the provider name, which keeps this domain's OAuth client separate.
// OAuth client: Google Cloud project juanpujol-agents (Internal, AI-powered agent client), see ../../../google-workspace.md.
import { decodeJson, defineApp, defineProvider, oauth2, object, router, string } from "apps";
import { mcpRouter } from "apps/mcp";

const servers = {
  gmail: "https://gmailmcp.googleapis.com/mcp/v1",
  calendar: "https://calendarmcp.googleapis.com/mcp/v1",
  drive: "https://drivemcp.googleapis.com/mcp/v1",
};

const auth = "https://www.googleapis.com/auth/";

const headers = (account: { fields: { access_token: string } }) => ({
  Authorization: "Bearer " + account.fields.access_token,
});

const google = defineProvider({
  name: "Google Workspace (juanpujol.com)",
  hosts: ["gmailmcp.googleapis.com", "calendarmcp.googleapis.com", "drivemcp.googleapis.com", "gmail.googleapis.com"],
  auth: {
    oauth: oauth2({
      discover: "https://accounts.google.com",
      scopes: [
        `${auth}gmail.readonly`,
        `${auth}gmail.compose`,
        `${auth}calendar.calendarlist.readonly`,
        `${auth}calendar.events.freebusy`,
        `${auth}calendar.events`,
        `${auth}drive.readonly`,
        `${auth}drive.file`,
      ],
      // Offline access for refresh tokens; select_account forces the account chooser so each app gets the right mailbox.
      authorizationParams: { access_type: "offline", prompt: "select_account consent" },
      resource: null,
    }),
  },
  // The MCP servers answer initialize without credentials, so check the token against Gmail and show which mailbox it is.
  async health({ account, fetch, signal }) {
    const response = await fetch("https://gmail.googleapis.com/gmail/v1/users/me/profile", {
      signal,
      headers: headers(account),
    });
    const profile = await decodeJson(response, object({ emailAddress: string() }));
    return { accountInfo: { externalId: profile.emailAddress, email: profile.emailAddress } };
  },
});

const requirements = { app: { accounts: { google } } };

export default defineApp(requirements, async ({ app, signal }) => {
  const account = app.accounts.google;
  // No approval prompts: Gmail can only draft, Drive cannot change sharing.
  const mount = (url: string) => mcpRouter({ url, account, headers: headers(account), signal });
  return {
    tools: router({
      gmail: await mount(servers.gmail),
      calendar: await mount(servers.calendar),
      drive: await mount(servers.drive),
    }),
  };
});
