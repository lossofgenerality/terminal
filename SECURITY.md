# CCN Terminal: the security scheme

*24 November 2026. Covers the terminal page, the job-authoring tool, the Journal and the service `ff_terminal` (endpoint `TerminalKernel` in the Wolfram Cloud).*

## 1. What is protected

| Secret | Who has it | Where it lives |
|---|---|---|
| Worker passkey | each worker | typed into the terminal at sign-in; the service keeps only a salted SHA-256 hash |
| Author key | whoever writes jobs | typed into the authoring tool; kept only as a salted hash |
| Manager key (Journal) | managers | typed into the Journal; kept only as a salted hash |
| Session token | the page, while signed in | in the page's memory only; the service keeps only its SHA-256 hash |
| The records (jobs, clicks, messages, groups) | the service | private cloud objects under `Terminal/` in the owner's account |

## 2. In transit

- Every request goes over **HTTPS** to the Wolfram Cloud. The connection is encrypted end to end between the device and the cloud.
- The request is one form field, `payload_b64`, and the reply is `{"reply_b64": …}`. **Base64 is not encryption.** It is there only so that every language survives the trip. Secrecy comes from HTTPS.
- Keys are always in the POST body, never in the address (URL). Addresses end up in browser history, server logs and referrer headers.
- A form POST is a "simple" request, so the browser sends no CORS preflight. The endpoint answers any origin (`access-control-allow-origin: *`). That is safe here because nothing is decided by the origin: every action that matters needs a key or a token.

## 3. Keys are sent once: session tokens

1. **Sign-in.** The page sends the passkey once, `{action:"signin", passkey}`. The service drops spaces and surrounding quotes, hashes the passkey with the salt and looks up the worker.
2. **The token.** On success the service makes a **session token** of 256 random bits from the system's cryptographic generator (`GenerateSymmetricKey`), written as 64 hexadecimal characters. It stores **only the token's SHA-256 hash**, under `Terminal/sessions/<hash>`, with the worker, page, station, creation time and expiry. It returns the token itself just once, in the sign-in reply.
3. **After sign-in.** The page **drops the passkey from memory** and sends `token` in place of the passkey with every click: ticks, job chosen, completion, messages.
4. **The end of a token.** A token ends:
   - at **sign-out**: the page sends `{action:"signout", token}` and the service marks the session ended;
   - after **12 hours** (`$terminalSessionHours`), whatever happens;
   - for workers and authors separately: a worker's token never opens the authoring tool.
5. **The authoring tool** works the same way: `authorSignin` with the author key returns a token, then `authorToken` is sent until `authorSignout`.
6. **Backward compatible.** A service without tokens is simply not given one, and the pages then keep the passkey in memory as before.

**What this buys.** A token caught somehow, on a shared screen, by a browser extension or in a crash report, works only until sign-out or 12 hours. It cannot be used to sign in again, and it never reveals the passkey. The cloud never holds a usable token either, only its hash.

## 4. At rest

- **Passkeys, author keys and manager keys:** salted SHA-256 hashes only, in the private object `Terminal/config`. They are added by the owner with `terminalAddWorker`, `terminalAddAuthor` and `terminalAddManager` **in a new, unsaved notebook**, closed without saving, so that no key is written to a file.
- **Session tokens:** SHA-256 hashes only.
- **The log:** one private object per event, under `Terminal/log/<date>/`. No log entry holds a passkey, a key or a token.
- **All objects are private** to the owner's account. The only public object is the endpoint `TerminalKernel`. It runs as the owner, so it can read and write the private store, but it exposes only the actions above.

## 5. On the device

- The passkey and the token are kept **in memory only**: never in local storage, cookies or the address bar. Closing or reloading the page ends the session on that device; the worker signs in again.
- The page keeps, on the device: the station name, the conversation id for messages, the messages sent, and the position where allowed. None of these are secrets.
- The passkey field is a password field; the page shows the warning "Unauthorized Access Forbidden".

## 6. What the Journal adds

- The Journal reads the history with a **manager key** (`terminalAddManager`), sent once for a manager session token, by the same scheme. Only a manager token reads the history; groups may be saved with a manager token or an author token (the admin tool); a worker's token does neither.
- Every request now also carries a **context**: time zone, local time, a device summary, and the position where the browser allowed it. The service also reads the **IP address** from the request. These are personal data. Telling the workers about them, and deciding how long they are kept, are the employer's responsibility (agreed 24 November 2026).

## 7. Not yet covered (planned)

- **Brute-force limit:** slow down or refuse sign-in after repeated wrong passkeys from one page or IP address. The refusals are already logged.
- **Ending every session at once:** for example after a passkey is changed (`terminalEndSessions[worker]`).
- **Clearing old sessions** and old log entries after an agreed time.
- **A queue that survives a reload:** clicks saved on the device would carry the token, never the passkey.

## 8. Testing

- `tests/TerminalTests.nb` checks, among other things:
  - keys are kept only as hashes;
  - tokens are 64 hex characters, different every time, and stored only as hashes;
  - a made-up, ended or expired token is refused, and a worker token is no author token;
  - quoted keys work;
  - the context is logged.

  It runs in its own `wolframscript` process with every cloud write blocked, and it **stops at once if that block is ever lost**. Loading `HTTPRequestData` inside the block clears it, so the test loads it first.
- `tests/clicks.py` checks, in a browser against a stand-in service:
  - ticks carry the token and never the passkey;
  - the passkey is gone from the page once signed in;
  - sign-out ends the token.

---
© Computational Classnotes · CC BY-NC-SA 4.0
