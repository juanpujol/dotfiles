#!/usr/bin/env python3
"""Build a Markdown digest of one local day of agent work, grouped by project.

Usage: extract.py YYYY-MM-DD [--out FILE] [--tz Area/City]

Sources: Claude Code, Codex, pi, OpenCode transcripts; Claude and Codex
memories; git commits; GitHub PRs and issues; tsk tasks. Python stdlib only
(Codex .zst rollouts need the `zstd` binary; skipped without it).
"""

import argparse
import collections
import concurrent.futures
import datetime as dt
import glob
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import time
from zoneinfo import ZoneInfo

HOME = os.path.expanduser("~")
LOCAL_TZ = [None]  # set by Day
ASSISTANT_CAP = 1200
EVENT_CAP = 200

# ---------------------------------------------------------------- helpers

SECRET_PATTERNS = [
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----"), "[REDACTED PRIVATE KEY]"),
    (re.compile(r"\bsk-(?:ant-|proj-)?[A-Za-z0-9_\-]{16,}"), "[REDACTED]"),
    (re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}"), "[REDACTED]"),
    (re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}"), "[REDACTED]"),
    (re.compile(r"\bxox[abprs]-[A-Za-z0-9\-]{10,}"), "[REDACTED]"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "[REDACTED]"),
    (re.compile(r"\b(?:sb_secret|sb_publishable|phx|phc|rk_live|sk_live|pk_live)_[A-Za-z0-9_\-]{12,}"), "[REDACTED]"),
    (re.compile(r"\beyJ[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}"), "[REDACTED JWT]"),
    (re.compile(r"(?i)\b(bearer)\s+[A-Za-z0-9_\-\.=]{16,}"), r"\1 [REDACTED]"),
    (
        re.compile(
            r"(?i)\b([A-Z0-9_]*(?:password|passwd|pwd|secret|token|api[_-]?key|apikey|access[_-]?key|private[_-]?key|client[_-]?secret)[A-Z0-9_]*)"
            r"(\s*[=:]\s*)(\"[^\"\s]{4,}\"|'[^'\s]{4,}'|[^\s,;'\"`)\]}]{4,})"
        ),
        r"\1\2[REDACTED]",
    ),
    (re.compile(r"(://[^/\s:@]+:)[^@\s/]{3,}@"), r"\1[REDACTED]@"),
]


def redact(text):
    for pattern, repl in SECRET_PATTERNS:
        text = pattern.sub(repl, text)
    return text


SYSTEM_REMINDER = re.compile(r"<system-reminder>[\s\S]*?</system-reminder>", re.I)


def clean(text):
    return redact(SYSTEM_REMINDER.sub("", text or "")).strip()


def cap(text, limit):
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + f" [... {len(text) - limit} more chars]"


def parse_ts(value):
    """ISO string, epoch seconds or epoch ms -> aware datetime (UTC)."""
    if value is None:
        return None
    try:
        if isinstance(value, (int, float)):
            seconds = value / 1000 if value > 1e11 else value
            return dt.datetime.fromtimestamp(seconds, dt.timezone.utc)
        text = str(value)
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        parsed = dt.datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=dt.timezone.utc)
        return parsed
    except (ValueError, OSError, OverflowError):
        return None


def run(cmd, cwd=None, timeout=60):
    try:
        proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as err:
        return None, str(err)
    if proc.returncode != 0:
        return None, (proc.stderr or proc.stdout).strip()[:300]
    return proc.stdout, None


def indent(text):
    return text.replace("\n", "\n  ")


# ---------------------------------------------------------------- context


def system_zone():
    """IANA name of the system zone, from $TZ or /etc/localtime."""
    if os.environ.get("TZ") and "/" in os.environ["TZ"]:
        return os.environ["TZ"].lstrip(":")
    target = os.path.realpath("/etc/localtime")
    return target.split("zoneinfo/", 1)[1] if "zoneinfo/" in target else None


class Day:
    def __init__(self, date_str, tz_name):
        tz_name = tz_name or system_zone()
        self.tz = ZoneInfo(tz_name) if tz_name else dt.datetime.now().astimezone().tzinfo
        self.tz_label = tz_name or str(self.tz)
        LOCAL_TZ[0] = self.tz
        self.date = dt.date.fromisoformat(date_str)
        self.start = dt.datetime.combine(self.date, dt.time(0), self.tz)
        self.end = self.start + dt.timedelta(days=1)
        self.start_epoch = self.start.timestamp()
        self.end_epoch = self.end.timestamp()
        start_utc = self.start.astimezone(dt.timezone.utc)
        end_utc = (self.end - dt.timedelta(microseconds=1)).astimezone(dt.timezone.utc)
        self.utc_dates = sorted({start_utc.date().isoformat(), end_utc.date().isoformat()})

    def contains(self, moment):
        return moment is not None and self.start <= moment < self.end

    def hm(self, moment):
        return moment.astimezone(self.tz).strftime("%H:%M")

    def line_may_match(self, line):
        """Cheap prefilter for JSON lines carrying an ISO UTC timestamp."""
        return any(d in line for d in self.utc_dates)

    def touched(self, path):
        try:
            return os.path.getmtime(path) >= self.start_epoch
        except OSError:
            return False

    def modified_in_day(self, path):
        try:
            mtime = os.path.getmtime(path)
        except OSError:
            return False
        return self.start_epoch <= mtime < self.end_epoch


