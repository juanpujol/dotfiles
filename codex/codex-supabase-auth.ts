#!/usr/bin/env bun
// Keeps Codex's Supabase MCP OAuth tokens fresh.
//
// Codex drops the client_secret Supabase issues at dynamic client registration
// (openai/codex#43216), so its own refresh fails once the 24h access token
// expires and it demands a new browser login. This tool owns the OAuth client
// instead: it registers, keeps the secret in its own Keychain entry, refreshes
// with it, and writes the tokens into Codex's Keychain entry in Codex's format.
// Codex then always finds a fresh access token and never runs its refresh.
//
// Usage:
//   bun ~/dotfiles/codex/codex-supabase-auth.ts install   build the binary, install the hourly launchd job
//   codex-supabase-auth login <server>     one-time browser consent
//   codex-supabase-auth refresh [--force]  refresh tokens expiring within 12h
//   codex-supabase-auth status             show token state (no secrets)
//
// `install` compiles this file to ~/.local/bin/codex-supabase-auth and launchd
// runs that binary, so Login Items lists it by name instead of by the signer
// of whatever interpreter would launch it. Rerun `install` after editing.
//
// Delete this tool and its launchd job once openai/codex#43216 ships.
//
// Retired 2026-11-02: Supabase now goes through Executor (see ~/dotfiles/mcp/README.md)
// and the launchd job was removed. Kept in case Codex needs direct Supabase MCP again.

