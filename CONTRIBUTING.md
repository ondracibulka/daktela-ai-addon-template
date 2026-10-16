# Contributing

This repository is a **template**. Most people should fork it and change everything. Contributions
back are welcome when they make the template clearer or more correct for everyone.

## Good contributions

- A gotcha you hit that the docs did not warn you about.
- A correction — the SDK changed, a route moved, an example no longer runs.
- A simplification. Less code in a template is worth more than more features.
- Better failure handling in the examples.

## Probably not

- New example modules. Four is already a lot to read; a fifth has to earn its place by teaching
  something the others do not.
- Extra tooling. Storybook, E2E harnesses and coverage gates were deliberately left out so a newcomer
  can read the whole repository in an afternoon.
- Your own addon's business logic.

## Setup

```bash
uv sync --all-extras
cd frontend && corepack pnpm install
```

## Before opening a pull request

```bash
make check      # ruff, ruff format --check, pyright, pytest, eslint, tsc, vitest
```

All of it must pass. It is the same thing CI runs.

If you changed a database model:

```bash
make db-up
make migrate-generate m="what changed"
make migrate
uv run alembic check      # must report no new operations
```

## Dependencies that are deliberately not on the latest version

These are held back on purpose. Bumping them breaks the build, so check here before "fixing" them:

| Package | Pinned at | Why |
|---|---|---|
| `@mui/material`, `@mui/icons-material` | `^7` | `@coworkers/cw-utils`, the shared theme, declares `@mui/material: ^6 \|\| ^7`. Moving to 9 leaves that peer unmet. |
| `@mui/x-data-grid` | `^8` | Same package, `^7 \|\| ^8`. The theme imports its `themeAugmentation` at runtime. |
| `vite` | `^7` | `@originjs/vite-plugin-federation` (last released for Vite 4, and the only plugin the host's loader can consume) breaks on Vite 8: it stops substituting its `__v__css__` placeholder, the bundle ships the literal token, and the configuration page dies at mount with `e.forEach is not a function`. The build says nothing. |
| `@vitejs/plugin-react` | `^5` | Version 6 imports `vite/internal` and needs Vite 8. |
| Python | `3.14` (`.python-version`) | Without a pin `uv` picks the newest CPython. `psycopg-binary` 3.3.5 ships wheels only up to `cp314`, so on 3.15 `uv sync` fails with "doesn't have a source distribution or wheel for the current platform". |
| `typescript` | `6.0.x` | `typescript-eslint` supports `>=4.8.4 <6.1.0`. On TypeScript 7 it refuses to run and `pnpm lint` fails outright. |

The MUI cap lifts when the theme widens its peer range; the TypeScript one when typescript-eslint
ships TS 7 support ([tracking issue](https://github.com/typescript-eslint/typescript-eslint/issues/10940));
the Vite one when the federation plugin supports Vite 8, or when the host can consume a bundle built
by `@module-federation/vite`.

`frontend/tests/federationBundle.test.ts` fails on the Vite 8 symptom, so a future bump cannot ship
it silently — but it only runs against a build, so run `pnpm build` before `pnpm test`.

## House style

**Code**

- Comments explain *why*, not *what*. This repository is read as documentation, so a comment that
  explains a non-obvious constraint is worth more here than in ordinary code.
- Every example file opens with a header: what it demonstrates, which chapter covers it, what to
  change first.
- Prefer fewer concepts over more abstraction. If a reader has to hold four layers in their head to
  follow one request, the design is wrong for a template.
- Keep the SQL table dialect-neutral, so the test suite can run it on SQLite.

**Docs**

- English, second person, present tense.
- Every chapter ends with **Next**.
- Show the command and its real output. An example nobody ran is a bug waiting to be reported.
- When behaviour is surprising, say so and explain why it is that way.

## Verifying the docs

The guide is only worth what it claims to be if the steps work. Before changing a chapter's
instructions, run them on a clean clone. The end-to-end path worth re-checking after any significant
change:

1. `uv sync --all-extras && uv run uvicorn server.main:app --reload`
2. `curl -H "X-Api-Key: default" localhost:8000/manifest` lists all four modules
3. `curl localhost:8000/readiness` reports `backend: json`
4. Register the addon in bot-platform as a custom addon with header `X-Api-Key: default`
5. Place the **Write Interaction Event** node in a flow and run a conversation
6. The event shows up in the interaction's Events panel

## Reporting a problem

Include the addon's log, the output of `curl -H "X-Api-Key: default" localhost:8000/manifest`, and
what you expected instead. If it involves bot-platform, say which version.