class Projects:
    """cwd -> project name (main repo basename for worktrees)."""

    def __init__(self):
        self.cache = {}

    def name(self, cwd):
        if not cwd:
            return "unknown"
        cwd = cwd.replace("file://", "").rstrip("/") or "/"
        if cwd in self.cache:
            return self.cache[cwd]
        result = self._resolve(cwd)
        self.cache[cwd] = result
        return result

    def _resolve(self, cwd):
        if os.path.realpath(cwd) == os.path.realpath(HOME):
            return "home"
        if re.match(r"^(/private)?/var/folders/", cwd) or cwd in ("/tmp", "/private/tmp"):
            return "tmp"
        if os.path.isdir(cwd):
            name = repo_name(cwd)
            if name:
                return name
        rel = cwd[len(HOME) + 1:] if cwd.startswith(HOME + "/") else None
        if rel:
            parts = rel.split("/")
            if parts[:2] == [".herdr", "worktrees"] and len(parts) >= 3:
                return parts[2]
            if parts[:2] == [".claude", "worktrees"] and len(parts) >= 3:
                return parts[2]
            if parts[:2] == [".codex", "worktrees"] and len(parts) >= 4:
                return parts[3]
            if parts[0] == "Code" and len(parts) >= 3 and parts[1].startswith("@"):
                return sibling_repo(os.path.join(HOME, "Code", parts[1]), parts[2])
            if parts[0] == "Code" and len(parts) >= 2:
                return parts[1]
            if parts[0] in ("dotfiles", ".dotfiles"):
                return "dotfiles"
            if parts[:2] == ["Vault", "agents"]:
                return "agents-vault"
        return os.path.basename(cwd) or cwd


def sibling_repo(org_dir, name):
    """Gone or non-git clone `laiki2-effect-web` -> sibling repo `laiki2` (longest `<repo>-` prefix)."""
    if os.path.exists(os.path.join(org_dir, name, ".git")):
        return name
    matches = [d for d in os.listdir(org_dir) if name.startswith(d + "-") and os.path.exists(os.path.join(org_dir, d, ".git"))] if os.path.isdir(org_dir) else []
    if not matches:
        return name
    best = max(matches, key=len)
    return repo_name(os.path.join(org_dir, best)) or best


def repo_name(path, common=None):
    """Repo name from the origin remote (laiki-co/laiki2 -> laiki2), else the git common dir."""
    out, _ = run(["git", "-C", path, "remote", "get-url", "origin"], timeout=10)
    if out and out.strip():
        base = re.split(r"[/:]", out.strip().rstrip("/"))[-1]
        base = base[:-4] if base.endswith(".git") else base
        if base:
            return base
    if common is None:
        out, _ = run(["git", "-C", path, "rev-parse", "--path-format=absolute", "--git-common-dir"], timeout=10)
        common = out.strip() if out else None
    return repo_name_from_common_dir(common) if common else None


def repo_name_from_common_dir(common):
    common = common.rstrip("/")
    if os.path.basename(common) == ".git":
        return os.path.basename(os.path.dirname(common))
    base = os.path.basename(common)
    return base[:-4] if base.endswith(".git") else base


class Session:
    def __init__(self, tool, sid, cwd):
        self.tool = tool
        self.sid = sid
        self.cwd = cwd
        self.branch = None
        self.title = None
        self.models = collections.Counter()
        self.tools = collections.Counter()
        self.messages = []  # (datetime, role, text)
        self.subagents = []  # (datetime, text)
        self.first = None
        self.last = None
        self.user_count = 0
        self.seen = {}

    def touch(self, moment):
        if self.first is None or moment < self.first:
            self.first = moment
        if self.last is None or moment > self.last:
            self.last = moment

    def add(self, moment, role, text):
        if not text:
            return
        self.touch(moment)
        if role in ("Juan", "User") and len(text) > 200:
            earlier = self.seen.get(text)
            if earlier:
                text = f"(same {len(text)}-char message as at {earlier})"
            else:
                self.seen[text] = moment.astimezone(LOCAL_TZ[0]).strftime("%H:%M")
        self.messages.append((moment, role, text))
        if role in ("Juan", "User"):
            self.user_count += 1

    @property
    def active(self):
        return self.first is not None


# ---------------------------------------------------------------- Claude Code

COMMAND_RE = re.compile(r"<command-name>\s*(.*?)\s*</command-name>[\s\S]*?(?:<command-args>([\s\S]*?)</command-args>)?", re.S)


def claude_user_text(entry):
    """Return (role, text) for a Claude user entry, or None to skip."""
    if entry.get("isMeta") or entry.get("isSidechain"):
        return None
    if entry.get("isCompactSummary"):
        return ("Event", "(context compacted)")
    if entry.get("toolUseResult") is not None:
        return None
    content = entry.get("message", {}).get("content")
    origin = entry.get("origin") or {}
    kind = origin.get("kind")
    if isinstance(content, list):
        if any(isinstance(b, dict) and b.get("type") == "tool_result" for b in content):
            return None
        pieces = []
        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "text":
                pieces.append(block.get("text", ""))
            elif block.get("type") == "image":
                pieces.append("[image]")
        text = "\n".join(pieces)
    elif isinstance(content, str):
        text = content
    else:
        return None
    text = clean(text)
    if not text:
        return None
    if kind == "task-notification" or text.startswith("<task-notification>"):
        summary = re.search(r"<summary>([\s\S]*?)</summary>", text)
        status = re.search(r"<status>([\s\S]*?)</status>", text)
        label = summary.group(1).strip() if summary else "background task update"
        return ("Event", f"(task notification: {label}{', ' + status.group(1).strip() if status else ''})")
    if kind == "peer":
        name = origin.get("name") or origin.get("from") or "peer"
        body = re.sub(r"\s+", " ", origin.get("body") or text)
        return ("Event", f"(message from {name}: {cap(body, EVENT_CAP)})")
    if text.startswith(("<local-command-stdout>", "<local-command-caveat>", "<local-command-stderr>", "<bash-stdout>", "<bash-stderr>")):
        return None
    match = COMMAND_RE.search(text)
    if match and text.lstrip().startswith(("<command-name>", "<command-message>")):
        args = (match.group(2) or "").strip()
        return ("Juan", f"{match.group(1)} {args}".strip())
    bash = re.match(r"<bash-input>([\s\S]*?)</bash-input>", text)
    if bash:
        return ("Juan", "! " + bash.group(1).strip())
    if text == "[Request interrupted by user]" or text.startswith("[Request interrupted by user"):
        return ("Event", "(Juan interrupted the agent)")
    return ("Juan", text)


