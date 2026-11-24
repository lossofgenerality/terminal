# Packing Station — Production notes

*Made with the CCN Terminal builder · 2026-11-24 00:57 UTC · builder build 2026.11.24-0043*

## Jobs

| # | Job | Address of its sub-tasks |
|---|---|---|
| 1 | Morning inspection | https://lossofgenerality.github.io/terminal/examples/morning-inspection.json |
| 2 | Label printer | https://lossofgenerality.github.io/terminal/examples/label-printer.json |
| 3 | Dispatch log | https://lossofgenerality.github.io/terminal/examples/dispatch-log.txt |

## Sign-in and sign-out

- The passkey is checked by the service at https://example.invalid/passkey-service.
- One job per session: sign-out is allowed once every sub-task of the chosen job is ticked, and records that job as done.
- The passkey is not sent with sub-task requests.
- Messages to the manager and the Emergency button go to the service (with the in-page check they cannot be sent). Both work without signing in.

---
© Computational Classnotes · CC BY-NC-SA 4.0
