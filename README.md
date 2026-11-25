# CCN Terminal — Builder

A web page that writes **terminal pages**: standalone apps in which a person signs in with a passkey, chooses one job, ticks off its sub-tasks, and may sign out only once they are all complete. The job is then done, and the next sign-in offers one job fewer. Built in the manner of the CCN Composite Eye-witness builder: the builder fills in a template, shows a preview, and hands over one instance folder.

Builder: https://lossofgenerality.github.io/terminal/ (once GitHub Pages is switched on for this repository).

## What a terminal page holds

From the top:

1. **The client's logo** (if one was chosen in the builder) and **the app's name**, with **Install app** under it and the **Emergency** button at the top right.
2. **Job**, directly under the name: a pulldown of the jobs not yet done. It appears only once the passkey is accepted, and is fixed once the first sub-task is ticked.
3. **Sign in** — a box reading *Enter passkey*; Enter or the button signs in.
4. **Sign out** — disabled until every sub-task of the chosen job is ticked. Pressing it opens an **ARE YOU SURE?** window; *Yes, sign out* then records the job as done; if it cannot be recorded, the person stays signed in and may try again. When every job is done, the pulldown says so and sign-out is open.
5. **Message** — a box for messages to the manager, available before signing in as well, so that a worker who cannot sign in can still reach the manager. Messages are two-way, but a reply is optional. Each message carries a small dot: red, not sent (with *Send again*); yellow, delivered with no response yet; green, opened by the manager; blue, handled. A written reply appears under the message. Each dot also has a text label.

Under the app's name is **Install app**, always shown (as on the witness pages). It first asks for the **installation's ID**, for example `Mail-Room1` or `Ducking-7`, since one page may be installed at several stations; then it installs the page as an app where the browser allows, and otherwise says what is in the way (on iPhone, Share then Add to Home Screen). The ID is printed in the title, after the app's name, for example *Packing Station (12)*, and kept on that device; an installed app opened without one asks for it. Every request to the service carries it as `station`.

At the top right of the page is the **Emergency** button, styled as a red emergency stop. One press, with no sign-in, sends an emergency to the service, which starts the emergency protocol; its status uses the same colours. A second press while one is open does not raise another. If it cannot be sent, the page says so, tells the worker to raise the alarm on site, and retries every 5 seconds.

Under the sign-in box is the red line *Warning: Unauthorized Access Forbidden*.

Choosing a job fetches its address. The job's **specifics** appear in a read-only, scrollable box, with the formatting given in the job-authoring tool. It is stored as a small markup, escaped before drawing: `**bold**`, `__italic__` (or `*italic*`), `[red]…[/red]` in red, amber, green or blue, and `- ` bullet points; under it, the sub-tasks are laid out as a vertical list, each with an unticked checkbox on the left and, to its right, the sub-task's **ID number** followed by its short text. The worker ticks each one as it is done. Specifics are optional: without them the box is not shown.

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