def queued_message(entry):
    """Message Juan typed while Claude was busy: delivered mid-turn as a queued_command attachment.

    Returned as a synthetic user entry; None for other attachments.
    """
    attachment = entry.get("attachment") or {}
    if attachment.get("type") != "queued_command":
        return None
    origin = attachment.get("origin") or entry.get("origin") or {}
    if origin.get("kind") not in (None, "human"):
        return None
    prompt = attachment.get("prompt")
    if isinstance(prompt, list):
        prompt = "\n".join(b.get("text", "") for b in prompt if isinstance(b, dict) and b.get("type") == "text")
    if not isinstance(prompt, str) or prompt.lstrip().startswith(("<task-notification>", "<agent-message")):
        return None
    return {
        "type": "user",
        "timestamp": attachment.get("timestamp") or entry.get("timestamp"),
        "isSidechain": entry.get("isSidechain"),
        "sessionId": entry.get("sessionId"),
        "cwd": entry.get("cwd"),
        "gitBranch": entry.get("gitBranch"),
        "origin": {"kind": "human"},
        "message": {"content": prompt},
    }


def first_ts_in_file(path, day):
    try:
        with open(path, encoding="utf-8", errors="replace") as handle:
            for line in handle:
                if not day.line_may_match(line):
                    continue
                try:
                    moment = parse_ts(json.loads(line).get("timestamp"))
                except json.JSONDecodeError:
                    continue
                if day.contains(moment):
                    return moment
    except OSError:
        pass
    return None


def collect_claude(day, stats, errors):
    sessions = []
    files = [p for p in glob.glob(os.path.join(HOME, ".claude/projects/*/*.jsonl")) if day.touched(p)]
    for path in files:
        session = None
        last_user = None
        title = None
        try:
            handle = open(path, encoding="utf-8", errors="replace")
        except OSError as err:
            errors.append(f"claude {path}: {err}")
            continue
        with handle:
            for line in handle:
                if '"ai-title"' in line:
                    try:
                        title = json.loads(line).get("aiTitle") or title
                    except json.JSONDecodeError:
                        pass
                    continue
                if not day.line_may_match(line):
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                kind = entry.get("type")
                if kind == "attachment":
                    entry = queued_message(entry)
                    if entry is None:
                        continue
                    kind = "user"
                if kind not in ("user", "assistant"):
                    continue
                moment = parse_ts(entry.get("timestamp"))
                if not day.contains(moment) or entry.get("isSidechain"):
                    continue
                if session is None:
                    session = Session("Claude", entry.get("sessionId") or os.path.basename(path)[:-6], entry.get("cwd"))
                if not session.branch and entry.get("gitBranch") and entry.get("gitBranch") != "HEAD":
                    session.branch = entry.get("gitBranch")
                if kind == "user":
                    parsed = claude_user_text(entry)
                    if not parsed:
                        continue
                    role, text = parsed
                    if role == "Juan" and last_user is not None and last_user.split()[:1] == text.split()[:1] and text.startswith("/") and last_user.startswith("/"):
                        continue  # duplicate "/cmd" echo next to <command-name>
                    if role == "Juan":
                        last_user = text
                    session.add(moment, role, text)
                else:
                    message = entry.get("message") or {}
                    model = message.get("model")
                    if model and model != "<synthetic>":
                        session.models[model] += 1
                    session.touch(moment)
                    for block in message.get("content") or []:
                        if not isinstance(block, dict):
                            continue
                        if block.get("type") == "tool_use":
                            session.tools[block.get("name", "?")] += 1
                        elif block.get("type") == "text":
                            text = clean(block.get("text", ""))
                            if text and text != "No response requested.":
                                session.add(moment, "Agent", cap(text, ASSISTANT_CAP))
        if session is None or not session.active:
            continue
        session.title = title
        sub_dir = path[:-6] + "/subagents"
        for meta_path in sorted(glob.glob(os.path.join(sub_dir, "*.meta.json"))):
            log_path = meta_path[: -len(".meta.json")] + ".jsonl"
            if not day.touched(log_path):
                continue
            moment = first_ts_in_file(log_path, day)
            if moment is None:
                continue
            try:
                meta = json.load(open(meta_path))
            except (OSError, json.JSONDecodeError):
                meta = {}
            session.subagents.append((moment, f"{meta.get('agentType', 'subagent')}: {meta.get('description', '')}".strip()))
            stats["claude_subagents"] += 1
        sessions.append(session)
    stats["claude_sessions"] = len(sessions)
    return sessions


# ---------------------------------------------------------------- Codex

CODEX_INJECTED = ("# AGENTS.md instructions", "<environment_context>", "<user_instructions>", "<permissions instructions>", "<INSTRUCTIONS>", "<turn_aborted>", "<user_shell_command>")


def codex_lines(path, errors):
    if path.endswith(".zst"):
        if not shutil.which("zstd"):
            errors.append(f"codex {os.path.basename(path)}: zstd binary missing, skipped")
            return []
        out, err = run(["zstd", "-dcq", path], timeout=60)
        if out is None:
            errors.append(f"codex {os.path.basename(path)}: {err}")
            return []
        return out.splitlines()
    try:
        with open(path, encoding="utf-8", errors="replace") as handle:
            return handle.readlines()
    except OSError as err:
        errors.append(f"codex {path}: {err}")
        return []


def codex_user_text(text):
    text = clean(text)
    if not text or text.startswith(CODEX_INJECTED):
        return None
    beat = re.match(r"<heartbeat>[\s\S]*?<automation_id>(.*?)</automation_id>", text)
    if beat:
        return f"(heartbeat automation `{beat.group(1).strip()}` fired; prompt omitted)"
    skill = re.match(r"<skill>\s*<name>(.*?)</name>", text, re.S)
    if skill:
        return f"[skill loaded: {skill.group(1).strip()}]"
    return text


