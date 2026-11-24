# End-to-end checks for the CCN Terminal builder and the pages it makes.
# Run from anywhere:  python3 -I tests/e2e.py   (needs: pip install playwright; playwright install chromium)
# Set CHROME=/path/to/chrome to use an installed Chrome instead of Playwright's Chromium.
# © Computational Classnotes · CC BY-NC-SA 4.0
import asyncio, zipfile, io, json, shutil, subprocess, sys, time, os, tempfile
from playwright.async_api import async_playwright
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE); SRV=os.path.join(tempfile.mkdtemp(prefix='terminal-test-'), 'srv'); U='http://localhost:8765'
results=[]
def ok(name, cond): results.append((name, bool(cond)))
async def tick_all(t, leave=0):
    boxes=await t.query_selector_all('#subtasks input')
    for bx in boxes[:len(boxes)-leave]: await bx.check()
async def signout(t, yes=True):
    await t.click('#logout'); await t.wait_for_selector('#sure:not([hidden])')
    await t.click('#sureYes' if yes else '#sureNo')
async def signin(t, key):
    await t.fill('#passkey', key); await t.press('#passkey','Enter')
    try: await t.wait_for_selector('#taskBar:not([hidden])', timeout=5000)
    except Exception: print('sign-in status:', await t.inner_text('#lstat')); raise
async def opts(t): return await t.eval_on_selector('#task','s=>[...s.options].slice(1).map(o=>o.textContent)')
async def build(pg, mode, key_or_url, name):
    await pg.fill('#appName', name)
    await pg.check(f'input[name=authMode][value={mode}]')
    if mode=='hash': await pg.fill('#pk1',key_or_url); await pg.fill('#pk2',key_or_url)
    else: await pg.fill('#authUrl',key_or_url)
    await pg.evaluate("document.body.dataset.built=''"); await pg.click('#build'); await pg.wait_for_function("document.body.dataset.built==='yes'")
async def zip_of(pg):
    async with pg.expect_download() as d: await pg.click('#dlZip')
    z=zipfile.ZipFile(io.BytesIO(open(await (await d.value).path(),'rb').read())); root=[n for n in z.namelist() if n.endswith('index.html')][0][:-10]
    return z, root
