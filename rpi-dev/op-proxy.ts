#!/usr/bin/env bun

import { spawnSync } from "node:child_process";
import { readdirSync, readFileSync } from "node:fs";
import { join, relative } from "node:path";
import { timingSafeEqual } from "node:crypto";

interface ProxyRequest {
  token?: unknown;
  argv?: unknown;
}

interface CommandResult {
  status: number;
  stdout: string;
  stderr: string;
}

function schemaFiles(root: string, directory = root): string[] {
  const files: string[] = [];

  for (const entry of readdirSync(directory, { withFileTypes: true })) {
    if (entry.name === "node_modules" || entry.name === ".git") {
      continue;
    }

    const path = join(directory, entry.name);
    if (entry.isDirectory()) {
      files.push(...schemaFiles(root, path));
    } else if (entry.isFile() && /^\.env.*\.schema$/.test(entry.name)) {
      files.push(relative(root, path));
    }
  }

  return files;
}

function allowedPairs(root: string): Set<string> {
  const pairs = new Set<string>();
  const pattern = /read-1password-env\.ts(?:\\?")?\s+([^\s;]+)\s+([^\s;)"]+)/g;

  for (const file of schemaFiles(root)) {
    const content = readFileSync(join(root, file), "utf8");
    for (const match of content.matchAll(pattern)) {
      const vault = match[1];
      const item = match[2];
      if (vault && item) {
        pairs.add(`${vault}:${item}`);
      }
    }
  }

  return pairs;
}

function isAllowed(argv: string[], pairs: Set<string>): boolean {
  if (argv.length !== 7) {
    return false;
  }

  const [resource, action, item, vaultFlag, vault, formatFlag, format] = argv;
  return (
    resource === "item" &&
    action === "get" &&
    typeof item === "string" &&
    vaultFlag === "--vault" &&
    typeof vault === "string" &&
    formatFlag === "--format" &&
    format === "json" &&
    pairs.has(`${vault}:${item}`)
  );
}

function tokenMatches(expected: string, received: unknown): boolean {
  if (typeof received !== "string") {
    return false;
  }

  const expectedBuffer = Buffer.from(expected);
  const receivedBuffer = Buffer.from(received);
  return expectedBuffer.length === receivedBuffer.length && timingSafeEqual(expectedBuffer, receivedBuffer);
}

function asRequest(value: unknown): ProxyRequest {
  return value && typeof value === "object" ? (value as ProxyRequest) : {};
}

function jsonResponse(status: number, body: CommandResult | Record<string, unknown>): Response {
  return Response.json(body, { status });
}

const token = process.env.OP_HOST_PROXY_TOKEN;
const host = process.env.OP_HOST_PROXY_HOST || "127.0.0.1";
const port = Number(process.env.OP_HOST_PROXY_PORT || "17691");
const opBin = process.env.OP_HOST_PROXY_OP_BIN || "op";
const repo = process.env.RPI_DEV_REPO;

if (!token) throw new Error("OP_HOST_PROXY_TOKEN is required");
if (!repo) throw new Error("RPI_DEV_REPO is required");
if (!Number.isInteger(port) || port <= 0 || port > 65_535) {
  throw new Error("OP_HOST_PROXY_PORT must be a valid TCP port");
}

const pairs = allowedPairs(repo);
if (pairs.size === 0) throw new Error(`no allowlisted 1Password items found under ${repo}`);

Bun.serve({
  hostname: host,
  port,
  async fetch(request: Request) {
    const url = new URL(request.url);
    if (request.method === "GET" && url.pathname === "/healthz") {
      return jsonResponse(200, { status: "ok", allowed_items: pairs.size });
    }

    if (request.method !== "POST" || url.pathname !== "/op") {
      return jsonResponse(404, { status: 1, stdout: "", stderr: "not found" });
    }

    const requestId = crypto.randomUUID().slice(0, 8);
    let body: ProxyRequest;
    try {
      body = asRequest(await request.json());
    } catch {
      return jsonResponse(400, { status: 1, stdout: "", stderr: "invalid JSON" });
    }

    if (!tokenMatches(token, body.token)) {
      console.error(`${new Date().toISOString()} request=${requestId} status=forbidden`);
      return jsonResponse(403, { status: 1, stdout: "", stderr: "forbidden" });
    }

    if (!Array.isArray(body.argv) || !body.argv.every((argument) => typeof argument === "string")) {
      return jsonResponse(400, { status: 1, stdout: "", stderr: "invalid argv" });
    }

    if (!isAllowed(body.argv, pairs)) {
      console.error(`${new Date().toISOString()} request=${requestId} status=not-allowed`);
      return jsonResponse(403, { status: 1, stdout: "", stderr: "op command not allowed" });
    }

    const result = spawnSync(opBin, body.argv, {
      encoding: "utf8",
      timeout: 120_000,
      maxBuffer: 10 * 1024 * 1024,
    });
    const status = result.status ?? 1;
    const timedOut = (result.error as NodeJS.ErrnoException | undefined)?.code === "ETIMEDOUT";
    const stderr = timedOut
      ? "1Password authorization timed out on the Mac; approve the biometric prompt and retry"
      : result.error?.message || result.stderr || "";
    console.error(
      `${new Date().toISOString()} request=${requestId} status=${timedOut ? "timeout" : status}`,
    );

    return jsonResponse(status === 0 ? 200 : timedOut ? 504 : 502, {
      status,
      stdout: result.stdout || "",
      stderr,
    });
  },
});

console.error(
  `${new Date().toISOString()} 1Password proxy listening on ${host}:${port} (${pairs.size} allowed items)`,
);