def collect_codex(day, stats, errors):
    root = os.path.join(HOME, ".codex/sessions")
    candidates = []
    for path in glob.glob(os.path.join(root, "*/*/*/rollout-*.jsonl*")):
        folder = path[len(root) + 1:].split("/")[:3]
        try:
            folder_date = dt.date(int(folder[0]), int(folder[1]), int(folder[2]))
        except ValueError:
            continue
        if folder_date <= day.date and day.touched(path):
            candidates.append(path)
    sessions = []
    by_thread = {}
    spawned = []
    for path in sorted(candidates):
        lines = codex_lines(path, errors)
        if not lines:
            continue
        try:
            meta = json.loads(lines[0]).get("payload", {})
        except json.JSONDecodeError:
            continue
        source = meta.get("source")
        source_text = json.dumps(source) if isinstance(source, dict) else str(source)
        if meta.get("thread_source") == "guardian_review" or '"guardian"' in source_text:
            stats["codex_guardian_skipped"] += 1
            continue
        session = Session("Codex", meta.get("id", os.path.basename(path)), meta.get("cwd"))
        session.branch = (meta.get("git") or {}).get("branch")
        effort = None
        used_items = False
        fallback = []
        for line in lines[1:]:
            if not day.line_may_match(line):
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            moment = parse_ts(entry.get("timestamp"))
            if not day.contains(moment):
                continue
            payload = entry.get("payload") or {}
            kind = entry.get("type")
            ptype = payload.get("type")
            if kind == "turn_context":
                if payload.get("model"):
                    session.models[payload["model"]] += 1
                effort = payload.get("effort") or effort
                session.touch(moment)
            elif kind == "event_msg" and ptype == "item_completed":
                item = payload.get("item") or {}
                itype = item.get("type")
                session.touch(moment)
                if itype == "UserMessage":
                    used_items = True
                    text = "\n".join(b.get("text", "") for b in item.get("content") or [] if isinstance(b, dict))
                    text = codex_user_text(text)
                    if text:
                        session.add(moment, "User", text)
                elif itype == "AgentMessage":
                    used_items = True
                    text = "\n".join(b.get("text", "") for b in item.get("content") or [] if isinstance(b, dict))
                    text = clean(text)
                    if text:
                        session.add(moment, "Agent", cap(text, ASSISTANT_CAP))
                elif itype == "CommandExecution":
                    session.tools["shell"] += 1
                elif itype == "FileChange":
                    session.tools["file_change"] += 1
                elif itype == "McpToolCall":
                    session.tools[f"mcp:{item.get('server')}.{item.get('tool')}"] += 1
                elif itype == "Extension":
                    session.tools[item.get("kind") or "extension"] += 1
                elif itype == "ImageView":
                    session.tools["view_image"] += 1
                elif itype == "SubAgentActivity" and item.get("kind") == "started":
                    session.tools["spawn_agent"] += 1
                elif itype == "ContextCompaction":
                    session.add(moment, "Event", "(context compacted)")
            elif kind == "event_msg" and ptype in ("user_message", "agent_message"):
                text = payload.get("message") or ""
                fallback.append((moment, "User" if ptype == "user_message" else "Agent", text))
            elif kind == "event_msg" and ptype == "turn_aborted":
                session.add(moment, "Event", "(turn aborted)")
            elif kind == "response_item" and ptype == "message" and payload.get("role") in ("user", "assistant"):
                text = "\n".join(b.get("text", "") for b in payload.get("content") or [] if isinstance(b, dict))
                fallback.append((moment, "User" if payload["role"] == "user" else "Agent", text))
            elif kind == "response_item" and ptype in ("function_call", "custom_tool_call", "local_shell_call"):
                session.tools[payload.get("name") or ptype] += 1
        if not used_items:
            for moment, role, text in fallback:
                text = codex_user_text(text) if role == "User" else clean(text)
                if text:
                    session.add(moment, role, text if role == "User" else cap(text, ASSISTANT_CAP))
        if not session.active:
            continue
        if effort and session.models:
            top = session.models.most_common(1)[0][0]
            session.models = collections.Counter({f"{top} ({effort})": 1})
        spawn = (source or {}).get("subagent", {}).get("thread_spawn") if isinstance(source, dict) else None
        if spawn:
            last_agent = next((t for _, r, t in reversed(session.messages) if r == "Agent"), "")
            label = spawn.get("agent_path") or spawn.get("agent_nickname") or "subagent"
            model = ", ".join(session.models) or "?"
            spawned.append((spawn.get("parent_thread_id"), session, f"{label} [{model}]: {cap(re.sub(r'\s+', ' ', last_agent), 300)}"))
            stats["codex_subagents"] += 1
            continue
        by_thread[session.sid] = session
        sessions.append(session)
    for parent_id, child, text in spawned:
        parent = by_thread.get(parent_id)
        if parent:
            parent.subagents.append((child.first, text))
        else:
            child.title = "subagent (parent not active this day)"
            sessions.append(child)
    stats["codex_sessions"] = len(sessions)
    return sessions


# ---------------------------------------------------------------- pi


def collect_pi(day, stats, errors):
    return collect_pi_format(day, stats, errors, "pi", [".pi/agent/sessions"])


def collect_omp(day, stats, errors):
    """oh-my-pi: same session format as pi."""
    return collect_pi_format(day, stats, errors, "omp", [".local/share/omp/sessions", ".omp/agent/sessions"])


