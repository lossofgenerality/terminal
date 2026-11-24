# CCN Terminal — Builder

A web page that writes **terminal pages**: standalone apps in which a person signs in with a passkey, chooses one job, ticks off its sub-tasks, and may sign out only once they are all complete. The job is then done, and the next sign-in offers one job fewer. Built in the manner of the CCN Composite Eye-witness builder: the builder fills in a template, shows a preview, and hands over one instance folder.

Builder: https://lossofgenerality.github.io/terminal/ (once GitHub Pages is switched on for this repository).

## What a terminal page holds

From the top:

1. **Job** — a pulldown of the jobs not yet done. It appears only once the passkey is accepted, and is fixed once the first sub-task is ticked.
2. **The name of the app.**
3. **Sign in** — a box reading *Enter passkey*; Enter or the button signs in.
4. **Sign out** — disabled until every sub-task of the chosen job is ticked. Pressing it opens an **ARE YOU SURE?** window; *Yes, sign out* then records the job as done; if it cannot be recorded, the person stays signed in and may try again. When every job is done, the pulldown says so and sign-out is open.
5. **Message** — a box for messages to the manager, available before signing in as well, so that a worker who cannot sign in can still reach the manager. Messages are two-way, but a reply is optional. Each message carries a small dot: red, not sent (with *Send again*); yellow, delivered with no response yet; green, opened by the manager; blue, handled. A written reply appears under the message. Each dot also has a text label.

Under the app's name is **Install app**, always shown (as on the witness pages). It first asks for the **installation's ID**, for example `Mail-Room1` or `Ducking-7`, since one page may be installed at several stations; then it installs the page as an app where the browser allows, and otherwise says what is in the way (on iPhone, Share then Add to Home Screen). The ID is printed in the title, after the app's name, for example *Packing Station (12)*, and kept on that device; an installed app opened without one asks for it. Every request to the service carries it as `station`.

At the top right of the page is the **Emergency** button, styled as a red emergency stop. One press, with no sign-in, sends an emergency to the service, which starts the emergency protocol; its status uses the same colours. A second press while one is open does not raise another. If it cannot be sent, the page says so, tells the worker to raise the alarm on site, and retries every 5 seconds.

Under the sign-in box is the red line *Warning: Unauthorized Access Forbidden*.

Choosing a job fetches its address. The job's **specifics** appear in a read-only, scrollable box; under it, the sub-tasks are laid out as a vertical list, each with an unticked checkbox on the left and, to its right, the sub-task's **ID number** followed by its short text. The worker ticks each one as it is done. Specifics are optional: without them the box is not shown.

The reply may be a JSON object `{"specifics": "…", "subtasks": [ … ]}` (`details` or `description` also serve for the specifics), or plain text: the specifics, a line holding only `---`, then one sub-task per line. A sub-task's ID comes with it: in JSON as an object `{"id": "MI-01", "text": "…"}` (`number` or `no` also serve), in plain text as `MI-01 | text`. A sub-task without an ID is numbered by its place in the list (1, 2, 3 …). For the sub-tasks alone, the reply may also be a JSON list of strings, a JSON object holding such a list under `subtasks`, `items`, `tasks`, `list` or `data` (its entries may also be objects with `text`, `name` or `title`), or plain text with one sub-task per line (leading `-`, `*`, `1.` or `[ ]` are removed). The addresses must allow cross-origin requests (CORS) from wherever the page is served.

## Using the builder

1. Name the app; optionally give a short name and a folder (for instance a customer).
2. List the jobs, one per line: `Job name | https://…`, or the name alone, with its address made from the pattern (`{slug}`, `{task}`, `{n}`).
3. Choose how the passkey is checked:
   - **by a separate service (the default, and the one to use):** see *The service* below;
   - **in the page (for tests only):** only a salted SHA-256 hash of it is written into the page, never the passkey itself. Completed jobs are then remembered in that browser only.
4. **Build the page**, try it in the preview (canned sub-tasks by default), then **Download ZIP** or the page alone. **Save the specification** keeps the settings (with the hash, never the passkey) for rebuilding later.

A check in the page is a gate, not protection: the job addresses can be read from the page's source. Real use therefore takes the separate service, which should also guard the sub-task addresses (the *Send the passkey* option sends it as `Authorization: Bearer …`).

## The service

The page POSTs JSON to the service's address twice per session (`page` is the instance's id, from `terminal-data.json`):

| When | The page sends | The service replies |
|---|---|---|
| Sign-in | `{"action": "signin", "passkey": …, "app": …, "page": …}` | `{"ok": true, "done": ["task name", …]}`, or `{"ok": false}` |
| Sign-out after a job | `{"action": "complete", "passkey": …, "app": …, "page": …, "task": "…", "subtasks": [{"id", "text"}, …]}` | `{"ok": true}` once recorded |
| A message | `{"action": "message", "conv": …, "mid": …, "text": …, "signedIn": …, "task": …, "app": …, "page": …}` (with `passkey` when signed in) | `{"ok": true}` |
| Emergency | `{"action": "emergency", "conv": …, "eid": …, "at": …, "signedIn": …, "task": …, "app": …, "page": …}` | `{"ok": true}`; the service starts the emergency protocol |
| Status, every 20 s while anything is open | `{"action": "messages", "conv": …, "app": …, "page": …}` | `{"ok": true, "messages": [{"mid", "status", "reply"}], "emergency": {"eid", "status"}}` |

Every request also carries `station`, the installation's ID (empty if none was given). `conv` is the device's conversation id, kept in the browser. Statuses are `delivered`, `opened` and `handled`. Messages and emergencies need no passkey: anyone may send. `done` lists the jobs already completed, which the pulldown leaves out. If the service omits `done`, the page falls back to what this browser remembers. The service is yet to be written; a Wolfram Cloud APIFunction is the natural home for it.

## An instance

Laid out as the witness pages in `lossofgenerality/eye-witness` are: `<folder>/<app>-<YYYYMMDD-HHMM>/` (UTC), holding

- `index.html` — the page, everything built in
- `README.md`, `notes.md` — what it is, and its production notes
- `terminal-data.json` — the page's settings, for reuse
- `manifest.webmanifest`, `sw.js`, `icons/` — install files

## Test mode

Add `?mock=1` to a terminal page's address: canned sub-tasks, no requests. With a passkey service, the test passkey is `123`. A dashed panel then plays the manager's side: open, reply to and mark handled messages and emergencies, or make the next send fail.

## Files

- `index.html` — the builder
- `terminal-template.html` — the terminal page it fills in
- `icons/` — the icons placed in each instance
- `examples/` — sub-task lists used by the builder's example
- `tests/` — end-to-end checks in a headless browser, with a stand-in passkey service (see `tests/README.md`)

This app is independent: it shares no files with any other app.

## Updated stamp

Each page shows its build number and when it was updated or made in its footer. The builder offers a reload when a newer copy is online than the one open.

---
© Computational Classnotes · CC BY-NC-SA 4.0
