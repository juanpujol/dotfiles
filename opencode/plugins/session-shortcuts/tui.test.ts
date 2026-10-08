import { describe, expect, test } from "bun:test"
import plugin from "./tui"

function fixture(description = "Show all project sessions", key = "ctrl+a") {
  let layer: any
  const forwarded: any[] = []
  plugin.setup({
    keymap: {
      layer: (factory: () => unknown) => {
        layer = factory()
      },
      active: () => [{ key, description }],
    },
    renderer: {
      keyInput: {
        processParsedKey: (event: unknown) => forwarded.push(event),
      },
    },
  } as any)
  return { layer, forwarded }
}

describe("session picker shortcut", () => {
  test("registers Ctrl+G in modal mode without changing preferences on load", () => {
    const { layer, forwarded } = fixture()
    expect(layer.mode).toBe("modal")
    expect(layer.commands[0].bind).toBe("ctrl+g")
    expect(forwarded).toEqual([])
  })

  for (const description of ["Show all project sessions", "Show current directory sessions"]) {
    test(`forwards to the built-in toggle: ${description}`, () => {
      const { layer, forwarded } = fixture(description)
      layer.commands[0].run()
      expect(forwarded).toHaveLength(1)
      expect(forwarded[0]).toMatchObject({ name: "a", ctrl: true, meta: false, eventType: "press" })
    })
  }

  test("leaves Ctrl+G alone in other dialogs", () => {
    const { layer, forwarded } = fixture("Connect provider")
    expect(layer.commands[0].run()).toBe(false)
    expect(forwarded).toEqual([])
  })

  test("does not forward when the built-in shortcut changes", () => {
    const { layer, forwarded } = fixture("Show all project sessions", "ctrl+b")
    expect(layer.commands[0].run()).toBe(false)
    expect(forwarded).toEqual([])
  })
})
