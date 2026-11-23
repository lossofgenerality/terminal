# Tests

End-to-end checks of the builder and the terminal pages it makes, in a headless browser:

- the builder's checks on its entries, the ZIP and its eye-witness file set, and that the passkey appears nowhere in the output;
- sign-in and refusal, one task per session, the task fixed after the first tick, sign-out held until every sub-task is ticked, and one task fewer at the next sign-in;
- the three reply formats, a list that cannot be loaded, the message box, and the preview with canned sub-tasks;
- the separate service (`server.py` stands in for it): a refused record keeps the session open, and completion is honoured on another device.

## Running them

```
pip install playwright
playwright install chromium
python3 -I tests/e2e.py
```

To use an installed Chrome instead, set `CHROME` to its path. The tests serve a copy of the repository at `http://localhost:8765` and print `32/32 passed` when all is well.

---
© Computational Classnotes · CC BY-NC-SA 4.0
