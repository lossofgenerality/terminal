# CCN Terminal — Builder

A web page that writes **terminal pages**: standalone apps in which a person signs in with a passkey, chooses a task, ticks off its sub-tasks, and may sign out only once the sub-tasks are complete. Built in the manner of the CCN Composite Eye-witness builder: the builder fills in a template, shows a preview, and hands over one instance folder.

Builder: https://lossofgenerality.github.io/terminal/ (once GitHub Pages is switched on for this repository).

## What a terminal page holds

From the top:

1. **Task** — a pulldown of the tasks. It appears only once the passkey is accepted.
2. **The name of the app.**
3. **Sign in** — a box reading *Enter passkey*; Enter or the button signs in.
4. **Sign out** — disabled until every sub-task is ticked: of every task, or of the chosen task only, as chosen in the builder.
5. **Message** — a box and a Send button calling `sendMessage(text)`, which is an empty placeholder for now.

Choosing a task fetches its address; the reply is laid out as a vertical list of sub-tasks, each with a checkbox marking it complete. The reply may be a JSON list of strings, a JSON object holding such a list under `subtasks`, `items`, `tasks`, `list` or `data` (its entries may also be objects with `text`, `name` or `title`), or plain text with one sub-task per line (leading `-`, `*`, `1.` or `[ ]` are removed). The addresses must allow cross-origin requests (CORS) from wherever the page is served.

## Using the builder

1. Name the app; optionally give a short name and a folder (for instance a customer).
2. List the tasks, one per line: `Task name | https://…`, or the name alone, with its address made from the pattern (`{slug}`, `{task}`, `{n}`).
3. Choose how the passkey is checked:
   - **in the page:** only a salted SHA-256 hash of it is written into the page, never the passkey itself;
   - **by a service:** the page POSTs `{"passkey": …, "app": …}` as JSON and expects `{"ok": true}`.
4. **Build the page**, try it in the preview (canned sub-tasks by default), then **Download ZIP** or the page alone. **Save the specification** keeps the settings (with the hash, never the passkey) for rebuilding later.

A check in the page is a gate, not protection: the task addresses can be read from the page's source. Anything that must stay private needs the service check, with the service also guarding the sub-task addresses (the *Send the passkey* option sends it as `Authorization: Bearer …`).

## An instance

Laid out as the witness pages in `lossofgenerality/eye-witness` are: `<folder>/<app>-<YYYYMMDD-HHMM>/` (UTC), holding

- `index.html` — the page, everything built in
- `README.md`, `notes.md` — what it is, and its production notes
- `terminal-data.json` — the page's settings, for reuse
- `manifest.webmanifest`, `sw.js`, `icons/` — install files

## Test mode

Add `?mock=1` to a terminal page's address: canned sub-tasks, no requests. With a passkey service, the test passkey is `test-passkey`.

## Files

- `index.html` — the builder
- `terminal-template.html` — the terminal page it fills in
- `icons/` — the icons placed in each instance
- `examples/` — sub-task lists used by the builder's example

This app is independent: it shares no files with any other app.

## Updated stamp

Each page shows its build number and when it was updated or made in its footer. The builder offers a reload when a newer copy is online than the one open.

---
© Computational Classnotes · CC BY-NC-SA 4.0
