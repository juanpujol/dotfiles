// Key commands keys.json and the prefix popup send as "shortcuts.<command>".
// It lives in an invisible kept window so it is always loaded: mods only get commands while shown.
import { View, div } from "gpui-kit";
import { agents, focused, panes, spaces, hc, run, nextCommand, openOverlay } from "herdr";

const VIM_KEYS = { left: "ctrl+h", down: "ctrl+j", up: "ctrl+k", right: "ctrl+l" };
// Same matcher as vim-tmux-navigator: vi, vim, nvim, view, vimdiff, ...
const VIM = /^g?(view|l?n?vim?x?)(diff)?$/;
const URGENCY = { blocked: 2, done: 1 };

// ctrl+hjkl: Vim's splits when the focused pane runs Vim, else Herdr's panes.
// At a Vim edge split, nvim/lua/config/keymaps.lua hands focus back with pane.go.
async function navigate(dir) {
  const f = focused();
  const pane = panes().find((p) => p.pane === f?.pane);
  if (f?.terminal && VIM.test(pane?.program.key ?? "")) await hc(["keys", f.terminal, VIM_KEYS[dir]]);
  else run("pane.go", { direction: dir });
}

function cyclePane(step) {
  const f = focused();
  const list = panes().filter((p) => p.tab === f?.tab);
  const at = list.findIndex((p) => p.pane === f?.pane);
  const next = list[(at + step + list.length) % list.length];
  if (next) run("pane.focus", { pane: next.pane });
}

// The agent that needs you most: blocked before done, newest first.
function attention() {
  const [agent] = agents()
    .filter((a) => URGENCY[a.status])
    .sort((x, y) => URGENCY[y.status] - URGENCY[x.status] || y.seq - x.seq);
  if (agent) run("agent.focus", { terminal: agent.address });
}

// A shell script in a 95% popup terminal that closes when the script ends.
async function popup(script, args, { cwd, machine } = {}) {
  const argv = ["run", "--bg", "--json", "--rm", "--no-parent"];
  if (machine) argv.push("--on", machine);
  if (cwd) argv.push("--cwd", cwd);
  argv.push("--", "sh", "-c", `PATH="$HOME/.local/bin:$PATH"; ${script}`, "sh", ...args);
  try {
    const r = await hc(argv);
    const { address } = JSON.parse(r.stdout);
    const layout = { type: "block", content: { terminal: address } };
    openOverlay({ kind: "dialog", width: 0.95, height: 0.95, layout });
    run("pane.focus", { terminal: address });
  } catch (err) {
    console.error(err);
  }
}

function lazygit() {
  const f = focused();
  const machine = spaces().find((s) => s.id === f?.space)?.machine;
  popup("exec lazygit", [], { cwd: f?.cwd ?? undefined, machine });
}

function scrollback() {
  const t = focused()?.terminal;
  if (!t) return;
  popup('f=$(mktemp -t herdr-scrollback); hc read "$1" > "$f"; exec ${EDITOR:-nvim} + "$f"', [t]);
}

function worktree(action, width, height) {
  const f = focused();
  openOverlay({ mod: "worktree", kind: "dialog", width, height, props: { space: f?.space, folder: f?.cwd, action } });
}

const COMMANDS = {
  left: () => navigate("left"),
  down: () => navigate("down"),
  up: () => navigate("up"),
  right: () => navigate("right"),
  // Create, then ask for the name (no name argument makes Herdr prompt the person).
  "new-tab": () => {
    run("tab.new");
    run("tab.rename");
  },
  "new-space": () => {
    run("space.new");
    run("space.rename");
  },
  "next-pane": () => cyclePane(1),
  "prev-pane": () => cyclePane(-1),
  attention,
  scrollback,
  lazygit,
  "new-worktree": () => worktree("new", 460, 280),
  "remove-worktree": () => worktree("remove", 440, 260),
  "send-prefix": () => {
    const t = focused()?.terminal;
    if (t) hc(["keys", t, "ctrl+a"]);
  },
};

export default class Shortcuts extends View {
  init(_props, cx) {
    cx.spawn(async () => {
      for (;;) {
        const command = await nextCommand();
        try {
          await COMMANDS[command]?.();
        } catch (err) {
          console.error(err);
        }
      }
    });
  }

  render() {
    return div();
  }
}
