# Calculator

A responsive calculator SPA built with React, TypeScript, and Vite. It supports keyboard input, light/dark themes, and all standard calculator operations including percent, sign toggle, and repeated equals. The application is deployed to GitHub Pages via an automated workflow.

## Getting started

```bash
npm install
npm run dev
```

The development server runs at [`http://localhost:5173`](http://localhost:5173) with hot module replacement enabled.

## Available scripts

| Command | Description |
| --- | --- |
| `npm run dev` | Start the Vite development server. |
| `npm run build` | Type-check and create a production build in `dist/`. |
| `npm run preview` | Preview the production build locally. |
| `npm run test` | Execute unit tests with Vitest (includes coverage). |
| `npm run lint` | Lint the project with ESLint. |
| `npm run format` | Format sources using Prettier. |

## Keyboard shortcuts

| Key | Action |
| --- | --- |
| `0-9` | Enter digits |
| `.` or `,` | Decimal separator |
| `+`, `-`, `*`, `/` | Arithmetic operators |
| `Enter` / `=` | Equals |
| `Escape` | All clear (`AC`) |
| `Delete` | Clear entry (`C`) |
| `Backspace` | Backspace (`⌫`) |
| `%` | Percent |
| `F9` | Toggle sign (`±`) |

## Features

- Addition, subtraction, multiplication, and division
- Decimal support with up to 12 significant digits and exponential formatting for very large/small numbers
- Operations: `AC`, `C`, `±`, `%`, `⌫`
- Repeated equals (e.g., `3 + 2 = =` → `7`)
- Graceful error handling (division by zero resets on next input)
- Keyboard-friendly with focus styles for accessibility
- Theme toggle with persistence and system preference detection

## Deployment

Pushes to the `main` branch that touch `apps/calculator/**` trigger the workflow in `.github/workflows/deploy-calculator.yml`. The action runs linting, tests, builds the project, and publishes the output to GitHub Pages. Once deployed, the site is available at `https://<github-username>.github.io/ddnet/`.
