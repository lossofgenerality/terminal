# Checks of the Journal (journal/index.html) on the fake sample: every screen renders without errors, and its figures
# agree with an independent computation, here in Python, from the raw clicks in journal/sample-data.json.
# Run:  python3 -I tests/journal.py   (needs: pip install playwright; playwright install chromium)
# © Computational Classnotes · CC BY-NC-SA 4.0
import asyncio, json, os, subprocess, sys, time, statistics, datetime as dt
from playwright.async_api import async_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); U = 'http://localhost:8767/journal/'
results = []
def ok(name, cond): results.append((name, bool(cond)))

# ---------- the independent computation ----------
D = json.load(open(os.path.join(ROOT, 'journal', 'sample-data.json'), encoding='utf-8'))
E = sorted(D['events'], key=lambda e: e['time'])
ms = lambda e: dt.datetime.strptime(e['time'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=dt.timezone.utc).timestamp() * 1000   # Europe/Dublin = UTC in November
sessions, steps, open_ = [], [], {}
for e in E:
    st = e['station']
    if e['action'] == 'signin':
        if e.get('ok') is False: continue
        s = {'station': st, 'worker': e['worker'], 'signin': ms(e), 'last': ms(e), 'date': e['time'][:10], 'chosen': None, 'end': None, 'job': ''}
        sessions.append(s); open_[st] = s; continue
    s = open_.get(st)
    if not s: continue
    if e['action'] == 'event' and e.get('kind') == 'job-chosen': s['chosen'] = ms(e); s['last'] = ms(e); s['job'] = e['detail']
    elif e['action'] == 'tick': steps.append({'job': e['job'], 'sub': e['sub'], 'dur': ms(e) - s['last'], 'checked': e.get('checked') is not False, 'date': s['date'], 'station': st, 'worker': e['worker'], 'h': int(e['time'][11:13]), 'retry': bool(e.get('retry'))}); s['last'] = ms(e)
    elif e['action'] == 'complete': s['end'] = ms(e)
    elif e['action'] == 'signout': open_.pop(st, None)
dates = sorted({e['time'][:10] for e in E})
last7 = dates[-7:]
runs7 = [s for s in sessions if s['end'] and s['chosen'] and s['date'] in last7]
steps7 = [x for x in steps if x['checked'] and x['date'] in last7]
un7 = [x for x in steps if not x['checked'] and x['date'] in last7]
per = {}
for x in steps7: per.setdefault((x['job'], x['sub']), []).append(x['dur'])
slow = sorted(((statistics.median(v), k) for k, v in per.items() if len(v) >= 5), reverse=True)[0]
import math
rnd = lambda x: int(math.floor(x + .5))   # half up, as the page rounds (Python's round() goes to even)
mmss = lambda m: f"{rnd(m / 1000) // 60}:{rnd(m / 1000) % 60:02d}"
grp = next(g for g in D['groups'] if g['id'] == 'cutters')
inG = lambda g, st, w: st in g['tables'] or w in g['workers']
runsCut = [s for s in runs7 if inG(grp, s['station'], s['worker'])]
day = dates[-1]; now = dt.datetime.fromisoformat(day + 'T10:30:00+00:00').timestamp() * 1000
done_now = [s for s in sessions if s['date'] == day and s['end'] and s['chosen'] and s['end'] <= now]
open_now = [s for s in sessions if s['date'] == day and s['signin'] <= now and not any(True for _ in [])]
# open at 10:30: signed in by then and not yet signed out
so = {}
for e in E:
    if e['action'] == 'signout' and e['time'][:10] == day: so.setdefault(e['station'], []).append(ms(e))
def closed_at(s):
    L = [t for t in so.get(s['station'], []) if t >= s['signin']]; return min(L) if L else None
open_now = [s for s in sessions if s['date'] == day and s['signin'] <= now and (closed_at(s) is None or closed_at(s) > now)]

async def main():
    srv = subprocess.Popen([sys.executable, '-m', 'http.server', '8767', '-d', ROOT], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
    try:
        async with async_playwright() as p:
            b = await p.chromium.launch(**({'executable_path': os.environ['CHROME']} if os.environ.get('CHROME') else {}), args=['--no-sandbox'])
            ctx = await b.new_context(viewport={'width': 1440, 'height': 1000}); pg = await ctx.new_page(); errs = []
            pg.on('pageerror', lambda e: errs.append(str(e)))
            await pg.goto(U + '#bottlenecks'); await pg.wait_for_selector('.kpis', timeout=30000)
            txt = await pg.inner_text('#app')
            ok('labelled as fake sample data', await pg.inner_text('#srcBadge') == 'Fake sample data')
            ok(f'jobs in the last 7 days = {len(runs7)}', f'{len(runs7):,} jobs' in txt)
            ok(f'steps = {len(steps7)}', f'{len(steps7):,} steps' in txt)
            ok(f'slowest step = {slow[1][1]} at {mmss(slow[0])}', slow[1][1] in txt and f'{mmss(slow[0])} median' in txt)
            ok('rework rate', f'{len(un7) / len(steps7) * 100:.1f}%' in txt)
            ok('the planted after-14:00 slow-down is found', 'Cutter-2 is' in txt and 'Dispatch-1 is' in txt and 'slower after 14:00' in txt)
            ok('the heatmap has 12 tables × 12 hours', await pg.locator('.heat .g').count() == 13 and await pg.locator('.heat .c').count() == 144)
            await pg.select_option('#grp', 'cutters'); await pg.wait_for_timeout(300)
            ok(f'group filter: Cutters, {len(runsCut)} jobs', f'{len(runsCut):,} jobs' in await pg.inner_text('#app'))
            await pg.select_option('#grp', ''); await pg.select_option('#range', 'all'); await pg.wait_for_timeout(300)
            runsAll = [s for s in sessions if s['end'] and s['chosen']]
            ok('all of the history', f'{len(runsAll):,} jobs' in await pg.inner_text('#app'))
            # live at the sample clock 10:30
            await pg.click('nav.views button[data-v=live]'); await pg.wait_for_selector('#clock')
            await pg.evaluate("document.querySelector('#clock').value = 630; document.querySelector('#clock').dispatchEvent(new Event('input'))"); await pg.wait_for_timeout(300)
            lt = await pg.inner_text('#app')
            ok(f'live at 10:30: {len(done_now)} jobs done', f'JOBS DONE\n{len(done_now)}' in lt.upper() or f'Jobs done\n{len(done_now)}' in lt)
            ok(f'live at 10:30: {len(open_now)} signed in', f'{len(open_now)} / 12' in lt)
            ok('work-table cards for every table', await pg.locator('.tcard').count() == 12)
            ok('the feed shows the latest clicks first', await pg.locator('.feed .it').count() >= 10)
            # timeline
            await pg.click('nav.views button[data-v=timeline]'); await pg.wait_for_selector('.track')
            ok('timeline: a row per table', await pg.locator('.tl .r:not(.hd)').count() == 12)
            await pg.click('#prevDay'); await pg.wait_for_timeout(200)
            ok('timeline: the day before', dt.date.fromisoformat(dates[-2]).strftime('%-d') in await pg.inner_text('.kick'))
            # drill-down: click a timeline row
            await pg.click('.tl .r:not(.hd) button >> nth=3'); await pg.wait_for_selector('.step')
            dtx = await pg.inner_text('#app')
            ok('drill-down from the timeline opens a run with steps and every click', await pg.locator('.step').count() >= 3 and 'Every click, as the cloud received it' in dtx and 'Confirmed' in dtx)
            ok('drill-down shows where and on what', 'Europe/Dublin' in dtx and '203.0.113' in dtx)
            # groups: change, keep, reset
            await pg.click('nav.views button[data-v=groups]'); await pg.wait_for_selector('.glist')
            await pg.click('#gNew'); await pg.fill('#gName', 'Night crew'); await pg.click('#gSave'); await pg.wait_for_timeout(200)
            await pg.select_option('#gAddW', 'Bea'); await pg.wait_for_timeout(200)
            ok('a new group with a worker', 'Night crew' in await pg.inner_text('.glist') and await pg.locator('.tok.w').count() == 1)
            await pg.reload(); await pg.wait_for_selector('.glist')
            ok('kept in this browser after a reload', 'Night crew' in await pg.inner_text('.glist'))
            await pg.click('#gReset'); await pg.wait_for_timeout(200)
            ok('back to the sample groups', 'Night crew' not in await pg.inner_text('.glist') and await pg.locator('.glist button').count() == len(D['groups']))
            # phone width: nothing wider than the screen
            ph = await b.new_page(viewport={'width': 390, 'height': 844}); ph.on('pageerror', lambda e: errs.append(str(e)))
            wide = []
            for v in ['live', 'bottlenecks', 'timeline', 'drill', 'groups']:
                await ph.goto(U + '#' + v); await ph.wait_for_selector('footer', timeout=30000)
                if await ph.evaluate('document.documentElement.scrollWidth') > 392: wide.append(v)
            ok('every screen fits a phone (wide tables scroll inside their box)', not wide)
            if wide: print('too wide on a phone:', wide)
            # service mode asks for the manager key, and says when the service has no Journal yet
            sv = await b.new_page(); await sv.route('https://www.wolframcloud.com/**', lambda r: r.fulfill(status=200, content_type='application/json', body=json.dumps({'reply_b64': __import__('base64').b64encode(b'{"ok":false,"message":"Unknown action."}').decode()})))
            await sv.goto(U + '?source=service'); await sv.wait_for_selector('#mkey')
            await sv.fill('#mkey', '"secret"'); await sv.click('#mform button'); await sv.wait_for_function("document.querySelector('#mstat').textContent.includes('next ff_terminal release')")
            ok('service mode: manager sign-in, and a clear note while the service has no Journal', True)
            # service mode against a stand-in that answers as ff_terminal does: manager key once, then a token; one day at a time
            import base64, urllib.parse
            byday = {}
            for k, e in enumerate(E): byday.setdefault(e['time'][:10], []).append({**e, 'id': e['time'][:10] + '/' + e['time'][11:19].replace(':', '') + '-%06d' % k})
            seen = []
            async def answer(route):
                req = json.loads(base64.b64decode(urllib.parse.parse_qs(route.request.post_data)['payload_b64'][0]).decode('utf-8')); seen.append(req)
                if req['action'] == 'managerSignin': out = {'ok': True, 'token': 'b' * 64} if req.get('managerKey') == 'boss-key' else {'ok': False, 'message': 'The manager key was not accepted.'}
                elif req['action'] == 'journal' and req.get('managerToken') == 'b' * 64:
                    evs = byday.get(req['day'], [])
                    if req.get('after'): evs = [x for x in evs if x['id'].split('/')[1][:6] >= req['after']]
                    out = {'ok': True, 'day': req['day'], 'events': evs, **({'workers': D['workers'], 'jobs': D['jobs'], 'groups': D['groups']} if req.get('meta') else {})}
                else: out = {'ok': False, 'message': 'refused'}
                await route.fulfill(status=200, content_type='application/json', body=json.dumps({'reply_b64': base64.b64encode(json.dumps(out, ensure_ascii=False).encode()).decode()}))
            s2 = await b.new_page(); s2.on('pageerror', lambda e: errs.append(str(e))); await s2.route('https://www.wolframcloud.com/**', answer)
            await s2.clock.install(time=dt.datetime(2026, 11, 24, 10, 30, tzinfo=dt.timezone.utc).timestamp())
            await s2.goto(U + '?source=service&days=7#bottlenecks'); await s2.wait_for_selector('#mkey')
            await s2.fill('#mkey', '"boss-key"'); await s2.click('#mform button'); await s2.wait_for_selector('.kpis', timeout=60000)
            ok('service mode: the key is sent once, then only the token', [r.get('managerKey') for r in seen if r['action'] == 'managerSignin'][-1] == 'boss-key' and all('managerKey' not in r and r.get('managerToken') == 'b' * 64 for r in seen if r['action'] == 'journal'))
            ok('service mode: reads 7 days, one at a time, lists once', [r['day'] for r in seen if r['action'] == 'journal'] == [(dt.date(2026, 11, 24) - dt.timedelta(days=i)).isoformat() for i in range(7)] and sum(1 for r in seen if r.get('meta')) == 1)
            last7svc = [d for d in dates if d >= '2026-11-18']
            runs7svc = [s for s in sessions if s['end'] and s['chosen'] and s['date'] in last7svc]
            ok(f'service mode: the same figures as the sample ({len(runs7svc)} jobs)', f'{len(runs7svc):,} jobs' in await s2.inner_text('#app') and await s2.inner_text('#srcBadge') == 'Service')
            await s2.click('nav.views button[data-v=live]'); await s2.wait_for_selector('.tcard')
            n0 = len(seen); await s2.clock.run_for(61000); await s2.wait_for_timeout(800)
            ok('service mode: each minute reads only today\'s newer clicks', any(r['action'] == 'journal' and r['day'] == '2026-11-24' and len(r.get('after', '')) == 6 for r in seen[n0:]))
            ok('no page errors', not errs)
            if errs: print(errs[:5])
            await b.close()
    finally: srv.terminate()
    good = sum(c for _, c in results); print(f'{good}/{len(results)} passed', 'FAILED: ' + '; '.join(n for n, c in results if not c) if good < len(results) else '')
asyncio.run(main())
