# Checks of the click reports (rules 1-3) against the stand-in service on the real wire (payload_b64 in, reply_b64 out):
# every tick and untick, the station named, the install, the job chosen, Sign out Cancel and Yes are sent at once, in order,
# with time, station, job and sub-task ID; with no connection they wait under a "waiting to send" sign, and sign-out completes
# only once the service has them all. Also the same in test mode (?mock=1), where the page plays the service.
# Run:  python3 -I tests/clicks.py   (needs: pip install playwright; playwright install chromium)
# © Computational Classnotes · CC BY-NC-SA 4.0
import asyncio, zipfile, io, json, shutil, subprocess, sys, time, os, tempfile
from playwright.async_api import async_playwright
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE); SRV=os.path.join(tempfile.mkdtemp(prefix='terminal-clicks-'), 'srv'); U='http://localhost:8765'
results=[]
def ok(name, cond): results.append((name, bool(cond)))
JOB='Prüfung 日本 ✓'
async def clicks(p): return await p.evaluate("fetch('/svc/clicks').then(r=>r.json())")
async def offline(p, on): await p.evaluate(f"fetch('/svc/offline',{{method:'POST',body:JSON.stringify({{on:{str(on).lower()}}})}})"); await p.wait_for_timeout(150)
async def main():
    shutil.rmtree(SRV, ignore_errors=True); shutil.copytree(ROOT, SRV, ignore=shutil.ignore_patterns('.git', 'tests'))
    srv=subprocess.Popen([sys.executable,'-I',os.path.join(HERE, 'server.py'),SRV]); time.sleep(1)
    try:
        async with async_playwright() as p:
            b=await p.chromium.launch(**({'executable_path': os.environ['CHROME']} if os.environ.get('CHROME') else {}), args=['--no-sandbox'])
            ctx=await b.new_context(accept_downloads=True); pg=await ctx.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
            await pg.goto(U+'/index.html')
            await pg.fill('#appName','Click Checks'); await pg.uncheck('#mockPreview')
            await pg.fill('#tasks',JOB+' | '+U+'/examples/morning-inspection.json\nLabel printer | '+U+'/examples/label-printer.json')
            await pg.check('input[name=authMode][value=remote]'); await pg.fill('#authUrl',U+'/svc')
            await pg.evaluate("document.body.dataset.built=''"); await pg.click('#build'); await pg.wait_for_function("document.body.dataset.built==='yes'")
            async with pg.expect_download() as d: await pg.click('#dlZip')
            z=zipfile.ZipFile(io.BytesIO(open(await (await d.value).path(),'rb').read())); root=[n for n in z.namelist() if n.endswith('index.html')][0][:-10]; z.extractall(SRV+'/out')
            t=await ctx.new_page(); t.on('pageerror', lambda e: errs.append(str(e))); await t.goto(U+'/out/'+root+'index.html')
            # the station, named at install
            await t.click('#installBtn'); await t.wait_for_selector('#nameWin:not([hidden])'); await t.fill('#stationIn','Mail-Room1'); await t.click('#nameYes'); await t.wait_for_timeout(500)
            c=await clicks(t); kinds=[x.get('kind') for x in c]
            ok('station named and install reported', kinds[:2]==['station-named','install'] and c[0]['detail']=='Mail-Room1' and all(x['station']=='Mail-Room1' for x in c[:2]))
            # sign in, choose the job, tick and untick
            await t.fill('#passkey','service-pass'); await t.press('#passkey','Enter'); await t.wait_for_selector('#taskBar:not([hidden])')
            await t.select_option('#task','0'); await t.wait_for_selector('#subtasks li'); await t.wait_for_timeout(300)
            c=await clicks(t); ok('job chosen reported, Unicode intact', c[-1]['kind']=='job-chosen' and c[-1]['detail']==JOB)
            boxes=await t.query_selector_all('#subtasks input'); ids=await t.eval_on_selector_all('#subtasks .sid','L=>L.map(e=>e.textContent)')
            await boxes[0].check(); await boxes[0].uncheck(); await boxes[0].check()
            for bx in boxes[1:]: await bx.check()
            await t.wait_for_timeout(800); c=[x for x in await clicks(t) if x['action']=='tick']
            ok('every tick and untick sent, in order', [(x['sub'],x['checked']) for x in c]==[(ids[0],True),(ids[0],False),(ids[0],True)]+[(i,True) for i in ids[1:]])
            ok('ticks carry time, station, job, passkey', all(x['at'] and x['station']=='Mail-Room1' and x['task']==JOB and x['passkey']=='service-pass' for x in c))
            ok('no waiting sign when all sent', await t.is_hidden('#outbox'))
            # Sign out, then Cancel
            await t.click('#logout'); await t.wait_for_selector('#sure:not([hidden])'); await t.click('#sureNo'); await t.wait_for_timeout(400)
            ok('Sign out Cancel reported', (await clicks(t))[-1]['kind']=='signout-cancel')
            # offline: clicks wait, in order; sign-out waits for them
            n0=len(await clicks(t)); await offline(t,True)
            await boxes[2].uncheck(); await boxes[2].check(); await t.wait_for_selector('#outbox:not([hidden])')
            ok('offline: waiting-to-send sign with the count', 'Waiting to send 2 clicks' in await t.inner_text('#outbox'))
            await t.click('#logout'); await t.wait_for_selector('#sure:not([hidden])'); await t.click('#sureYes'); await t.wait_for_timeout(600)
            ok('offline: sign-out waits, still signed in', await t.is_visible('#taskBar') and 'sign-out completes as soon as' in await t.inner_text('#logoutWhy') and 'Waiting to send 3 clicks' in await t.inner_text('#outbox'))
            ok('offline: nothing reached the service', len(await clicks(t))==n0)
            await offline(t,False); await t.wait_for_selector('#loginPanel:not([hidden])', timeout=12000)
            c=(await clicks(t))[n0:]
            ok('back online: the waiting clicks arrive in order, then sign-out', [(x['action'],x.get('sub') or x.get('kind'),x.get('checked')) for x in c]==[('tick',ids[2],False),('tick',ids[2],True),('event','signout-confirm',None)])
            ok('signed out with the job recorded', 'is recorded as done' in await t.inner_text('#lstat') and await t.is_hidden('#outbox'))
            await t.fill('#passkey','service-pass'); await t.press('#passkey','Enter'); await t.wait_for_selector('#taskBar:not([hidden])')
            ok('one job fewer at the next sign-in', await t.eval_on_selector('#task','s=>[...s.options].slice(1).map(o=>o.textContent)')==['Label printer'])
            # test mode: the page plays the service
            m=await ctx.new_page(); m.on('pageerror', lambda e: errs.append(str(e))); await m.goto(U+'/demo/?mock=1')
            await m.fill('#passkey','123'); await m.press('#passkey','Enter'); await m.wait_for_selector('#taskBar:not([hidden])')
            await m.select_option('#task', index=1); await m.wait_for_selector('#subtasks li'); await m.check('#subtasks input >> nth=0'); await m.wait_for_timeout(500)
            ok('test mode: clicks listed on the manager side', 'ticked' in await m.inner_text('#mockClicks') and 'job-chosen' in await m.inner_text('#mockClicks'))
            await m.check('#mockOffline'); await m.uncheck('#subtasks input >> nth=0'); await m.wait_for_selector('#outbox:not([hidden])')
            ok('test mode: no connection shows the waiting sign', 'Waiting to send 1 click' in await m.inner_text('#outbox'))
            await m.uncheck('#mockOffline'); await m.wait_for_selector('#outbox', state='hidden', timeout=3000)
            ok('test mode: connection back sends it', 'unticked' in await m.inner_text('#mockClicks'))
            ok('no page errors', not errs)
            if errs: print(errs)
            await b.close()
    finally: srv.terminate()
    good=sum(c for _,c in results); print(f'{good}/{len(results)} passed', 'FAILED: '+'; '.join(n for n,c in results if not c) if good<len(results) else '')
asyncio.run(main())