The service is `ff_terminal` in the Wolfram Cloud, live at `https://www.wolframcloud.com/obj/ccn2/TerminalKernel` (the builder's default address). Each request is a POST of one form field, `payload_b64`: base64 of the UTF-8 JSON below. The reply is `{"reply_b64": …}`, base64 of the UTF-8 JSON reply. Base64 keeps every language intact, and a form POST needs no CORS preflight. `page` is the instance's id, from `terminal-data.json`.

| When | The page sends | The service replies |
|---|---|---|
| Sign-in | `{"action": "signin", "passkey": …, "app": …, "page": …}` | `{"ok": true, "done": ["task name", …]}`, or `{"ok": false}` |
| Sign-out after a job | `{"action": "complete", "passkey": …, "app": …, "page": …, "task": "…", "subtasks": [{"id", "text"}, …]}` | `{"ok": true}` once recorded |
| A message | `{"action": "message", "conv": …, "mid": …, "text": …, "signedIn": …, "task": …, "app": …, "page": …}` (with `passkey` when signed in) | `{"ok": true}` |
| Emergency | `{"action": "emergency", "conv": …, "eid": …, "at": …, "signedIn": …, "task": …, "app": …, "page": …}` | `{"ok": true}`; the service starts the emergency protocol |
| Each tick and untick | `{"action": "tick", "job": …, "task": …, "sub": "MI-02", "checked": true, "at": …, "passkey": …}` | `{"ok": true}`; an untick is recorded too, nothing is deleted |
| Job chosen, Sign out Cancel, Sign out Yes, station named, Install | `{"action": "event", "kind": "job-chosen" \| "signout-cancel" \| "signout-confirm" \| "station-named" \| "install", "detail": …, "at": …}` (with `passkey` when signed in) | `{"ok": true}` |
| Status, every 20 s while anything is open | `{"action": "messages", "conv": …, "app": …, "page": …}` | `{"ok": true, "messages": [{"mid", "status", "reply"}], "emergency": {"eid", "status"}}` |

**Keys:** passkeys and author keys are read with spaces and surrounding quotes dropped (`"123"`, `'123'`, `“123”` all mean `123`), on the pages and in the service, both when a key is added and when it is checked.

Every request also carries `station`, the installation's ID (empty if none was given). `conv` is the device's conversation id, kept in the browser. Statuses are `delivered`, `opened` and `handled`. Messages and emergencies need no passkey: anyone may send. `done` lists the jobs already completed, which the pulldown leaves out. If the service omits `done`, the page falls back to what this browser remembers. Sign-in attempts, accepted or refused, are logged by the service itself.

**Every action shows its receipt.** When the service has a click, **Confirmed** appears in bold green beside or under the control: beside each sub-task (it stays), beside the Job menu (sign-in, job chosen), under Sign out, under Install, beside each message, in the emergency box. **If a tick or untick is not Confirmed within 5 seconds, the box goes back to how it was and *Press again!* shows in bold full red:** no Confirmed means press again. Sign out opens only when every tick is Confirmed.

**Every click is sent at once, in order.** With no connection, the other clicks wait on the page under a small amber *Waiting to send …* sign, and are retried every 5 seconds and as soon as the connection returns; any reply means the service has the click. **Sign out completes only once the service has received every waiting click**; the job is then recorded as done. The emergency keeps retrying on its own.

## The job-authoring tool (`author/`)

Jobs are written in the authoring tool and kept by the service in the Wolfram Cloud. When the sign-in reply carries `jobs: [{"id", "name"}]`, the terminal's Job menu lists those, and choosing one sends `{"action": "job", "job": id, "passkey": …}`, whose reply `{"ok": true, "specifics": …, "subtasks": [{"id", "text"}]}` fills the screen; otherwise the jobs given in the builder are used. In test mode, the terminal lists the jobs saved in the authoring tool in the same browser, so the two can be tried together before the service exists. The tool speaks to the service with its own key, so that workers cannot change jobs:

| The tool sends | The service replies |
|---|---|
| `{"action": "listJobs", "authorKey": …}` | `{"ok": true, "jobs": [{"id", "name"}]}` |
| `{"action": "getJob", "authorKey": …, "id": …}` | `{"ok": true, "job": {"id", "name", "specifics", "subtasks": [{"id", "text"}]}}` |
| `{"action": "saveJob", "authorKey": …, "job": {…}, "was": "old ID"}` | `{"ok": true}` |

The tool uses the service above by default (another address can be given as `?svc=https://…`), with the same base64 wire; with `?mock=1` it runs in test mode. Attachments are planned for a later version.

## An instance

Laid out as the witness pages in `lossofgenerality/eye-witness` are: `<folder>/<app>-<YYYYMMDD-HHMM>/` (UTC), holding

- `index.html` — the page, everything built in
- `README.md`, `notes.md` — what it is, and its production notes
- `terminal-data.json` — the page's settings, for reuse
- `manifest.webmanifest`, `sw.js`, `icons/` — install files

## Test mode

Add `?mock=1` to a terminal page's address: canned sub-tasks, no requests. With a passkey service, the test passkey is `123`. A dashed panel then plays the manager's side: open, reply to and mark handled messages and emergencies, make the next send fail, or cut the connection to see clicks wait under *Waiting to send*; it also lists the clicks the service has received.

## Files

- `index.html` — the builder
- `terminal-template.html` — the terminal page it fills in
- `icons/` — the icons placed in each instance
- `examples/` — sub-task lists used by the builder's example
- `author/` — the **job-authoring tool**: write each job's specifics in a WYSIWYG editor (**B**, *I*, four colours, bullet points and Clear; pasted text arrives plain) and its sub-tasks with IDs, previewed as the terminal shows them, and save them to the service. Test mode keeps the jobs in the browser (author key `123`): https://lossofgenerality.github.io/terminal/author/?mock=1
- `live/` — the same terminal connected to the live Wolfram service (a worker passkey from the owner): https://lossofgenerality.github.io/terminal/live/
- `demo/` — a terminal page built by the builder, in test mode (passkey `123`): https://lossofgenerality.github.io/terminal/demo/
- `journal/` — the **Journal**, the manager's view: the floor live (every minute) and where the work slows down (heatmap, slowest steps, timeline, drill-down group / work-table / worker / job, groups). Runs now on a FAKE sample history; see `journal/SPEC.md` (and `.pdf`): https://lossofgenerality.github.io/terminal/journal/
- `SECURITY.md` — the security scheme: HTTPS, keys sent once for session tokens, hashes at rest
- `tests/` — end-to-end checks in a headless browser, with a stand-in passkey service (see `tests/README.md`)

This app is independent: it shares no files with any other app.

## Updated stamp

Each page shows its build number and when it was updated or made in its footer. The builder offers a reload when a newer copy is online than the one open.

---
© Computational Classnotes · CC BY-NC-SA 4.0
