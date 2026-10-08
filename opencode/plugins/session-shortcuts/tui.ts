import type { Plugin } from "@opencode/plugin/tui"

export default {
  id: "juan.session-shortcuts",
  setup(context: Plugin.Context) {
    context.keymap.layer(() => ({
      mode: "modal",
      priority: 10,
      commands: [
        {
          id: "session.list.toggle-scope",
          title: "Toggle session list scope",
          group: "Dialog",
          bind: "ctrl+g",
          run: () => {
            // V2.0.25's scope toggle is an inline Ctrl+A binding, not a configurable command.
            const sessionListOpen = context.keymap.active().some(
              (binding) =>
                binding.key === "ctrl+a" &&
                (binding.description === "Show all project sessions" ||
                  binding.description === "Show current directory sessions"),
            )
            if (!sessionListOpen) return false

            // Forward locally to the built-in toggle; no state changes until Ctrl+G is pressed.
            context.renderer.keyInput.processParsedKey({
              name: "a",
              ctrl: true,
              meta: false,
              shift: false,
              option: false,
              sequence: "\u0001",
              number: false,
              raw: "\u0001",
              eventType: "press",
              source: "raw",
            })
          },
        },
      ],
    }))
  },
}
