# CCN Terminal · Journal — specification

*Version 1.1 · 24 November 2026 · Computational Classnotes*

## 1. Purpose

The Journal is the manager's view of everything the terminals report. It has two jobs:

1. **Live:** show the floor as it is now. That covers who is signed in where, on which job, how far along, and which steps are running long. The view refreshes every minute.
2. **History:** show, over any range of dates, **where the work slows down**: which steps, at which work-tables, at which hours, for which groups.

It reads the same clicks the terminals already send to the service. Every figure is computed in the page from those raw clicks, so every number can be traced back to the clicks behind it.

## 2. Who uses it

- **Managers**, with a manager key: a third kind of key, beside worker passkeys and author keys. The key is sent once and exchanged for a session token (section 10).
- The **employer** is responsible for telling workers what is collected, and for how long it is kept (agreed 24 November 2026).

## 3. The path: group / work-table / worker

Everything in CCN has a path, usually *group / user / project*. In the Terminal it is **group / work-table / worker**.

- **Work-table** is where the work happens: the station named at install, such as `Mail-Room1` or `Cutter-2`.
- **Worker** is whoever signs in there.
- **Group** is any named set of work-tables, workers, or both, made by any design the client chooses. Examples: by place (*First floor*), by people (*New starters*), by role (*Cutters*), by time (*Second shift*).

**An entity may sit in several groups at once, and its work counts in each.** A click belongs to a group if its work-table is in the group's tables or its worker is in the group's workers.

Groups are kept by the service, next to the jobs. The Journal and the admin tool both edit them through the same service actions. There is one copy and nothing to keep in step.

## 4. What each click carries

The terminal sends each click to the service, and the service logs it as one record under `Terminal/log/<date>/`. The Journal reads these records.

| Field | Example | Notes |
|---|---|---|
| `time` | `2026-11-24T08:39:58Z` | set by the service on arrival (UTC) |
| `action` | `signin`, `tick`, `event`, `complete`, `signout`, `message`, `emergency` | |
| `kind` | `job-chosen`, `signout-cancel`, `signout-confirm`, `station-named`, `install` | for `event` |
| `page`, `station` | `ccn-factory`, `Mail-Room1` | the page, and the work-table |
| `worker` | `Bea` | from the session token (or passkey) |
| `job`, `sub`, `checked` | `12`, `12-04`, `true` | for `tick`; `checked:false` is an untick, kept, never deleted |
| `retry` | `true` | **new:** the tick was Confirmed only on a second press (*Press again!*) |
| `ok` | `false` | for a refused sign-in |
| `ctx.tz`, `ctx.local` | `Europe/Dublin`, `2026-11-24T08:39:58` | **new:** the device's time zone and local time |
| `ctx.device` | `tablet · Chrome/131 · 1280×800` | **new:** kind of device, browser, screen |
| `ctx.gps` | `{lat, lon, acc}` | **new:** only where the browser allowed it; asked once, when the station is named |
| `ip` | `203.0.113.17` | **new:** read by the service from the request (to be confirmed on the live endpoint; see section 13) |

No record ever holds a passkey, a key or a token.

## 5. Service actions

These already exist: `signin` (now returns a `token`), `signout`, `job`, `tick`, `event`, `complete`, `message`, `messages`, `emergency`, `authorSignin`, `authorSignout`, `listJobs`, `getJob` and `saveJob`.

**New, for the Journal.** These are written and tested in `ff_terminal.nb` (70 checks), and wait for the owner's release:

| Action | Sends | Answers |
|---|---|---|
| `managerSignin` | `managerKey` | `{ok, token}` |
| `managerSignout` | `managerToken` | `{ok}` |
| `journal` | `managerToken, day` (`YYYY-MM-DD`), optional `after` (`HHMMSS`) and `meta:true` | `{ok, day, events}`: that day's records, each with an `id`; with `meta`, also `workers`, `jobs` and `groups` |
| `saveGroups` | `managerToken` (or `authorToken`, for the admin tool), `groups` | `{ok}`. Each group is cleaned, and a group without a name, or two groups with one ID, are refused |
| `terminalAddManager[name, key]` | (owner, unsaved notebook) | adds a manager key, as a salted hash |

