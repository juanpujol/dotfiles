import type { Plugin } from "@opencode/plugin/tui"

export default {
  id: "juan.tab-management",
  setup(context: Plugin.Context) {
    return context.ui.slot({
      append: "app",
      render: () => {
        context.keymap.layer(() => ({
          mode: "global",
          priority: 10,
          commands: [
            {
              id: "tabs.close-others",
              title: "Close other session tabs",
              group: "Sessions",
              bind: "<leader>shift+w",
              palette: true,
              slash: { name: "close-others" },
              enabled: () => context.ui.tabs.enabled() && context.ui.tabs.list().length > 1,
              run: () => {
                const current = context.ui.tabs.list().find((tab) => tab.active)
                if (!current) return

                let closed = 0
                for (const tab of context.ui.tabs.list()) {
                  if (tab.sessionID === current.sessionID) continue
                  if (context.ui.tabs.close(tab.sessionID)) closed++
                }

                context.ui.toast.show({
                  message: `Closed ${closed} other ${closed === 1 ? "tab" : "tabs"}`,
                  variant: "success",
                })
              },
            },
            {
              id: "session.new-here",
              title: "New session in current tab",
              group: "Sessions",
              bind: "<leader>shift+n",
              palette: true,
              slash: { name: "new-here" },
              run: async () => {
                const current = context.ui.tabs.list().find((tab) => tab.active)
                const previous = current ? context.data.session.get(current.sessionID) : undefined
                const location = previous?.location ?? context.location
                const session = await context.client.session.create({
                  ...(location ? { location } : {}),
                  ...(previous?.agent ? { agent: previous.agent } : {}),
                  ...(previous?.model ? { model: previous.model } : {}),
                })

                if (!context.ui.tabs.enabled()) {
                  context.ui.router.navigate({ type: "session", sessionID: session.id })
                  return
                }

                context.ui.tabs.open(session.id)
                if (current) context.ui.tabs.close(current.sessionID)
              },
            },
          ],
          bindings: ["tabs.close-others", "session.new-here"],
        }))

        return null
      },
    })
  },
}
