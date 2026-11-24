# Tests

End-to-end checks of the builder and the terminal pages it makes, in a headless browser:

- the builder's checks on its entries, the ZIP and its eye-witness file set, and that the passkey appears nowhere in the output;
- sign-in and refusal, one task per session, the task fixed after the first tick, sign-out held until every sub-task is ticked, the ARE YOU SURE? window (Cancel keeps the session), and one task fewer at the next sign-in;
- the three reply formats, a list that cannot be loaded, the message box, and the preview with canned sub-tasks;
- the separate service (`server.py` stands in for it): a refused record keeps the session open, completion is honoured on another device, and the job list can come from the service at sign-in, each job fetched when chosen.

`messaging.py` checks, in test mode, the messages and the Emergency button: each colour of status, replies, a failed send and *Send again*, the automatic retry of an emergency, that a second press raises no second emergency, and that the Emergency button can be pressed while the ARE YOU SURE? window is open.

`clicks.py` checks the click reports against the stand-in service on the real wire (`payload_b64` in, `reply_b64` out): the station named and Install, the job chosen (with non-ASCII text intact), every tick and untick in order with time, station, job and passkey, Sign out Cancel; then, with the connection cut, the *Waiting to send* sign, sign-out held until the waiting clicks arrive in order, and the job recorded; and the same in test mode (`16/16 passed`).

`author.py` checks the job-authoring tool in test mode: sign-in, the WYSIWYG editor (B, I, colours, bold with italic, Clear, bullet points, plain-text paste), the preview and its escaping of HTML, sub-task IDs and reordering, the checks before saving, saving and reopening, and that a job saved there appears on the demo terminal (`26/26 passed`).

## Running them

```
pip install playwright
playwright install chromium
python3 -I tests/e2e.py
python3 -I tests/messaging.py
python3 -I tests/author.py
python3 -I tests/clicks.py
```

To use an installed Chrome instead, set `CHROME` to its path. The tests serve a copy of the repository at `http://localhost:8765` and print `45/45 passed` when all is well; `messaging.py` prints `25/25 passed`.

---
© Computational Classnotes · CC BY-NC-SA 4.0