async def main():
    shutil.rmtree(SRV, ignore_errors=True); shutil.copytree(ROOT, SRV, ignore=shutil.ignore_patterns('.git', 'tests'))
    srv=subprocess.Popen([sys.executable,'-I',os.path.join(HERE, 'server.py'),SRV]); time.sleep(1)
    try:
        async with async_playwright() as p:
            b=await p.chromium.launch(**({'executable_path': os.environ['CHROME']} if os.environ.get('CHROME') else {}), args=['--no-sandbox'])
            ctx=await b.new_context(accept_downloads=True); pg=await ctx.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
            await pg.goto(U+'/index.html')
            ok('builder footer stamp', 'Build 2026.' in await pg.inner_text('#updatedStamp'))
            ok('service is the default', await pg.is_checked('input[name=authMode][value=remote]'))
            await pg.click('#build'); await pg.wait_for_selector('#errs:not([hidden])')
            e=await pg.inner_text('#errs'); ok('validation: name, jobs, service address', 'name' in e and 'job' in e and 'passkey service' in e)
            await pg.fill('#folder','sfx-ray'); await pg.uncheck('#mockPreview')
            await pg.fill('#tasks','Morning inspection\nLabel printer\nDispatch log | '+U+'/examples/dispatch-log.txt'); await pg.fill('#pattern',U+'/examples/{slug}.json')
            ok('pattern resolves slug', 'examples/morning-inspection.json' in await pg.inner_text('#taskTable tbody'))
            await pg.check('input[name=authMode][value=hash]'); await pg.fill('#appName','Packing Station — Daily Checks'); await pg.fill('#pk1','correct-horse'); await pg.fill('#pk2','correct-hors'); await pg.click('#build')
            await pg.wait_for_selector('#errs:not([hidden])'); ok('passkey mismatch caught', 'differ' in await pg.inner_text('#errs'))
            # ---- A: in-page check ----
            await pg.set_input_files('#logoFile', os.path.join(ROOT,'icons','icon-192.png')); await pg.wait_for_selector('#logoPv:not([hidden])')
            await build(pg,'hash','correct-horse','Packing Station — Daily Checks')
            ok('instance folder name', 'sfx-ray/packing-station-daily-checks-2026' in await pg.inner_text('#where'))
            z,root=await zip_of(pg); names=z.namelist()
            want=['index.html','README.md','notes.md','terminal-data.json','manifest.webmanifest','sw.js']+['icons/'+n for n in ['icon-192.png','icon-512.png','icon-maskable-512.png','apple-touch-icon.png','favicon-32.png']]
            ok('zip has eye-witness file set', all(root+w in names for w in want) and z.testzip() is None)
            ok('logo built into the page', 'data:image/png;base64,' in z.read(root+'index.html').decode())
            ok('passkey nowhere in the zip', all('correct-horse' not in z.read(n).decode('utf-8','ignore') for n in names))
            json.loads(z.read(root+'manifest.webmanifest')); cfg=json.loads(z.read(root+'terminal-data.json'))['data']
            ok('data json: tasks, hash, no logoutRule', len(cfg['tasks'])==3 and len(cfg['auth']['hash'])==64 and 'logoutRule' not in cfg)
            ok('copyright in page/notes/readme', all('© Computational Classnotes · CC BY-NC-SA 4.0' in z.read(root+f).decode() for f in ['index.html','notes.md','README.md']))
            z.extractall(SRV+'/out')
            t=await ctx.new_page(); t.on('pageerror', lambda e: errs.append(str(e))); await t.goto(U+'/out/'+root+'index.html')
            ok('tasks hidden before sign-in', await t.is_hidden('#taskBar') and await t.is_hidden('#logoutPanel'))
            ok('logo shown beside the title', await t.is_visible('#logo') and (await t.eval_on_selector('#logo','i=>i.naturalWidth'))>0)
            ok('passkey placeholder', await t.get_attribute('#passkey','placeholder')=='Enter passkey')
            await t.fill('#passkey','wrong-one'); await t.press('#passkey','Enter'); await t.wait_for_function("document.querySelector('#lstat').textContent.includes('not accepted')")
            ok('wrong passkey refused', await t.is_hidden('#taskBar'))
            await signin(t,'correct-horse'); ok('session 1: three jobs', len(await opts(t))==3)
            ok('sign-out disabled before choosing', await t.is_disabled('#logout'))
            await t.select_option('#task','0'); await t.wait_for_selector('#subtasks li')
            ok('may change task before ticking', await t.is_enabled('#task'))
            ok('JSON sub-task IDs shown before the text', (await t.inner_text('#subtasks li:first-child')).strip().startswith('MI-01')); ok('JSON specifics shown, read-only', 'safety boots' in await t.inner_text('#specifics') and await t.eval_on_selector('#specifics','e=>e.tagName')=='DIV' and not await t.eval_on_selector('#specifics','e=>e.isContentEditable') and await t.is_visible('#specifics'))
            await tick_all(t, leave=1); ok('task fixed after first tick', await t.is_disabled('#task'))
            ok('sign-out disabled with one left', await t.is_disabled('#logout'))
            await tick_all(t); ok('sign-out enabled when the task is complete', await t.is_enabled('#logout'))
            await signout(t, yes=False); ok('ARE YOU SURE? Cancel keeps the session', await t.is_visible('#taskBar') and await t.is_hidden('#sure') and 'ARE YOU SURE?' in await t.inner_text('#sureT'))
            await t.fill('#message','hello'); await t.click('#send'); await t.wait_for_selector('#msgs .dot.failed'); ok('in-page check: message shows red, no service', 'Send again' in await t.inner_text('#msgs'))
            await signout(t); await t.wait_for_selector('#loginPanel:not([hidden])')
            ok('signed out, task recorded', 'recorded as done' in await t.inner_text('#lstat') and await t.is_hidden('#taskBar'))
            await signin(t,'correct-horse'); o=await opts(t); ok('session 2: one job fewer', o==['Label printer','Dispatch log'])
            await t.select_option('#task', label='Label printer'); await t.wait_for_selector('#subtasks li'); ok('object list parsed', 'Clean the print head' in await t.inner_text('#subtasks')); ok('no specifics: box hidden', await t.is_hidden('#specifics')); ok('no IDs given: numbered 1, 2, 3', [ (await x.inner_text()).strip() for x in await t.query_selector_all('#subtasks .sid') ]==['1','2','3'])
            await tick_all(t); await signout(t); await t.wait_for_selector('#loginPanel:not([hidden])')
            await signin(t,'correct-horse'); await t.select_option('#task', label='Dispatch log'); await t.wait_for_selector('#subtasks li')
            ok('plain-text IDs before the bar', [ (await x.inner_text()).strip() for x in await t.query_selector_all('#subtasks .sid') ]==['DL-01','DL-02','DL-03']); ok('plain-text list parsed, specifics split at ---', 'Sign the log' in await t.inner_text('#subtasks') and 'blue folder' in await t.inner_text('#specifics') and 'blue folder' not in await t.inner_text('#subtasks') and len(await t.query_selector_all('#subtasks li'))==3); await tick_all(t); await signout(t); await t.wait_for_selector('#loginPanel:not([hidden])')
            await signin(t,'correct-horse'); ok('all done: none offered, sign-out open', await opts(t)==[] and await t.is_enabled('#logout') and 'Every job is complete' in await t.inner_text('#logoutWhy'))
            ok('footer stamp on instance', 'builder build 2026.' in await t.inner_text('#updatedStamp'))
            # ---- B: the separate service ----
            await build(pg,'remote',U+'/svc','Service Checks'); z,root=await zip_of(pg); z.extractall(SRV+'/out')
            ctx2=await b.new_context(); s=await ctx2.new_page(); s.on('pageerror', lambda e: errs.append(str(e))); await s.goto(U+'/out/'+root+'index.html')
            await s.fill('#passkey','nope'); await s.press('#passkey','Enter'); await s.wait_for_function("document.querySelector('#lstat').textContent.includes('not accepted')"); ok('service refuses wrong passkey', True)
            await signin(s,'service-pass'); await s.select_option('#task','0'); await s.wait_for_selector('#subtasks li'); await tick_all(s)
            await s.evaluate("fetch('/svc/fail',{method:'POST',body:JSON.stringify({on:true})})"); await s.wait_for_timeout(200)
            await signout(s); await s.wait_for_function("document.querySelector('#logoutWhy').textContent.includes('could not be recorded')")
            ok('refused record keeps the session', await s.is_visible('#taskBar') and await s.is_enabled('#logout'))
            await s.evaluate("fetch('/svc/fail',{method:'POST',body:JSON.stringify({on:false})})"); await s.wait_for_timeout(200)
            await signout(s); await s.wait_for_selector('#loginPanel:not([hidden])')
            ctx3=await b.new_context(); s2=await ctx3.new_page(); await s2.goto(U+'/out/'+root+'index.html')   # another device: nothing remembered locally
            await signin(s2,'service-pass'); ok('service record honoured on another device', await opts(s2)==['Label printer','Dispatch log'])
            # ---- C: preview and a missing list ----
            await pg.check('#mockPreview'); await pg.fill('#tasks','Morning inspection\nMissing list'); await build(pg,'hash','correct-horse','Packing Station — Daily Checks')
            fr=pg.frame_locator('#frame'); await fr.locator('#passkey').fill('correct-horse'); await fr.locator('#passkey').press('Enter'); await fr.locator('#taskBar').wait_for(state='visible')
            await fr.locator('#task').select_option('1'); await fr.locator('#subtasks li').first.wait_for()
            ok('mock preview canned', 'Missing list: sub-task 1' in await fr.locator('#subtasks').inner_text())
            await pg.uncheck('#mockPreview'); await build(pg,'hash','correct-horse','Missing Checks')
            async with pg.expect_download() as d3: await pg.click('#dlHtml')
            open(SRV+'/single.html','w').write(open(await (await d3.value).path()).read())
            m=await ctx.new_page(); await m.goto(U+'/single.html'); await signin(m,'correct-horse'); await m.select_option('#task','1'); await m.wait_for_selector('#retryRow:not([hidden])')
            ok('missing list reported, sign-out held', 'could not be loaded' in await m.inner_text('#tstat') and await m.is_disabled('#logout'))
            ok('no page errors', not errs)
            if errs: print(errs)
            await b.close()
    finally: srv.terminate(); shutil.rmtree(os.path.dirname(SRV), ignore_errors=True)
asyncio.run(main())
bad=[n for n,c in results if not c]
print(f"{len(results)-len(bad)}/{len(results)} passed", "FAILED: "+"; ".join(bad) if bad else "")
