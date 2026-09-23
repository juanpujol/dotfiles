# RPI development services

`rpi-dev` keeps the Mac-to-Raspberry Pi development tunnel and the restricted
1Password proxy observable and reproducible.

## Setup

```bash
~/dotfiles/bin/rpi-dev install
rpi-dev start
rpi-dev doctor
rpi-dev test-1p
```

The first authenticated request can display a 1Password biometric prompt on the
Mac. The Mac must be awake, connected to the Pi, and able to access the
`Laiki-Env` vault.

## Use from a Pi Herdr pane

```bash
cd ~/Code/@laiki/laiki2
with-1p bun dev
with-1p bun dev:web
with-1p bun dev:workflow
with-1p bun s:run scripts/example.ts
```

Only the proxy credential is passed to the wrapped process. Varlock uses the
existing `.env.schema` integration to retrieve secrets. Secret values are never
written to the project or proxy logs.

## Operations

```bash
rpi-dev start
rpi-dev stop
rpi-dev restart
rpi-dev status
rpi-dev doctor
rpi-dev logs proxy
rpi-dev logs tunnel
rpi-dev test-1p
rpi-dev rotate-token
```

Version-controlled files live under `~/dotfiles/rpi-dev` and `~/dotfiles/bin`.
Runtime configuration, tokens, and logs live under `~/.config/rpi-dev` and
`~/.local/state/rpi-dev` and are not committed.

The Mac proxy listens only on loopback. The Pi reaches it through a loopback-only
SSH reverse forward. The proxy accepts only the exact `op item get` operations
referenced by the canonical Mac checkout's `.env.schema` files.
