// tmux-style ctrl+a prefix: keys.json opens this popup on ctrl-a and the next key runs an action.
// Herdr's default prefix map plus the old config's w, a, g and ctrl-d. Pane focus is ctrl+hjkl, not here.
import { View, div } from "gpui-kit";
import { v_flex, h_flex } from "gpui-base";
import { run, props, closeOverlay, theme } from "herdr";

const go = (name, args) => () => run(name, args);
const mine = (command) => () => run(`shortcuts.${command}`);

// [key, hint, action]
const BINDS = [
  ["v", "split vertical", go("pane.split", { direction: "right" })],
  ["-", "split horizontal", go("pane.split", { direction: "down" })],
  ["x", "close pane", go("pane.close")],
  ["z", "zoom pane", go("pane.zoom")],
  ["tab", "next pane", mine("next-pane")],
  ["shift-tab", "previous pane", mine("prev-pane")],
  ["c", "new tab", mine("new-tab")],
  ["n", "next tab", go("tab.next")],
  ["p", "previous tab", go("tab.prev")],
  ["1-9", "select tab", null],
  ["shift-t", "rename tab", go("tab.rename")],
  ["shift-x", "close tab", go("tab.close")],
  ["shift-n", "new space", mine("new-space")],
  ["shift-w", "rename space", go("space.rename")],
  ["shift-d", "close space", go("space.close")],
  ["shift-g", "new worktree", mine("new-worktree")],
  ["ctrl-d", "remove worktree", mine("remove-worktree")],
  ["w", "go to", go("mod.open", { name: "picker" })],
  ["o", "agent needing you", mine("attention")],
  ["g", "lazygit", mine("lazygit")],
  ["e", "scrollback in editor", mine("scrollback")],
  ["a", "command palette", go("app.palette")],
  ["b", "toggle sidebar", go("layout.toggle", { id: "sidebar" })],
  ["s", "settings", go("app.settings")],
  ["?", "help", go("app.help")],
  ["q", "close window", go("window.close")],
  ["ctrl-a", "send ctrl+a", mine("send-prefix")],
];
const ACTIONS = Object.fromEntries(BINDS.filter(([, , action]) => action).map(([key, , action]) => [key, action]));
const HALF = Math.ceil(BINDS.length / 2);

export default class Prefix extends View {
  init(_props, cx) {
    this.handle = cx.focus_handle();
    this.handle.focus();
  }

  column(t, binds) {
    return v_flex()
      .flex_1()
      .gap(6)
      .children(
        binds.map(([key, label]) =>
          h_flex()
            .gap(10)
            .child(div().w(70).text_color(t.accent).child(key))
            .child(div().text_color(t.muted).truncate().child(label)),
        ),
      );
  }

  render() {
    const t = theme();
    return v_flex()
      .id("prefix")
      .track_focus(this.handle)
      .size_full()
      .p(12)
      .gap(10)
      .bg(t.popover)
      .text_size(12)
      .on_key_down((e, cx) => {
        cx.stop_propagation();
        if (["shift", "control", "alt", "platform", "function"].includes(e.key)) return;
        closeOverlay(props().overlay);
        if (/^[1-9]$/.test(e.keystroke)) return run("tab.select", { index: Number(e.keystroke) });
        (ACTIONS[e.keystroke] ?? ACTIONS[e.key_char ?? ""])?.();
      })
      .child(
        h_flex()
          .justify_between()
          .child(div().font_semibold().text_color(t.foreground).child("ctrl+a"))
          .child(div().text_color(t.dim).child("esc")),
      )
      .child(h_flex().gap(16).items_start().child(this.column(t, BINDS.slice(0, HALF))).child(this.column(t, BINDS.slice(HALF))));
  }
}