def collect_pi_format(day, stats, errors, label, roots):
    sessions = []
    nested = []
    paths = [p for root in roots for p in glob.glob(os.path.join(HOME, root, "**/*.jsonl"), recursive=True)]
    for path in paths:
        if not day.touched(path):
            continue
        session = None
        try:
            handle = open(path, encoding="utf-8", errors="replace")
        except OSError as err:
            errors.append(f"{label} {path}: {err}")
            continue
        with handle:
            for line in handle:
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if entry.get("type") == "session":
                    session = Session(label, entry.get("id", os.path.basename(path)), entry.get("cwd"))
                    continue
                if session is None:
                    session = Session(label, os.path.basename(path), None)
                if entry.get("type") == "session_info" and entry.get("name"):
                    session.title = entry["name"]
                moment = parse_ts(entry.get("timestamp"))
                if not day.contains(moment):
                    continue
                if entry.get("type") == "model_change" and entry.get("modelId"):
                    session.models[entry["modelId"]] += 0
                if entry.get("type") != "message":
                    continue
                message = entry.get("message") or {}
                role = message.get("role")
                content = message.get("content")
                if role == "assistant" and message.get("model"):
                    session.models[message["model"]] += 1
                if role not in ("user", "assistant"):
                    continue
                blocks = content if isinstance(content, list) else [{"type": "text", "text": content or ""}]
                texts = []
                for block in blocks:
                    if not isinstance(block, dict):
                        continue
                    if block.get("type") == "text":
                        texts.append(block.get("text", ""))
                    elif block.get("type") == "toolCall":
                        session.tools[block.get("name", "?")] += 1
                    elif block.get("type") == "image":
                        texts.append("[image]")
                text = clean("\n".join(texts))
                session.touch(moment)
                if text:
                    session.add(moment, "User" if role == "user" else "Agent", text if role == "user" else cap(text, ASSISTANT_CAP))
        if session and session.active:
            session.models = +session.models or collections.Counter({m: 1 for m in session.models})
            parent_log = os.path.dirname(path) + ".jsonl"
            if os.path.exists(parent_log):  # subagent log inside its parent session folder
                nested.append((parent_log, path, session))
            else:
                session.path = path
                sessions.append(session)
    by_path = {getattr(s, "path", None): s for s in sessions}
    for parent_log, path, child in nested:
        last_agent = next((t for _, r, t in reversed(child.messages) if r == "Agent"), "")
        model = ", ".join(child.models) or "?"
        text = f"{os.path.basename(path)[:-6]} [{model}]: {cap(re.sub(r'\s+', ' ', last_agent), 300)}"
        parent = by_path.get(parent_log)
        if parent:
            parent.subagents.append((child.first, text))
            stats[f"{label}_subagents"] += 1
        else:
            child.title = child.title or f"subagent {os.path.basename(path)[:-6]} (parent not active this day)"
            sessions.append(child)
    stats[f"{label}_sessions"] = len(sessions)
    return sessions


# ---------------------------------------------------------------- OpenCode


def collect_opencode(day, stats, errors):
    base = os.path.join(HOME, ".local/share/opencode")
    db_path = os.path.join(base, "opencode.db")
    sessions = []
    legacy = [p for p in glob.glob(os.path.join(base, "storage/session/**/*.json"), recursive=True) if day.modified_in_day(p)]
    if legacy:
        errors.append(f"opencode: {len(legacy)} legacy storage/ session files modified this day, not parsed")
    if not os.path.exists(db_path):
        return sessions
    if not day.touched(db_path) and not day.touched(db_path + "-wal"):
        return sessions
    start_ms, end_ms = int(day.start_epoch * 1000), int(day.end_epoch * 1000)
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=5)
    except sqlite3.Error as err:
        errors.append(f"opencode db: {err}")
        return sessions
    children = []
    try:
        tables = {r[0] for r in conn.execute("select name from sqlite_master where type='table'")}
        found = {}
        if "session_message" in tables and "session_v2" in tables:
            rows = conn.execute(
                "select m.session_id, m.type, m.time_created, m.data, s.directory, s.title, s.parent_id "
                "from session_message m join session_v2 s on s.id = m.session_id "
                "where m.time_created >= ? and m.time_created < ? order by m.time_created",
                (start_ms, end_ms),
            )
            for sid, mtype, created, data, directory, title, parent in rows:
                session = found.get(sid)
                if session is None:
                    session = found[sid] = Session("OpenCode", sid, directory)
                    session.title = title
                    session.parent = parent
                moment = parse_ts(created)
                try:
                    body = json.loads(data)
                except json.JSONDecodeError:
                    continue
                session.touch(moment)
                if mtype == "user":
                    text = clean(body.get("text", ""))
                    session.add(moment, "User", text)
                elif mtype == "assistant":
                    model = (body.get("model") or {}).get("id")
                    if model:
                        session.models[model] += 1
                    texts = []
                    for block in body.get("content") or []:
                        if block.get("type") == "tool":
                            session.tools[block.get("name", "?")] += 1
                        elif block.get("type") == "text":
                            texts.append(block.get("text", ""))
                    text = clean("\n".join(texts))
                    if text:
                        session.add(moment, "Agent", cap(text, ASSISTANT_CAP))
        if "session" in tables and "message" in tables and "part" in tables:
            old = conn.execute(
                "select id, directory, title, parent_id from session where time_updated >= ? and time_created < ?",
                (start_ms, end_ms),
            ).fetchall()
            for sid, directory, title, parent in old:
                if sid in found:
                    continue
                session = Session("OpenCode", sid, directory)
                session.title, session.parent = title, parent
                msgs = conn.execute(
                    "select id, time_created, data from message where session_id = ? and time_created >= ? and time_created < ? order by time_created",
                    (sid, start_ms, end_ms),
                ).fetchall()
                for mid, created, data in msgs:
                    moment = parse_ts(created)
                    try:
                        info = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    role = info.get("role")
                    if info.get("modelID") and role == "assistant":
                        session.models[info["modelID"]] += 1
                    texts = []
                    for (pdata,) in conn.execute("select data from part where message_id = ? order by id", (mid,)):
                        try:
                            part = json.loads(pdata)
                        except json.JSONDecodeError:
                            continue
                        if part.get("type") == "text" and not part.get("synthetic"):
                            texts.append(part.get("text", ""))
                        elif part.get("type") == "tool":
                            session.tools[part.get("tool", "?")] += 1
                    session.touch(moment)
                    text = clean("\n".join(texts))
                    if text:
                        session.add(moment, "User" if role == "user" else "Agent", text if role == "user" else cap(text, ASSISTANT_CAP))
                if session.active:
                    found[sid] = session
        for sid, session in found.items():
            if not session.active:
                continue
            if getattr(session, "parent", None) and session.parent in found:
                children.append(session)
            else:
                sessions.append(session)
        for child in children:
            parent = found[child.parent]
            last_agent = next((t for _, r, t in reversed(child.messages) if r == "Agent"), "")
            parent.subagents.append((child.first, f"{child.title or 'subagent'}: {cap(re.sub(r'\s+', ' ', last_agent), 300)}"))
            stats["opencode_subagents"] += 1
    except sqlite3.Error as err:
        errors.append(f"opencode db query: {err}")
    finally:
        conn.close()
    stats["opencode_sessions"] = len(sessions)
    return sessions


