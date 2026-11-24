# Checks of messaging and the Emergency button in test mode (?mock=1): the coloured status, replies, failure and retry.
# Run from anywhere:  python3 -I tests/messaging.py   (same requirements as e2e.py; CHROME=/path optional)
# © Computational Classnotes · CC BY-NC-SA 4.0
import asyncio, json, html, os, tempfile
from playwright.async_api import async_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
R = []
def ok(n, c): R.append((n, bool(c)))
def demo():
    t = open(os.path.join(ROOT, 'terminal-template.html'), encoding='utf-8').read()
    cfg = {"id": "terminal-test", "made": "2026-11-24T00:00:00Z", "appName": "Test Station", "short": "Test",
           "tasks": [{"name": "Morning inspection", "url": "https://example.invalid/a"}, {"name": "Label printer", "url": "https://example.invalid/b"}],
           "auth": {"mode": "remote", "url": "https://example.invalid/svc"}, "sendPasskey": False, "builder_build": "test", "mock": True}
    f = os.path.join(tempfile.mkdtemp(prefix='terminal-msg-'), 'page.html')
    open(f, 'w', encoding='utf-8').write(t.replace('__APP_NAME__', html.escape(cfg['appName'])).replace('__CONFIG__', json.dumps(cfg).replace('<', '\\u003c'), 1))
    return f
async def main():
    f = demo()
    async with async_playwright() as p:
        b = await p.chromium.launch(**({'executable_path': os.environ['CHROME']} if os.environ.get('CHROME') else {}), args=['--no-sandbox'])
        pg = await b.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://' + f)
        dot = lambda: pg.eval_on_selector('#msgs li .dot', 'd=>d.className')
        ok('Install app shown at the top', await pg.is_visible('#installBtn'))
        await pg.click('#installBtn'); await pg.wait_for_selector('#nameWin:not([hidden])')
        ok('Install asks for the installation ID first', 'Name this installation' in await pg.inner_text('#nameWin'))
        await pg.fill('#stationIn', '-bad'); await pg.click('#nameYes'); ok('a bad ID is refused', 'Use 1–40' in await pg.inner_text('#nameStat') and await pg.is_visible('#nameWin'))
        await pg.fill('#stationIn', 'Mail-Room1'); await pg.press('#stationIn', 'Enter'); await pg.wait_for_selector('#nameWin', state='hidden')
        ok('ID printed in the title, then the install explanation', (await pg.inner_text('#appName')).strip()=='Test Station (Mail-Room1)' and await pg.title()=='Test Station (Mail-Room1)' and 'Installation ID saved: Mail-Room1' in await pg.inner_text('#installMsg') and 'cannot be installed' in await pg.inner_text('#installMsg'))
        ok('warning under sign-in', 'Unauthorized Access Forbidden' in await pg.inner_text('#loginPanel'))
        # messages
        await pg.fill('#message', 'I cannot sign in'); await pg.press('#message', 'Enter')
        await pg.wait_for_function("document.querySelector('#msgs .dot.delivered')"); ok('yellow when delivered', 'delivered' in await dot())
        ok('manager sees not signed in', 'not signed in' in await pg.inner_text('#mockRows'))
        ok('manager sees the installation ID', 'Mail-Room1' in await pg.inner_text('#mockRows'))
        await pg.click('[data-act=open]'); ok('green when opened', 'opened' in await dot())
        await pg.click('[data-act=reply]'); await pg.fill('#mockRows input', 'Coming now'); await pg.press('#mockRows input', 'Enter')
        ok('reply under the message', 'Coming now' in await pg.inner_text('#msgs'))
        await pg.click('[data-act=handle]'); ok('blue when handled', 'handled' in await dot())
        await pg.check('#mockFail'); await pg.fill('#message', 'Second'); await pg.click('#send')
        await pg.wait_for_function("document.querySelector('#msgs .dot.failed')"); ok('red with Send again', 'Send again' in await pg.inner_text('#msgs'))
        await pg.click('#msgs .again'); await pg.wait_for_function("!document.querySelector('#msgs .dot.failed') && !document.querySelector('#msgs .dot.sending')")
        ok('Send again delivers', 'delivered' in await dot())
        ok('every dot labelled', await pg.eval_on_selector_all('#msgs .dot', 'd=>d.every(x=>x.getAttribute("aria-label"))'))
        # emergency, before sign-in
        ok('Emergency button before sign-in', await pg.is_visible('#emergency'))
        await pg.check('#mockFail'); await pg.click('#emergency')
        await pg.wait_for_function("document.querySelector('#emDot').classList.contains('failed')")
        ok('failed emergency says so and what to do', 'NOT reached' in await pg.inner_text('#emText') and 'raise the alarm' in await pg.inner_text('#emHelp'))
        await pg.wait_for_function("document.querySelector('#emDot').classList.contains('delivered')", timeout=9000); ok('retried automatically', True)
        await pg.click('#emergency'); await pg.wait_for_timeout(300)
        ok('second press raises no second emergency', await pg.eval_on_selector_all('#mockRows tr', 'r=>r.filter(x=>x.textContent.includes("EMERGENCY")).length') == 1)
        await pg.click('[data-act=emopen]'); ok('emergency green when seen', await pg.eval_on_selector('#emDot', 'd=>d.classList.contains("opened")'))
        await pg.click('[data-act=emhandle]'); ok('emergency blue when handled', await pg.eval_on_selector('#emDot', 'd=>d.classList.contains("handled")'))
        # signed in: the task travels with the message
        await pg.fill('#passkey', '123'); await pg.press('#passkey', 'Enter'); await pg.wait_for_selector('#taskBar:not([hidden])')
        await pg.select_option('#task', '0'); await pg.wait_for_selector('#subtasks li')
        ok('test-mode specifics shown above the checkboxes', await pg.is_visible('#specifics') and 'specifics of this job' in await pg.inner_text('#specifics'))
        ok('specifics drawn with their formatting', await pg.eval_on_selector('#specifics', 'e=>!!e.querySelector("b") && !!e.querySelector("i") && !!e.querySelector(".c-red") && !!e.querySelector("ul li")'))
        await pg.fill('#message', 'Come see me ASAP'); await pg.click('#send'); await pg.wait_for_timeout(700)
        ok('signed-in message carries the task', 'job: Morning inspection' in await pg.inner_text('#mockRows'))
        bx = await pg.query_selector_all('#subtasks input')
        for x in bx: await x.check()
        await pg.click('#logout'); await pg.wait_for_selector('#sure:not([hidden])')
        await pg.click('#emergency', timeout=3000); await pg.wait_for_timeout(600)
        ok('Emergency can be pressed while ARE YOU SURE? is open', await pg.eval_on_selector_all('#mockRows tr', 'r=>r.filter(x=>x.textContent.includes("EMERGENCY")).length') == 1 and 'sent at' in await pg.inner_text('#emText'))
        ok('no page errors', not errs)
        if errs: print(errs)
        await b.close()
    os.remove(f); os.rmdir(os.path.dirname(f))
asyncio.run(main())
bad = [n for n, c in R if not c]
print(f"{len(R) - len(bad)}/{len(R)} passed", "FAILED: " + "; ".join(bad) if bad else "")