A group is `{id, name, basis, color, tables:[…], workers:[…]}`.

**One day at a time.** The page asks for one day per request: 14 days on opening (`?days=` changes this, up to 60), then, each minute, only today's clicks after the last one it has (`after`). It merges records by `id`. The service gathers a past day once into a single object, `Terminal/logday/<date>`, so later reads of that day are one read, not one per click. Today is always read fresh.

## 6. Definitions (how every figure is computed)

- **Session:** from an accepted sign-in to the next sign-out at the same work-table.
- **Step time:** the time from the previous click in the session (job chosen, or the previous tick or untick) to this tick.
- **Job time:** from *job chosen* to *job recorded as done*.
- **Usual time of a step:** the median step time of that sub-task over the whole history.
- **Running long:** a step whose time is over **1.5 ×** its usual time (`LONG = 1.5`, one constant in the page). In the live view, the time so far on the next unticked sub-task is compared with its usual time.
- **Rework:** unticks divided by ticks.
- **Press again!:** ticks marked `retry`.
- **Idle between jobs:** from a sign-out to the next sign-in at the same work-table on the same day.
- **Heatmap cell** (work-table × hour): its number is the median step time in minutes. Its colour is the median of *step time ÷ usual time*, in six bands: below 0.85, 0.85–0.95, 0.95–1.08, 1.08–1.25, 1.25–1.55, and 1.55 and above (amber). So the colour says *slower than usual for that step*, not merely *a long step*.
- **After-14:00 pattern:** for each table, the median of that ratio after 14:00 divided by the median before. The Journal names any table at 1.35 × or more, with at least 10 steps.
- **Medians and p90** are used rather than averages, so that one very long step does not hide the usual pace.

## 7. Screens

1. **Live: the floor, right now.**
   - Figures for today: signed in, jobs done, median job (against last week), running long, Press again!, messages and emergencies.
   - A card per work-table: worker, job, progress, current step and time on it, and a status (On track, Running long, Choosing a job, Idle).
   - *Running long now*.
   - *As it happens*: the latest clicks.
   - Group chips filter everything. A card opens the drill-down.
2. **Bottlenecks: where the work slows down.**
   - Filters: dates (last 3 or 7 working days, all, or chosen dates), group and job.
   - Figures: median step, slowest step, rework, idle between jobs, jobs done.
   - The heatmap, with the after-14:00 pattern under it.
   - *The slowest sub-tasks*: median, p90, spread from p10 to p90, unticks, Press again!.
   - *Groups compared* (median job time).
   - *Trouble signs* by table: unticks, Press again!, refused sign-ins, messages.
   - Download CSV.
3. **Timeline: a day at every table.**
   - One row per work-table, 06:00–18:00: jobs as bars, steps running long in amber, ticks, and markers for messages, Press again! and refused sign-ins.
   - Today shows a *now* line.
   - Summaries: longest step, longest idle, busiest table.
   - Day stepper and group filter. A row opens the drill-down.
4. **Drill-down: group / work-table / worker / job.**
   - Choose a table, a worker and a job run.
   - The worker: their groups, jobs done, time signed in, unticks, Press again!.
   - *Where, and on what*, from the latest sign-in at that table: time zone, local time, IP address, position, device.
   - *Time per step* in bars, with amber over 1.5 × usual.
   - *Every click, as the cloud received it*, with Download CSV.
5. **Groups.**
   - The list of groups.
   - An editor: name, a note on what makes the group, and its tables and workers. Save, *See its bottlenecks*, Delete.
   - A grid of who is in which group.

The look: dark, IBM Plex Sans and Mono, teal for normal work, amber for slow-downs. The orange **Confirmed** matches the terminal. Every screen works at phone width, and wide tables scroll inside their box.