# ---------------------------------------------------------------- memories


def frontmatter(path):
    fields = {}
    try:
        with open(path, encoding="utf-8", errors="replace") as handle:
            lines = handle.read(4000).splitlines()
    except OSError:
        return fields, ""
    body_start = 0
    if lines and lines[0].strip() == "---":
        for i, line in enumerate(lines[1:], 1):
            if line.strip() == "---":
                body_start = i + 1
                break
            if ":" in line and not line.startswith(" "):
                key, value = line.split(":", 1)
                fields[key.strip()] = value.strip().strip('"')
    first = next((l.strip() for l in lines[body_start:] if l.strip()), "")
    return fields, first


def collect_memories(day, projects, stats):
    claude = []
    for path in glob.glob(os.path.join(HOME, ".claude/projects/*/memory/*.md")):
        if not day.modified_in_day(path):
            continue
        folder = path.split("/memory/")[0]
        project = memory_project(folder, projects)
        fields, first = frontmatter(path)
        claude.append((project, os.path.basename(path), redact(fields.get("description") or first)))
    codex = []
    for path in glob.glob(os.path.join(HOME, ".codex/memories/**/*"), recursive=True):
        if os.path.isfile(path) and day.modified_in_day(path):
            fields, first = frontmatter(path)
            codex.append((os.path.relpath(path, os.path.join(HOME, ".codex/memories")), redact(fields.get("description") or first)))
    stats["claude_memories"] = len(claude)
    stats["codex_memories"] = len(codex)
    return sorted(claude), sorted(codex)


def memory_project(folder, projects):
    for path in glob.glob(os.path.join(folder, "*.jsonl"))[:3]:
        try:
            with open(path, encoding="utf-8", errors="replace") as handle:
                for _, line in zip(range(50), handle):
                    cwd = json.loads(line).get("cwd")
                    if cwd:
                        return projects.name(cwd)
        except (OSError, json.JSONDecodeError):
            continue
    return os.path.basename(folder)


# ---------------------------------------------------------------- git


def git_repos():
    roots = set()
    code = os.path.join(HOME, "Code")
    for dirpath, dirnames, _ in os.walk(code):
        depth = dirpath[len(code):].count(os.sep)
        if ".git" in dirnames or os.path.isfile(os.path.join(dirpath, ".git")):
            roots.add(dirpath)
        dirnames[:] = [d for d in dirnames if d not in (".git", "node_modules") and not d.startswith(".")] if depth < 3 else []
    for extra in (os.path.join(HOME, "dotfiles"), os.path.join(HOME, "Vault/agents")):
        if os.path.exists(os.path.join(extra, ".git")):
            roots.add(extra)
    roots.update(p for p in glob.glob(os.path.join(HOME, ".herdr/worktrees/*/*")) if os.path.exists(os.path.join(p, ".git")))
    return sorted(roots)


def collect_git(day, stats, errors):
    common = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(run, ["git", "-C", r, "rev-parse", "--path-format=absolute", "--git-common-dir"], None, 15): r for r in git_repos()}
        for future in concurrent.futures.as_completed(futures):
            out, _ = future.result()
            if out:
                common.setdefault(out.strip(), futures[future])
    since = (day.start - dt.timedelta(days=2)).isoformat()
    fmt = "%H%x1f%aI%x1f%an%x1f%s%x1f%D"

    def log(item):
        common_dir, repo = item
        out, err = run(["git", "-C", repo, "log", "--all", f"--since={since}", f"--format={fmt}"], timeout=60)
        return common_dir, repo_name(repo, common_dir), out, err

    commits = collections.defaultdict(dict)
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        for common_dir, name, out, err in pool.map(log, common.items()):
            if out is None:
                if err and "does not have any commits" not in err:
                    errors.append(f"git {common_dir}: {err}")
                continue
            for line in out.splitlines():
                parts = line.split("\x1f")
                if len(parts) < 5:
                    continue
                sha, author_date, author, subject, refs = parts
                moment = parse_ts(author_date)
                if day.contains(moment):
                    commits[name][sha] = (moment, sha[:8], author, redact(subject), refs)
    result = {name: sorted(items.values()) for name, items in commits.items()}
    stats["git_commits"] = sum(len(v) for v in result.values())
    stats["git_repos_scanned"] = len(common)
    return result


# ---------------------------------------------------------------- GitHub


def collect_github(day, stats, errors):
    if not shutil.which("gh"):
        errors.append("github: gh not installed")
        return {}
    found = collections.defaultdict(list)
    for kind, fields in (("prs", "number,title,state,repository,url,updatedAt,createdAt,closedAt,isDraft"), ("issues", "number,title,state,repository,url,updatedAt,createdAt,closedAt")):
        out, err = run(["gh", "search", kind, "--author", "@me", "--updated", day.date.isoformat(), "--limit", "100", "--json", fields], timeout=60)
        if out is None:
            errors.append(f"github {kind}: {err}")
            continue
        try:
            rows = json.loads(out)
        except json.JSONDecodeError as err:
            errors.append(f"github {kind}: {err}")
            continue
        for row in rows:
            repo = (row.get("repository") or {}).get("name") or "unknown"
            created = parse_ts(row.get("createdAt"))
            closed = parse_ts(row.get("closedAt"))
            notes = []
            if day.contains(created):
                notes.append("created")
            if day.contains(closed):
                notes.append("closed/merged")
            state = row.get("state", "")
            if row.get("isDraft"):
                state += ", draft"
            found[repo].append(f"{'PR' if kind == 'prs' else 'Issue'} #{row.get('number')} [{state}{'; ' + ', '.join(notes) if notes else ''}] {redact(row.get('title', ''))} ({row.get('url')})")
        stats[f"github_{kind}"] = len(rows)
    return found


