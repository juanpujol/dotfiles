# Google Workspace (Gmail, Calendar, Drive) through Executor

Checked: 2026-11-02. Done for lab1095.com.br; repeat per Workspace domain (Laiki, juanpujol.com), each with its own
Cloud project, consent screen and OAuth client, so each company's mail stays in its own Google organization.

Sources: [Configure the Google Workspace MCP servers](https://developers.google.com/workspace/guides/configure-mcp-servers),
[Developer Preview Program](https://developers.google.com/workspace/preview).

## How it fits

Google runs official remote MCP servers, one per product, in Developer Preview:

| Product | URL | Notes |
| --- | --- | --- |
| Gmail | `https://gmailmcp.googleapis.com/mcp/v1` | read, labels, drafts; cannot send |
| Calendar | `https://calendarmcp.googleapis.com/mcp/v1` | read, free/busy, create and edit events |
| Drive | `https://drivemcp.googleapis.com/mcp/v1` | read, create files; cannot change sharing |

Docs, Sheets, Slides, Chat, People exist too (same pattern). Google offers no dynamic client registration, so each
domain needs its own OAuth client, entered once on Executor's connect page.

In Executor: one app per Google account, each mounting the three servers behind one login
(`apps/<company>/google-<user>/`). Writes ask for approval. The health check reads the Gmail profile, so the account
shows which mailbox it is. Google's account chooser is forced (`prompt=select_account consent`) so each app gets the
right mailbox.

## Steps for a new domain

Do these as a Workspace admin of the domain, in a browser profile signed in to that domain only.

1. **Cloud project.** console.cloud.google.com/projectcreate. Name `<Company> Agents`, ID `<company>-agents` (the ID is
   permanent and never reusable). Organization and parent must be the company's domain, not "No organization", so the
   company owns it and teammates can be added through IAM. Ignore the free trial / billing prompts: none of this needs
   billing.
2. **APIs.** Enable all six in one go:
   `https://console.cloud.google.com/apis/enableflow?apiid=gmail.googleapis.com,calendar-json.googleapis.com,drive.googleapis.com,gmailmcp.googleapis.com,calendarmcp.googleapis.com,drivemcp.googleapis.com&project=<project-id>`
3. **Consent screen** (Google Auth Platform, Get started). App name `<Company> Agents`, support and contact email the
   admin, audience **Internal** (only the domain's accounts; no Google verification needed, even for Gmail). Accepting
   the Google API Services User Data Policy is the admin's click.
4. **Data Access scopes.** Add or remove scopes, paste, Add to table, Update, then **Save** (automated clicks on Save
   did not persist; click it by hand and reload to confirm):
   ```
   https://www.googleapis.com/auth/gmail.readonly
   https://www.googleapis.com/auth/gmail.compose
   https://www.googleapis.com/auth/calendar.calendarlist.readonly
   https://www.googleapis.com/auth/calendar.events.freebusy
   https://www.googleapis.com/auth/calendar.events
   https://www.googleapis.com/auth/drive.readonly
   https://www.googleapis.com/auth/drive.file
   ```
   For an Internal app this list is mostly documentation, but keep it in sync with the app's `scopes`.
5. **OAuth client** (Clients, Create). Type Web application, name `Executor`, redirect URI
   `http://127.0.0.1:4312/api/oauth/callback` (add the mini PC `https://<host>.ts.net/api/oauth/callback` later), and
   check **Use this client for an AI-powered agent** (permanent for that client). Save the client ID and secret to the
   company's 1Password vault right away: Google does not show the secret again.
6. **Developer Preview.** Apply at the form linked from the program page, once per person: the form records the signed-in
   account; the access email must be in the Workspace domain; give the project number. The admin ticks the terms and
   submits. Registration "normally takes a day" (Lab1095 took a few hours); if nothing in a week, write to
   workspace-dpp-mod@google.com. Before approval the MCP tools fail with "requires that your Google Cloud project ... is
   enrolled in the Google Workspace Developer Preview Program".
7. **Executor.** Copy `apps/lab1095/google-juan/` to `apps/<company>/google-<user>/` (one folder per account, update
   the comments), run `~/dotfiles/mcp/bootstrap.sh`, then per app: Accounts, Connect new account, paste the client ID
   and secret (first time only; Executor reuses the saved client), pick the account in Google's chooser, name the
   account `[<company>] Google <user> - full access`. Login and health work before the preview is approved; the MCP
   tools only after.
8. **Connection.** Put the mailboxes in the company's communication connection (`<company>-comms`), separate from
   infrastructure, and add `executor-<company>-comms` only to projects that should read mail.

**Second domain on the same Executor:** Executor offers the Google client it already saved (it keys saved clients by
issuer plus client ID), so the first connect for a new domain silently used Lab1095's client and Google answered
"Access blocked: ... can only be used within its organization" (`org_internal`). Fix: on Connect new account, open
**Advanced**, choose **Change** next to OAuth client, and paste the new domain's client. Existing accounts keep the
client they signed in with, so other domains are unaffected. Give each domain's provider its own name anyway
(`Google Workspace (juanpujol.com)`).

## Lab1095 record

| Item | Value |
| --- | --- |
| Cloud project | `lab1095-agents` ("Lab1095 Agents"), number 1035106704839, organization lab1095.com.br |
| Consent screen | Lab1095 Agents, Internal, support/contact juan@lab1095.com.br |
| OAuth client | `Executor`, Web, AI-powered agent, redirect `http://127.0.0.1:4312/api/oauth/callback` |
| Credential | 1Password, Lab1095 account: `Google OAuth: lab1095-agents (Executor)` ([open](https://start.1password.com/open/i?a=54B4OWMKEZAIVKOOVSUYBB5CCM&v=wil6u5vgconmmvwp63mpeoc6xe&i=mat6bu2f5krng4h7nz3gdzb3su&h=lab1095.1password.com)) |
| Developer Preview | applied 2026-11-02 for juan@ and ferramentas@; project 1035106704839 registered the same day (email at 14:20, a few hours after applying) |
| Executor apps | `[lab1095] Google juan`, `[lab1095] Google ferramentas` |
| Connection | `lab1095-comms` (both apps plus Slack); used by Orbit as `executor-lab1095-comms` |

## juanpujol.com record

| Item | Value |
| --- | --- |
| Cloud project | `juanpujol-agents` ("Juanpujol Agents"), number 300775206367, organization juanpujol.com |
| Consent screen | Juanpujol Agents, Internal, support/contact contact@juanpujol.com |
| OAuth client | `Executor`, Web, AI-powered agent, redirect `http://127.0.0.1:4312/api/oauth/callback` |
| Credential | personal 1Password: `Google OAuth: juanpujol-agents (Executor)` |
| Developer Preview | applied and registered 2026-11-02; Gmail, Calendar (7 calendars) and Drive verified for contact@juanpujol.com |
| Executor app | `[juanpujol] Google contact@juanpujol.com` (folder `apps/juanpujol/google-contact@juanpujol.com`), account `[juanpujol] Google contact@juanpujol.com - full access`, Working |
| Connection | `juanpujol-comms`, not added to any project yet |

## Open

- Verified 2026-11-02 after approval: Gmail labels, Calendar list and Drive listing work for juan@ and ferramentas@ through `executor-lab1095-comms`.
- Mini PC: add its redirect URI to the client; Google accepts `https` redirects on any host.
- 2026-11-02: `[lab1095] Google juan` dropped to "Needs sign-in" about an hour after linking while ferramentas kept
  refreshing. Reconnected; if it recurs, check whether juan@ (an admin) gets a refresh token and any Workspace session
  controls.
