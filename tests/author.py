# Checks of the job-authoring tool in test mode (?mock=1; author key 123): sign-in, the formatting toolbar,
# the preview, sub-task IDs, the checks before saving, saving and reopening.
# Run from anywhere:  python3 -I tests/author.py   (same requirements as e2e.py; CHROME=/path optional)
# © Computational Classnotes · CC BY-NC-SA 4.0
import asyncio, os
from playwright.async_api import async_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
R = []
def ok(n, c): R.append((n, bool(c)))
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(**({'executable_path': os.environ['CHROME']} if os.environ.get('CHROME') else {}), args=['--no-sandbox'])
        pg = await b.new_page(viewport={'width': 1400, 'height': 1000}); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.on('dialog', lambda d: asyncio.ensure_future(d.accept()))
        await pg.goto('file://' + os.path.join(ROOT, 'author', 'index.html') + '?mock=1')
        await pg.fill('#key', 'nope'); await pg.press('#key', 'Enter'); await pg.wait_for_function("document.querySelector('#sstat').textContent.includes('not accepted')"); ok('wrong author key refused', await pg.is_hidden('#work'))
        await pg.fill('#key', '123'); await pg.press('#key', 'Enter'); await pg.wait_for_selector('#work:not([hidden])')
        ok('job list loads with the sample job', 'Morning inspection' in await pg.inner_text('#jobs'))
        await pg.click('#jobs button'); await pg.wait_for_function("document.querySelector('#jobId').value==='MI'")
        ok('opening a job fills the form', await pg.input_value('#jobName') == 'Morning inspection' and len(await pg.query_selector_all('.sub-row')) == 4)
        ok('preview draws bold, red and bullets', await pg.eval_on_selector('#pvSpec', 'e=>!!e.querySelector("b") && !!e.querySelector(".c-red") && !!e.querySelector("ul li")'))
        ok('preview shows sub-task IDs', 'MI-01' in await pg.inner_text('#pvSubs'))
        # a new job, with the toolbar
        await pg.click('#newJob'); await pg.fill('#jobId', 'DL'); await pg.fill('#jobName', 'Dispatch log')
        await pg.fill('#spec', 'Use a pen'); await pg.eval_on_selector('#spec', 'e=>e.setSelectionRange(6,9)'); await pg.click('[data-f=b]')
        ok('B wraps the selection', await pg.input_value('#spec') == 'Use a **pen**')
        await pg.eval_on_selector('#spec', 'e=>e.setSelectionRange(0,3)'); await pg.click('[data-c=blue]')
        ok('a colour wraps the selection', await pg.input_value('#spec') == '[blue]Use[/blue] a **pen**')
        await pg.eval_on_selector('#spec', 'e=>e.setSelectionRange(0,0)'); await pg.press('#spec', 'Control+i')
        ok('Ctrl+I adds italic', '*text*' in await pg.input_value('#spec'))
        await pg.fill('#spec', '<script>alert(1)</script> and [green]ok[/green]'); 
        ok('the preview escapes HTML', await pg.eval_on_selector('#pvSpec', 'e=>!e.querySelector("script") && e.textContent.includes("<script>") && !!e.querySelector(".c-green")'))
        await pg.fill('.sub-row .tx', 'Open the dispatch log'); await pg.click('#addSub'); await pg.fill('.sub-row:last-child .tx', 'Sign the log')
        ok('sub-tasks without IDs are numbered from the job ID', 'DL-01' in await pg.inner_text('#pvSubs') and 'DL-02' in await pg.inner_text('#pvSubs'))
        await pg.click('.sub-row:last-child [data-a=up]'); ok('reordering moves the sub-task', (await pg.inner_text('#pvSubs')).strip().startswith('DL-01 Sign the log'))
        ok('unsaved changes are marked', await pg.is_visible('#dirty'))
        # checks before saving
        await pg.fill('.sub-row:first-child .id', 'X'); await pg.fill('.sub-row:last-child .id', 'X'); await pg.click('#save')
        await pg.wait_for_selector('#errs:not([hidden])'); ok('duplicate sub-task IDs refused', 'used twice' in await pg.inner_text('#errs'))
        await pg.fill('.sub-row:first-child .id', ''); await pg.fill('.sub-row:last-child .id', ''); await pg.fill('#jobId', 'mi'); await pg.click('#save')
        await pg.wait_for_selector('#errs:not([hidden])'); ok('a job ID already in use refused', 'already has the ID' in await pg.inner_text('#errs'))
        await pg.fill('#jobId', 'DL'); await pg.click('#save'); await pg.wait_for_function("document.querySelector('#estat').textContent.startsWith('Saved')")
        ok('saved, listed, no longer marked unsaved', 'Dispatch log' in await pg.inner_text('#jobs') and await pg.is_hidden('#dirty'))
        await pg.reload(); await pg.fill('#key', '123'); await pg.press('#key', 'Enter'); await pg.wait_for_selector('#work:not([hidden])')
        await pg.click('#jobs button:has-text("Dispatch log")'); await pg.wait_for_function("document.querySelector('#jobId').value==='DL'")
        ok('reopened after a reload, as saved', await pg.input_value('.sub-row:first-child .tx') == 'Sign the log' and '[green]ok[/green]' in await pg.input_value('#spec'))
        ok('copyright and build in the footer', '© Computational Classnotes · CC BY-NC-SA 4.0' in await pg.inner_text('footer') and 'Build 2026.' in await pg.inner_text('footer'))
        ok('no page errors', not errs)
        if errs: print(errs)
        await pg.screenshot(path='/tmp/author.png')
        await b.close()
asyncio.run(main())
bad = [n for n, c in R if not c]
print(f"{len(R) - len(bad)}/{len(R)} passed", "FAILED: " + "; ".join(bad) if bad else "")