# ---------------------------------------------------------------- tsk


def tsk_project_path(scope):
    """Project path from a tsk scope of any shape ("global", {"project": {"path": ...}}, null)."""
    if not isinstance(scope, dict):
        return None
    project = scope.get("project")
    if isinstance(project, dict):
        path = project.get("path")
        return path if isinstance(path, str) else None
    return project if isinstance(project, str) else None


def collect_tsk(day, projects, stats, errors):
    store = os.path.join(HOME, ".tsk/tsk.json")
    found = collections.defaultdict(list)
    if os.path.exists(store):
        try:
            data = json.load(open(store))
        except (OSError, json.JSONDecodeError) as err:
            errors.append(f"tsk store: {err}")
            data = None
        if data:
            for task in data.get("tasks", []):
                events = []
                for event in task.get("history") or []:
                    at = event.get("at")
                    moment = parse_ts(at[0] + at[1] / 1e9 if isinstance(at, list) else at)
                    if day.contains(moment):
                        events.append(f"{event.get('kind')} {day.hm(moment)}")
                if not events:
                    continue
                path = tsk_project_path(task.get("scope"))
                project = projects.name(path) if path else "desk"
                steps = task.get("steps") or []
                done = sum(1 for s in steps if s.get("done"))
                notes = cap(redact(task.get("notes") or ""), 1000)
                kinds = collections.Counter(e.split()[0] for e in events)
                summary = ", ".join(f"{k} x{v}" if v > 1 else k for k, v in kinds.items())
                line = f"T{task.get('number')} [{task.get('status')}{', archived' if task.get('archived') else ''}] {redact(task.get('title', ''))} (thread {task.get('thread') or '-'}; steps {done}/{len(steps)}; events: {summary}; first {events[0].split()[-1]}, last {events[-1].split()[-1]})"
                if notes:
                    line += "\n  Notes: " + indent(notes)
                found[project].append(line)
            stats["tsk_tasks"] = sum(len(v) for v in found.values())
            return found
    if not shutil.which("tsk"):
        return found
    for flag in ("--all", "--done"):
        out, err = run(["tsk", "list", "--all", "--json"] + ([flag] if flag != "--all" else []), timeout=30)
        if out is None:
            errors.append(f"tsk {flag}: {err}")
            continue
        for task in json.loads(out or "[]"):
            project = projects.name(task.get("project")) if task.get("project") else "desk"
            found[project].append(f"T{task.get('number')} [{task.get('status')}] {task.get('title')} (no timestamps in CLI output; may not be from this day)")
    stats["tsk_tasks"] = sum(len(v) for v in found.values())
    return found


# ---------------------------------------------------------------- render


BATCH_MIN = 6
# Automated runs in temp dirs, attributed by session title prefix.
TMP_TITLE_PROJECTS = {"Laiki MCP eval": "laiki2"}


def session_project(session, projects):
    name = projects.name(session.cwd)
    if name == "tmp" and session.title:
        for prefix, project in TMP_TITLE_PROJECTS.items():
            if session.title.startswith(prefix):
                return project
    return name


def batch_sessions(group):
    """Collapse runs of near-identical automated sessions (same title modulo ids)."""
    keyed = collections.defaultdict(list)
    for session in group:
        if session.title and session.user_count <= 2:
            key = re.sub(r"[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}|\b[0-9a-f]{7,}\b|\d+", "<id>", session.title)
            keyed[key].append(session)
    batched = {k: v for k, v in keyed.items() if len(v) >= BATCH_MIN}
    ids = {id(s) for v in batched.values() for s in v}
    return [s for s in group if id(s) not in ids], sorted(batched.items(), key=lambda kv: kv[1][0].first)