## 8. Live refresh

The live view and today's timeline refresh **every minute** while the page is in view.

- **With the service:** the Journal reads the new clicks.
- **With the sample:** a **sample clock** stands in for now, by default 10:30. It moves on a minute each minute and can be dragged anywhere from 06:00 to 18:00.

## 9. The fake sample

`journal/sample-data.json` is **fake data**, made by `journal/tools/make-sample.py`. It involves no real person or factory, and the page labels it *Fake sample data* throughout.

- 12 work-tables, 12 workers, 7 jobs, 8 groups.
- Working days from Monday 10 to Tuesday 24 November 2026, 06:00–18:00, with two shifts.
- 28,293 clicks: about 4.4 MB, or about 250 KB compressed, as GitHub Pages serves it.

It is in the service's log format. To stay small, it carries the context and IP address on sign-ins only. It is deterministic, so the same seed gives the same file.

**Planted bottlenecks,** so that the Journal has something to find:
- CT-03 *Set the blade depth* is slow and unpredictable.
- Cutter-2 and Dispatch-1 slow down after 14:00, when the second shift starts.
- LP-02 *Load the labels* often needs Press again! and is often unticked.
- New starters (Bea, Ravi) are slower.
- Mondays are a little slower.
- Docking-7 stands idle over the middle of the day.
- There is one emergency, on 12 November at Cutter-2.

The Journal finds the planted ones. For example, *"Dispatch-1 is 2.0 × slower after 14:00; Cutter-2 is 1.9 × slower after 14:00"*, and CT-03 heads the slowest sub-tasks.

## 10. Security

In short (full scheme: `SECURITY.md`):

- Everything travels over HTTPS.
- Keys are **sent once**, at sign-in, in exchange for a random 256-bit **session token**. The service keeps only the token's SHA-256 hash, and the token ends at sign-out or after 12 hours.
- Keys are stored only as salted hashes.
- No record holds a key or a token.
- The manager key follows the same scheme.

## 11. Files

- `journal/index.html`: the Journal. One page; nothing to install.
- `journal/sample-data.json` and `journal/tools/make-sample.py`: the fake sample and its maker.
- `journal/SPEC.md`, `journal/SPEC.pdf`: this specification.
- `SECURITY.md`: the security scheme.
- `tests/journal.py`: 27 checks. Every screen renders on the sample, at desktop and phone width. The figures agree with an independent computation in Python. The group filter works, and groups are kept and reset. Against a stand-in that answers as the service does, the key is sent once and then only the token; 7 days are read one at a time; the figures match the sample; and each minute reads only today's newer clicks.
- `tests/TerminalTests.nb` (in the owner's `Terminal` folder): 70 checks of the service, the Journal actions included.

Address: https://lossofgenerality.github.io/terminal/journal/ (add `?source=service` for the live service, once it offers the Journal).

## 12. The owner's steps

1. Release `ff_terminal.nb`. One release brings the session tokens, the context and the Journal actions. Open it fresh, evaluate it, quit. Then deploy again: `CloudGet[…ffTerminal]; terminalDeploy[]`.
2. Add a manager key with `terminalAddManager["<name>", "<key>"]` in a new, unsaved notebook, closed without saving.
3. Open the Journal with `?source=service` and sign in with that key.

## 13. Open questions and next steps

- **IP address:** the service reads it with `HTTPRequestData` (the `x-forwarded-for` header, then the remote address). This is to be confirmed on the live endpoint after the release, by reading one log record.
- **Paging and summaries** for long date ranges.
- **Brute-force limit** on sign-in, and ending every session of a worker at once.
- **How long records are kept:** the employer to decide.
- **Messages and emergencies:** whether the Journal also becomes the manager's inbox, with replies and *opened* / *handled*, or whether that stays in the admin tool.
- **Thresholds:** whether the 1.5 × *running long* threshold and the colour bands should be settable per client.

---
© Computational Classnotes · CC BY-NC-SA 4.0