import { mkdirSync, rmSync, statSync, writeFileSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

const MCP_JSON = join(homedir(), "Code/@laiki/laiki2/.mcp.json");
const SERVERS = ["supabase-prod", "supabase-staging"];
const READ_ONLY_SERVERS = new Set(["supabase-prod"]);

const ISSUER = "https://api.supabase.com";
const AUTHORIZE_URL = `${ISSUER}/v1/oauth/authorize`;
const TOKEN_URL = `${ISSUER}/v1/oauth/token`;
const REGISTER_URL = `${ISSUER}/platform/oauth/apps/register`;

const CODEX_SERVICE = "Codex MCP Credentials";
const OWN_SERVICE = "codex-supabase-auth";
const REFRESH_WITHIN_MS = 12 * 60 * 60 * 1000;
const LOGIN_TIMEOUT_MS = 5 * 60 * 1000;

const STATE_DIR = join(homedir(), ".local/state/codex-supabase-auth");
const LOCK_DIR = join(STATE_DIR, "lock");
const LABEL = "dev.juan.codex-supabase-auth";
const PLIST = join(homedir(), "Library/LaunchAgents", `${LABEL}.plist`);
const SOURCE = join(homedir(), "dotfiles/codex/codex-supabase-auth.ts");
const BINARY = join(homedir(), ".local/bin/codex-supabase-auth");

type Server = { name: string; url: string; scopes: string[] };
type Client = { client_id: string; client_secret: string };
type Managed = Client & { refresh_token: string; scope?: string };
type TokenResponse = {
  access_token: string;
  token_type: string;
  expires_in: number;
  refresh_token?: string;
  scope?: string;
};
type CodexEntry = { client_id: string; expires_at?: number };

// --- config ----------------------------------------------------------------

async function loadServer(name: string): Promise<Server> {
  if (!SERVERS.includes(name)) throw new Error(`unknown server ${name}; expected ${SERVERS.join(" | ")}`);
  const config: unknown = await Bun.file(MCP_JSON).json();
  const entry = (config as { mcpServers?: Record<string, { url?: string; scopes?: string[] }> }).mcpServers?.[
    name
  ];
  if (!entry?.url) throw new Error(`${name} missing from ${MCP_JSON}`);
  const server = { name, url: entry.url, scopes: entry.scopes ?? [] };
  if (READ_ONLY_SERVERS.has(name)) assertReadOnlyConfig(server);
  return server;
}

function assertReadOnlyConfig(server: Server) {
  if (new URL(server.url).searchParams.get("read_only") !== "true")
    throw new Error(`${server.name}: URL must carry read_only=true; refusing`);
  if (server.scopes.length === 0 || !server.scopes.every((scope) => scope.endsWith(":read")))
    throw new Error(`${server.name}: scopes must be a non-empty list of :read scopes; refusing`);
}

// Rejects any grant wider than the requested :read scopes. Supabase omits
// `scope` from some responses; the requested scopes then bound the grant.
function assertReadOnlyGrant(server: Server, granted: string | undefined) {
  if (!READ_ONLY_SERVERS.has(server.name) || !granted) return;
  const extra = granted.split(/\s+/).filter((scope) => scope && !server.scopes.includes(scope));
  const write = granted.split(/\s+/).filter((scope) => scope && !scope.endsWith(":read"));
  if (extra.length || write.length)
    throw new Error(`${server.name}: grant exceeds read-only scopes (${[...extra, ...write].join(" ")}); not saved`);
}

// Same key Codex derives in rmcp-client/src/oauth.rs compute_store_key.
function codexAccount(server: Server) {
  const payload = JSON.stringify({ type: "http", url: server.url, headers: {} });
  return `${server.name}|${new Bun.CryptoHasher("sha256").update(payload).digest("hex").slice(0, 16)}`;
}

// --- keychain --------------------------------------------------------------

async function keychainRead(service: string, account: string): Promise<string | null> {
  const proc = Bun.spawn(["security", "find-generic-password", "-s", service, "-a", account, "-w"], {
    stdout: "pipe",
    stderr: "pipe",
  });
  const out = await new Response(proc.stdout).text();
  return (await proc.exited) === 0 ? out.trimEnd() : null;
}

// Writes through `security -i` on stdin so secrets never appear in argv.
async function keychainWrite(service: string, account: string, value: string) {
  const hex = Buffer.from(value).toString("hex");
  const proc = Bun.spawn(["security", "-i"], { stdin: "pipe", stdout: "pipe", stderr: "pipe" });
  proc.stdin.write(`add-generic-password -U -s "${service}" -a "${account}" -X ${hex}\n`);
  proc.stdin.end();
  const err = (await new Response(proc.stderr).text()).trim();
  if ((await proc.exited) !== 0 || err) throw new Error(`keychain write ${account} failed: ${err}`);
  if ((await keychainRead(service, account)) !== value) throw new Error(`keychain write ${account} did not persist`);
}

async function readJson<T>(service: string, account: string): Promise<T | null> {
  const raw = await keychainRead(service, account);
  return raw ? (JSON.parse(raw) as T) : null;
}

// --- oauth -----------------------------------------------------------------

function randomToken() {
  return Buffer.from(crypto.getRandomValues(new Uint8Array(32))).toString("base64url");
}

async function register(redirectUri: string, scopes: string[]): Promise<Client> {
  const res = await fetch(REGISTER_URL, {
    method: "POST",
    headers: { "content-type": "application/json", accept: "application/json" },
    body: JSON.stringify({
      client_name: "Codex",
      redirect_uris: [redirectUri],
      grant_types: ["authorization_code", "refresh_token"],
      response_types: ["code"],
      token_endpoint_auth_method: "client_secret_basic",
      ...(scopes.length ? { scope: scopes.join(" ") } : {}),
    }),
  });
  const body = (await res.json()) as Partial<Client>;
  if (!res.ok || !body.client_id || !body.client_secret)
    throw new Error(`client registration failed (${res.status})`);
  return { client_id: body.client_id, client_secret: body.client_secret };
}

async function tokenRequest(client: Client, params: Record<string, string>): Promise<TokenResponse> {
  const basic = btoa(`${encodeURIComponent(client.client_id)}:${encodeURIComponent(client.client_secret)}`);
  const res = await fetch(TOKEN_URL, {
    method: "POST",
    headers: {
      authorization: `Basic ${basic}`,
      "content-type": "application/x-www-form-urlencoded",
      accept: "application/json",
    },
    body: new URLSearchParams(params),
  });
  const text = await res.text();
  if (!res.ok) throw new Error(`token endpoint ${res.status}: ${text.slice(0, 300)}`);
  const token = JSON.parse(text) as Partial<TokenResponse>;
  if (!token.access_token || !token.token_type || typeof token.expires_in !== "number")
    throw new Error("token endpoint returned an incomplete response");
  return token as TokenResponse;
}

// Ours is written first: it holds the refresh token, the source of truth.
// Codex's entry gets no refresh token, so Codex can never rotate our chain.
async function save(server: Server, client: Client, token: TokenResponse, previous?: Managed) {
  const scope = token.scope ?? previous?.scope;
  assertReadOnlyGrant(server, scope);
  const refreshToken = token.refresh_token ?? previous?.refresh_token;
  if (!refreshToken) throw new Error(`${server.name}: no refresh token issued`);

  const managed: Managed = { ...client, refresh_token: refreshToken, ...(scope ? { scope } : {}) };
  await keychainWrite(OWN_SERVICE, server.name, JSON.stringify(managed));

  const codexEntry = {
    server_name: server.name,
    url: server.url,
    issuer: ISSUER,
    client_id: client.client_id,
    token_response: {
      access_token: token.access_token,
      token_type: token.token_type,
      expires_in: token.expires_in,
      ...(scope ? { scope } : {}),
    },
    expires_at: Date.now() + token.expires_in * 1000,
  };
  await keychainWrite(CODEX_SERVICE, codexAccount(server), JSON.stringify(codexEntry));
}

// --- commands --------------------------------------------------------------

async function login(name: string) {
  const server = await loadServer(name);
  const state = randomToken();
  const verifier = randomToken();
  const challenge = new Bun.CryptoHasher("sha256").update(verifier).digest("base64url");

  let settle: { resolve: (code: string) => void; reject: (err: Error) => void } | undefined;
  const codePromise = new Promise<string>((resolve, reject) => (settle = { resolve, reject }));
  const callback = Bun.serve({
    hostname: "127.0.0.1",
    port: 0,
    fetch(req) {
      const url = new URL(req.url);
      if (url.pathname !== "/callback") return new Response("not found", { status: 404 });
      const params = url.searchParams;
      if (params.get("error")) settle?.reject(new Error(`authorization denied: ${params.get("error")}`));
      else if (params.get("state") !== state) settle?.reject(new Error("state mismatch"));
      else if (params.get("iss") && params.get("iss") !== ISSUER) settle?.reject(new Error("issuer mismatch"));
      else if (!params.get("code")) settle?.reject(new Error("callback without code"));
      else settle?.resolve(params.get("code") as string);
      return new Response("codex-supabase-auth: done, you can close this tab.");
    },
  });

  try {
    const redirectUri = `http://127.0.0.1:${callback.port}/callback`;
    const client = await register(redirectUri, server.scopes);
    const authorize = new URL(AUTHORIZE_URL);
    authorize.search = new URLSearchParams({
      response_type: "code",
      client_id: client.client_id,
      redirect_uri: redirectUri,
      state,
      code_challenge: challenge,
      code_challenge_method: "S256",
      ...(server.scopes.length ? { scope: server.scopes.join(" ") } : {}),
    }).toString();

    console.log(`${server.name}: opening browser for consent.`);
    if (server.scopes.length) console.log(`requested scopes: ${server.scopes.join(" ")}`);
    console.log(`if it does not open, visit:\n${authorize}`);
    Bun.spawn(["open", authorize.toString()]);

    const timeout = setTimeout(() => settle?.reject(new Error("login timed out")), LOGIN_TIMEOUT_MS);
    const code = await codePromise.finally(() => clearTimeout(timeout));
    const token = await tokenRequest(client, {
      grant_type: "authorization_code",
      code,
      redirect_uri: redirectUri,
      code_verifier: verifier,
    });
    await save(server, client, token);
    console.log(`${server.name}: saved. granted scope: ${token.scope ?? "(not reported)"}`);
  } finally {
    callback.stop(true);
  }
}

async function refresh(name: string, force: boolean) {
  const server = await loadServer(name);
  const managed = await readJson<Managed>(OWN_SERVICE, server.name);
  if (!managed) {
    console.log(`${server.name}: not managed, run \`codex-supabase-auth login ${server.name}\``);
    return;
  }
  const codex = await readJson<CodexEntry>(CODEX_SERVICE, codexAccount(server));
  const ours = codex?.client_id === managed.client_id;
  const remaining = ours && codex?.expires_at ? codex.expires_at - Date.now() : 0;
  if (!force && remaining > REFRESH_WITHIN_MS) return;

  const token = await tokenRequest(managed, { grant_type: "refresh_token", refresh_token: managed.refresh_token });
  await save(server, managed, token, managed);
  console.log(`${new Date().toISOString()} ${server.name}: refreshed${ours ? "" : " (restored Codex entry)"}`);
}

async function status() {
  for (const name of SERVERS) {
    const server = await loadServer(name);
    const managed = await readJson<Managed>(OWN_SERVICE, name);
    const codex = await readJson<CodexEntry>(CODEX_SERVICE, codexAccount(server));
    const hours = codex?.expires_at ? ((codex.expires_at - Date.now()) / 3_600_000).toFixed(1) : "?";
    console.log(
      [
        `${name}:`,
        `managed=${managed ? "yes" : "no"}`,
        `codex_entry=${codex ? (codex.client_id === managed?.client_id ? "ours" : "codex-owned") : "missing"}`,
        `expires_in_h=${hours}`,
        `scope=${managed?.scope ?? "(not reported)"}`,
      ].join(" "),
    );
  }
}

function install() {
  mkdirSync(STATE_DIR, { recursive: true });
  const build = Bun.spawnSync(["bun", "build", "--compile", SOURCE, "--outfile", BINARY]);
  if (build.exitCode !== 0) throw new Error(`build failed: ${build.stderr.toString()}`);
  const plist = `<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>${LABEL}</string>
  <key>ProgramArguments</key>
  <array>
    <string>${BINARY}</string>
    <string>refresh</string>
  </array>
  <key>EnvironmentVariables</key>
  <dict>
    <key>HOME</key>
    <string>${homedir()}</string>
    <key>PATH</key>
    <string>/usr/bin:/bin</string>
  </dict>
  <key>RunAtLoad</key>
  <true/>
  <key>StartInterval</key>
  <integer>3600</integer>
  <key>StandardOutPath</key>
  <string>${STATE_DIR}/refresh.log</string>
  <key>StandardErrorPath</key>
  <string>${STATE_DIR}/refresh.log</string>
</dict>
</plist>
`;
  writeFileSync(PLIST, plist);
  const domain = `gui/${process.getuid?.()}`;
  Bun.spawnSync(["launchctl", "bootout", domain, PLIST]);
  const boot = Bun.spawnSync(["launchctl", "bootstrap", domain, PLIST]);
  if (boot.exitCode !== 0) throw new Error(`launchctl bootstrap failed: ${boot.stderr.toString()}`);
  console.log(`built ${BINARY}; installed ${PLIST}; log at ${STATE_DIR}/refresh.log`);
}

// Serializes runs: two concurrent refreshes would redeem one refresh token twice.
function withLock<T>(run: () => Promise<T>): Promise<T> {
  mkdirSync(STATE_DIR, { recursive: true });
  try {
    if (Date.now() - statSync(LOCK_DIR).mtimeMs > 10 * 60 * 1000) rmSync(LOCK_DIR, { recursive: true });
  } catch {
    // no lock present
  }
  try {
    mkdirSync(LOCK_DIR);
  } catch {
    throw new Error("another codex-supabase-auth run holds the lock");
  }
  return run().finally(() => rmSync(LOCK_DIR, { recursive: true, force: true }));
}

function notify(message: string) {
  const escaped = message.replaceAll("\\", "\\\\").replaceAll('"', '\\"');
  Bun.spawnSync(["osascript", "-e", `display notification "${escaped}" with title "codex-supabase-auth"`]);
}

async function main() {
  const [command, arg] = process.argv.slice(2);
  if (command === "login" && arg) return withLock(() => login(arg));
  if (command === "status") return status();
  if (command === "install") return install();
  if (command === "refresh") {
    return withLock(async () => {
      let failed = false;
      for (const name of SERVERS) {
        try {
          await refresh(name, arg === "--force");
        } catch (err) {
          failed = true;
          console.error(`${new Date().toISOString()} ${name}: refresh failed`, err);
          notify(`${name} refresh failed: ${err instanceof Error ? err.message : String(err)}`);
        }
      }
      if (failed) process.exitCode = 1;
    });
  }
  console.error("usage: codex-supabase-auth login <server> | refresh [--force] | status | install");
  process.exitCode = 2;
}

main().catch((err) => {
  console.error(err);
  process.exitCode = 1;
});