def render(day, sessions, memories, commits, github, tasks, stats, errors, projects, elapsed):
    by_project = collections.defaultdict(list)
    for session in sessions:
        by_project[session_project(session, projects)].append(session)
    names = set(by_project) | set(commits) | set(github) | set(tasks) | {m[0] for m in memories[0]}
    split = {n: batch_sessions(sorted(by_project.get(n, []), key=lambda s: s.first)) for n in names}
    weight = lambda n: (-(sum(s.user_count for s in split[n][0]) * 5 + len(split[n][0]) + len(commits.get(n, []))), n)
    ordered = sorted(names, key=weight)

    out = [f"# Agent work digest: {day.date.isoformat()} ({day.date.strftime('%a')})", ""]
    out.append(f"Window: {day.start.isoformat()} to {day.end.isoformat()} ({day.tz_label}). Generated in {elapsed:.1f}s.")
    out.append("Roles: `Juan` = typed by Juan in Claude Code; `User` = the user turn in Codex, pi, omp, OpenCode (often an orchestrator brief sent through herdr, check the wording); `Agent` = visible assistant text, capped at "
               f"{ASSISTANT_CAP} chars; `Event` = harness events. Secrets are redacted; never copy anything that looks like a credential.")
    out.append("")
    out.append("## Coverage")
    labels = [
        ("Claude sessions", "claude_sessions"), ("Claude subagents (one line each)", "claude_subagents"),
        ("Codex sessions", "codex_sessions"), ("Codex subagents (one line each)", "codex_subagents"), ("Codex guardian reviews skipped", "codex_guardian_skipped"),
        ("pi sessions", "pi_sessions"), ("omp sessions", "omp_sessions"), ("omp subagents (one line each)", "omp_subagents"), ("OpenCode sessions", "opencode_sessions"), ("OpenCode subagents", "opencode_subagents"),
        ("Claude memories changed", "claude_memories"), ("Codex memories changed", "codex_memories"),
        ("Git commits", "git_commits"), ("Git repos scanned", "git_repos_scanned"),
        ("GitHub PRs (author @me, updated)", "github_prs"), ("GitHub issues (author @me, updated)", "github_issues"),
        ("tsk tasks touched", "tsk_tasks"),
    ]
    for label, key in labels:
        out.append(f"- {label}: {stats.get(key, 0)}")
    out.append("")
    out.append("| Project | Sessions | User msgs | Agent msgs | Commits | GitHub | tsk |")
    out.append("| --- | --- | --- | --- | --- | --- | --- |")
    for name in ordered:
        group = by_project.get(name, [])
        agent_msgs = sum(1 for s in group for m in s.messages if m[1] == "Agent")
        out.append(f"| {name} | {len(group)} | {sum(s.user_count for s in group)} | {agent_msgs} | {len(commits.get(name, []))} | {len(github.get(name, []))} | {len(tasks.get(name, []))} |")
    if errors:
        out.append("")
        out.append("Problems while reading sources:")
        out.extend(f"- {redact(e)}" for e in errors[:40])
        if len(errors) > 40:
            out.append(f"- ... {len(errors) - 40} more")
    claude_mem, codex_mem = memories
    if codex_mem:
        out += ["", "## Codex memories changed"]
        out.extend(f"- `{name}`: {desc}" for name, desc in codex_mem)

    for name in ordered:
        out += ["", f"# Project: {name}"]
        if commits.get(name):
            out += ["", f"## Git commits ({len(commits[name])})"]
            for moment, sha, author, subject, refs in commits[name]:
                out.append(f"- {day.hm(moment)} `{sha}` {subject} ({author}{'; ' + refs if refs else ''})")
        if github.get(name):
            out += ["", "## GitHub"]
            out.extend(f"- {row}" for row in github[name])
        if tasks.get(name):
            out += ["", "## tsk"]
            out.extend(f"- {row}" for row in tasks[name])
        mems = [m for m in claude_mem if m[0] == name]
        if mems:
            out += ["", "## Claude memories changed"]
            out.extend(f"- `{fname}`: {desc}" for _, fname, desc in mems)
        group, batches = split[name]
        if batches:
            out += ["", "## Automated session batches (collapsed)"]
            for title, items in batches:
                models = collections.Counter(m for s in items for m in s.models)
                samples = []
                for s in items:
                    first_user = next((t for _, r, t in s.messages if r in ("User", "Juan")), None)
                    if first_user and first_user not in samples:
                        samples.append(first_user)
                out.append(f"- {len(items)} {items[0].tool} sessions titled \"{redact(title)}\", {day.hm(items[0].first)}-{day.hm(max(s.last for s in items))}, models {', '.join(m for m, _ in models.most_common(3)) or '?'}; tools {sum(sum(s.tools.values()) for s in items)} calls. Sample prompts:")
                out.extend(f"  - {cap(re.sub(r'\s+', ' ', t), 300)}" for t in samples[:3])
        if group:
            out += ["", f"## Sessions ({len(group)})"]
        for session in group:
            where = os.path.basename((session.cwd or "").rstrip("/")) or "?"
            head = f"### {session.tool} {day.hm(session.first)}-{day.hm(session.last)} · {where}"
            if session.branch:
                head += f" (branch {session.branch})"
            out += ["", head]
            meta = [f"session `{session.sid}`", f"cwd `{session.cwd}`"]
            if session.models:
                meta.append("model " + ", ".join(m for m, _ in session.models.most_common(3)))
            if session.title:
                meta.append(f"title \"{redact(session.title)}\"")
            out.append("- " + "; ".join(meta))
            if session.tools:
                out.append("- Tools: " + ", ".join(f"{t} {c}" for t, c in session.tools.most_common()))
            for moment, text in sorted(session.subagents, key=lambda x: x[0]):
                out.append(f"- Subagent {day.hm(moment)}: {redact(text)}")
            if not session.user_count:
                out.append("- No user messages this day.")
            out.append("")
            for moment, role, text in sorted(session.messages, key=lambda m: m[0]):
                out.append(f"- [{day.hm(moment)}] {role}: {indent(text)}")
    out.append("")
    return "\n".join(out)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("date", nargs="?", default=None, help="YYYY-MM-DD (default: today)")
    parser.add_argument("--out", help="write the digest here (default: stdout)")
    parser.add_argument("--tz", default=os.environ.get("JOURNAL_TZ"), help="IANA zone (default: system local time)")
    args = parser.parse_args()
    started = time.time()
    date_str = args.date or dt.date.today().isoformat()
    try:
        day = Day(date_str, args.tz)
    except ValueError as err:
        sys.exit(f"bad date {date_str!r}: {err}")
    stats = collections.Counter()
    errors = []
    projects = Projects()

    def guarded(collector, fallback, *extra):
        """Run one source reader; a failure becomes a Coverage warning, not a crash."""
        try:
            return collector(day, *extra)
        except Exception as err:  # keep other sources if one format changes
            errors.append(f"WARNING {collector.__name__} failed, source skipped: {type(err).__name__}: {err}")
            return fallback

    sessions = []
    for collector in (collect_claude, collect_codex, collect_pi, collect_omp, collect_opencode):
        sessions += guarded(collector, [], stats, errors)
    memories = guarded(collect_memories, ([], []), projects, stats)
    commits = guarded(collect_git, {}, stats, errors)
    github = guarded(collect_github, {}, stats, errors)
    tasks = guarded(collect_tsk, {}, projects, stats, errors)

    text = render(day, sessions, memories, commits, github, tasks, stats, errors, projects, time.time() - started)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write(text)
        size = len(text.encode("utf-8"))
        print(f"wrote {args.out}: {size} bytes, {text.count(chr(10))} lines, {time.time() - started:.1f}s", file=sys.stderr)
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
