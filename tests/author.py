# Checks of the job-authoring tool in test mode (?mock=1; author key 123): sign-in, the formatting toolbar,
# the WYSIWYG editor, the preview, sub-task IDs, the checks before saving, saving and reopening.
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
        ok('opened job shows formatting, not marks', await pg.eval_on_selector('#spec', 'e=>!!e.querySelector("b") && !!e.querySelector(".c-red") && !!e.querySelector("ul li") && !e.textContent.includes("**")'))
        ok('opening a job leaves it unchanged', await pg.is_hidden('#dirty'))
        # a new job, with the WYSIWYG toolbar
        SEL = """([t]) => { const ed = document.querySelector('#spec'), w = document.createTreeWalker(ed, NodeFilter.SHOW_TEXT), i = ed.textContent.indexOf(t);
                   if (i < 0) return false; const r = document.createRange(); let n, pos = 0, started = false;
                   while ((n = w.nextNode())) { const L = n.nodeValue.length;
                     if (!started && pos + L > i) { r.setStart(n, i - pos); started = true; }
                     if (started && pos + L >= i + t.length) { r.setEnd(n, i + t.length - pos); break; } pos += L; }
                   const s = getSelection(); s.removeAllRanges(); s.addRange(r); return true; }"""
        mk = lambda: pg.evaluate('specValue()')
        await pg.click('#newJob'); await pg.fill('#jobId', 'DL'); await pg.fill('#jobName', 'Dispatch log')
        await pg.click('#spec'); await pg.keyboard.type('Use a pen')
        await pg.evaluate(SEL, ['pen']); await pg.click('[data-f=b]')
        ok('B makes the selection bold, as seen', await pg.eval_on_selector('#spec', 'e=>e.querySelector("b")?.textContent==="pen"') and await mk() == 'Use a **pen**')
        await pg.evaluate(SEL, ['Use']); await pg.click('[data-c=blue]')
        ok('a colour colours the selection', await pg.eval_on_selector('#spec', 'e=>e.querySelector(".c-blue")?.textContent==="Use"') and await mk() == '[blue]Use[/blue] a **pen**')
        await pg.evaluate(SEL, ['pen']); await pg.click('[data-f=i]')
        ok('bold and italic together draw correctly', await pg.eval_on_selector('#pvSpec', 'e=>!!e.querySelector("b i, i b") && e.textContent.trim()==="Use a pen"'))
        await pg.evaluate(SEL, ['Use a pen']); await pg.click('[data-f=clear]')
        ok('Clear removes the formatting', await mk() == 'Use a pen' and await pg.eval_on_selector('#spec', 'e=>!e.querySelector("b,i,span")'))
        await pg.click('#spec'); await pg.keyboard.press('End'); await pg.keyboard.press('Enter'); await pg.keyboard.type('first point')
        await pg.click('[data-f=ul]'); ok('List makes bullet points', await pg.eval_on_selector('#spec', 'e=>!!e.querySelector("ul li")') and '- first point' in await mk())
        await pg.click('#spec'); await pg.keyboard.press('Control+End'); await pg.keyboard.press('Enter'); await pg.keyboard.press('Enter')
        await pg.evaluate("""() => { const d = new DataTransfer(); d.setData('text/html', '<b>bold</b><script>alert(1)<\\/script><img src=x onerror=alert(2)>'); d.setData('text/plain', 'pasted <script>alert(1)</script>');
                                 document.querySelector('#spec').dispatchEvent(new ClipboardEvent('paste', { clipboardData: d, bubbles: true, cancelable: true })); }""")
        ok('paste brings plain text only', await pg.eval_on_selector('#spec', 'e=>!e.querySelector("script,img") && e.textContent.includes("pasted <script>")'))
        ok('the preview escapes HTML', await pg.eval_on_selector('#pvSpec', 'e=>!e.querySelector("script,img") && e.textContent.includes("<script>")'))
        await pg.evaluate("setSpec('[green]ok[/green] **fine**')"); await pg.evaluate("changed()")
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
        ok('test mode says the job stayed in this browser', 'this browser only' in await pg.inner_text('#estat') and 'test mode' in await pg.inner_text('#save'))
        ok('saved, listed, no longer marked unsaved', 'Dispatch log' in await pg.inner_text('#jobs') and await pg.is_hidden('#dirty'))
        await pg.reload(); await pg.fill('#key', '123'); await pg.press('#key', 'Enter'); await pg.wait_for_selector('#work:not([hidden])')
        await pg.click('#jobs button:has-text("Dispatch log")'); await pg.wait_for_function("document.querySelector('#jobId').value==='DL'")
        ok('reopened after a reload, as saved', await pg.input_value('.sub-row:first-child .tx') == 'Sign the log' and await pg.eval_on_selector('#spec', 'e=>e.querySelector(".c-green")?.textContent==="ok"'))
        # end to end in test mode: a job saved in the authoring tool appears on the demo terminal (same site, same browser)
        import subprocess, sys, time
        srv = subprocess.Popen([sys.executable, '-I', '-m', 'http.server', '8766', '--directory', ROOT], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
        try:
            ctx = await b.new_context(); a2 = await ctx.new_page(); a2.on('pageerror', lambda e: errs.append(str(e)))
            await a2.goto('http://localhost:8766/author/?mock=1'); await a2.fill('#key', '123'); await a2.press('#key', 'Enter'); await a2.wait_for_selector('#work:not([hidden])')
            await a2.click('#newJob'); await a2.fill('#jobId', 'ZZ'); await a2.fill('#jobName', 'My new job'); await a2.evaluate("setSpec('[blue]Hello[/blue] from the author')"); await a2.evaluate('changed()')
            await a2.fill('.sub-row .tx', 'Do the thing'); await a2.click('#save'); await a2.wait_for_function("document.querySelector('#estat').textContent.startsWith('Saved')")
            t2 = await ctx.new_page(); t2.on('pageerror', lambda e: errs.append(str(e))); await t2.goto('http://localhost:8766/demo/')
            await t2.fill('#passkey', '123'); await t2.press('#passkey', 'Enter'); await t2.wait_for_selector('#taskBar:not([hidden])')
            names = await t2.eval_on_selector('#task', 's=>[...s.options].slice(1).map(o=>o.textContent)')
            ok('the demo terminal lists the authored jobs', 'My new job' in names and 'Morning inspection' in names)
            await t2.select_option('#task', label='My new job'); await t2.wait_for_selector('#subtasks li')
            ok('the authored job fills the terminal screen', 'ZZ-01' in await t2.inner_text('#subtasks') and await t2.eval_on_selector('#specifics', 'e=>!!e.querySelector(".c-blue")'))
            await ctx.close()
        finally: srv.terminate()
        ok('copyright and build in the footer', '© Computational Classnotes · CC BY-NC-SA 4.0' in await pg.inner_text('footer') and 'Build 2026.' in await pg.inner_text('footer'))
        ok('no page errors', not errs)
        if errs: print(errs)
        await pg.screenshot(path='/tmp/author.png')
        await b.close()
asyncio.run(main())
bad = [n for n, c in R if not c]
print(f"{len(R) - len(bad)}/{len(R)} passed", "FAILED: " + "; ".join(bad) if bad else "")
