# Tests

End-to-end checks of the builder and the terminal pages it makes, in a headless browser:

- the builder's checks on its entries, the ZIP and its eye-witness file set, and that the passkey appears nowhere in the output;
- sign-in and refusal, one task per session, the task fixed after the first tick, sign-out held until every sub-task is ticked, the ARE YOU SURE? window (Cancel keeps the session), and one task fewer at the next sign-in;
- the three reply formats, a list that cannot be loaded, the message box, and the preview with canned sub-tasks;
- the separate service (`server.py` stands in for it): a refused record keeps the session open, and completion is honoured on another device.

`messaging.py` checks, in test mode, the messages and the Emergency button: each colour of status, replies, a failed send and *Send again*, the automatic retry of an emergency, that a second press raises no second emergency, and that the Emergency button can be pressed while the ARE YOU SURE? window is open.

## Running them

```
pip install playwright
playwright install chromium
python3 -I tests/e2e.py
python3 -I tests/messaging.py
```

To use an installed Chrome instead, set `CHROME` to its path. The tests serve a copy of the repository at `http://localhost:8765` and print `33/33 passed` when all is well; `messaging.py` prints `18/18 passed`.

---
© Computational Classnotes · CC BY-NC-SA 4.0
