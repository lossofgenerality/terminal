# Makes journal/sample-data.json: a FAKE history for the CCN Terminal Journal, in the service's own log format.
# 12 work-tables, 12 workers, 7 jobs, groups, Mon 10 – Tue 24 November 2026 (working days, 06:00–18:00, Europe/Dublin = UTC in November).
# Bottlenecks are planted on purpose, so the Journal has something to find:
#   CT-03 "Set the blade depth" is slow and unpredictable; Cutter-2 and Dispatch-1 slow down after 14:00 (second shift);
#   LP-02 "Load the labels" often needs Press again! and is often unticked; new starters (Bea, Ravi) are slower;
#   Mondays are a little slower; Docking-7 stands idle over the middle of the day.
# Deterministic: the same seed gives the same file.   python3 -I journal/tools/make-sample.py
# © Computational Classnotes · CC BY-NC-SA 4.0
import json, random, math, datetime as dt, os
R = random.Random(20261124)
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'sample-data.json')
PAGE = 'ccn-factory'

JOBS = {
    'CT': ('Cut to order', [('CT-01', 'Fetch the sheet', 2.5), ('CT-02', 'Measure the sheet', 3.0), ('CT-03', 'Set the blade depth', 8.5), ('CT-04', 'Cut', 4.0), ('CT-05', 'Stack and label', 3.0)]),
    'MI': ('Morning inspection', [('MI-01', 'Check the floor is clear', 2.0), ('MI-02', 'Inspect the conveyor guard', 3.0), ('MI-03', 'Test the emergency stop', 5.0), ('MI-04', 'Record the room temperature', 1.0)]),
    'LP': ('Label printer', [('LP-01', 'Check the ribbon', 2.0), ('LP-02', 'Load the labels', 4.5), ('LP-03', 'Print a test label', 1.5), ('LP-04', 'Scan the test label', 1.0)]),
    'DL': ('Dispatch log', [('DL-01', 'Count the parcels', 4.0), ('DL-02', 'Check the seals', 3.0), ('DL-03', 'Sign the log', 4.0), ('DL-04', 'Hand over to the driver', 2.5)]),
    'AS': ('Assembly', [('AS-01', 'Lay out the parts', 3.0), ('AS-02', 'Fit the frame', 6.0), ('AS-03', 'Fix the panels', 5.0), ('AS-04', 'Wire the switch', 4.0), ('AS-05', 'Final check', 2.0)]),
    'QA': ('Quality check', [('QA-01', 'Pick a sample', 1.5), ('QA-02', 'Measure against spec', 4.0), ('QA-03', 'Record the result', 1.5), ('QA-04', 'Release or hold', 1.0)]),
    '12': ('Check stocks', [('12-01', 'Do inventory', 4.0), ('12-02', 'setup the cutter', 2.0), ('12-04', 'cut', 3.0)]),
}
# table: floor, jobs it does, first shift worker, second shift worker (or None), device, position (or None)
TABLES = {
    'Cutter-1':   ('First floor', ['CT', 'MI'], 'Aoife', None, 'tablet · Chrome/131 · 1280×800', (53.34981, -6.26031)),
    'Cutter-2':   ('First floor', ['CT'], 'Tomás', 'Aoife', 'tablet · Chrome/131 · 1280×800', (53.34984, -6.26022)),
    'Cutter-3':   ('First floor', ['CT', 'QA'], 'Tomás', None, 'tablet · Chrome/130 · 1280×800', None),
    'Mail-Room1': ('First floor', ['12', 'LP'], 'Bea', None, 'computer · Chrome/131 · 1920×1080', None),
    'Assembly-4': ('First floor', ['AS'], 'Dmitri', 'Lena', 'tablet · Safari/18 · 1180×820', (53.34978, -6.26044)),
    'Assembly-5': ('First floor', ['AS', 'QA'], 'Lena', None, 'tablet · Safari/18 · 1180×820', None),
    'Packing-7':  ('Ground floor', ['MI', 'LP'], 'Niamh', None, 'tablet · Chrome/131 · 1280×800', None),
    'Packing-12': ('Ground floor', ['LP'], 'Seán', 'Niamh', 'phone · Chrome/131 · 412×915', None),
    'Dispatch-1': ('Ground floor', ['DL'], 'Ciara', 'Kofi', 'tablet · Chrome/131 · 1280×800', (53.34969, -6.26010)),
    'Dispatch-2': ('Ground floor', ['DL'], 'Ravi', None, 'phone · Safari/18 · 390×844', None),
    'Docking-7':  ('Ground floor', ['DL'], 'Kofi', 'Ravi', 'tablet · Chrome/129 · 1280×800', None),
    'QA-1':       ('Ground floor', ['QA', 'MI'], 'Marta', None, 'computer · Edg/131 · 1920×1080', None),
}
WORKERS = sorted({w for t in TABLES.values() for w in (t[2], t[3]) if w})
NEW_STARTERS = {'Bea', 'Ravi'}
GROUPS = [
    {'id': 'first', 'name': 'First floor', 'basis': 'Place · machines upstairs', 'color': '#2DD4BF', 'tables': [t for t, v in TABLES.items() if v[0] == 'First floor'], 'workers': []},
    {'id': 'ground', 'name': 'Ground floor', 'basis': 'Place', 'color': '#60A5FA', 'tables': [t for t, v in TABLES.items() if v[0] == 'Ground floor'], 'workers': []},
    {'id': 'cutters', 'name': 'Cutters', 'basis': 'Role · whoever cuts', 'color': '#F59E0B', 'tables': ['Cutter-1', 'Cutter-2', 'Cutter-3'], 'workers': ['Aoife', 'Tomás']},
    {'id': 'assembly', 'name': 'Assembly', 'basis': 'Role', 'color': '#F472B6', 'tables': ['Assembly-4', 'Assembly-5'], 'workers': ['Dmitri', 'Lena']},
    {'id': 'packing', 'name': 'Packing', 'basis': 'Role', 'color': '#A78BFA', 'tables': ['Mail-Room1', 'Packing-7', 'Packing-12'], 'workers': ['Bea', 'Niamh', 'Seán']},
    {'id': 'dispatch', 'name': 'Dispatch', 'basis': 'Role', 'color': '#FB923C', 'tables': ['Dispatch-1', 'Dispatch-2', 'Docking-7'], 'workers': ['Ciara', 'Kofi', 'Ravi']},
    {'id': 'second', 'name': 'Second shift', 'basis': 'Time · 14:00 – 18:00', 'color': '#94A3B8', 'tables': [], 'workers': sorted({v[3] for v in TABLES.values() if v[3]})},
    {'id': 'new', 'name': 'New starters', 'basis': 'People · first 30 days', 'color': '#4ADE80', 'tables': [], 'workers': sorted(NEW_STARTERS)},
]
MESSAGES = ['Labels jammed again', 'Blade feels dull', 'Out of tape', 'Need a second pair of hands', 'Scanner not reading', 'Pallet in the way', 'Come see me when you can', 'Running low on sheets']
WAN, MOBILE = '203.0.113.17', '198.51.100.'

def lognorm(mean, spread):
    s = spread; mu = math.log(mean) - s * s / 2
    return R.lognormvariate(mu, s)

events = []
def ev(t, action, station, **kw):
    e = {'time': t.strftime('%Y-%m-%dT%H:%M:%SZ'), 'action': action, 'page': PAGE, 'station': station}
    e.update({k: v for k, v in kw.items() if v is not None})
    tab = TABLES.get(station)
    if tab and action == 'signin':   # the sample keeps the context and IP on sign-ins only, to stay small; the service logs them on every click
        ctx = {'tz': 'Europe/Dublin', 'local': t.strftime('%Y-%m-%dT%H:%M:%S'), 'device': tab[4]}
        if tab[5]: ctx['gps'] = {'lat': round(tab[5][0] + R.uniform(-.00004, .00004), 5), 'lon': round(tab[5][1] + R.uniform(-.00004, .00004), 5), 'acc': R.choice([12, 18, 25, 40])}
        e['ctx'] = ctx
        e['ip'] = WAN if R.random() > .06 else MOBILE + str(R.randint(2, 250))
    events.append(e)

def day_list():
    d = dt.date(2026, 11, 10)
    while d <= dt.date(2026, 11, 24):
        if d.weekday() < 5: yield d
        d += dt.timedelta(days=1)

emergency_done = False
last_day = dt.date(2026, 11, 24)
for day in day_list():
    monday = 1.1 if day.weekday() == 0 else 1.0
    for station, (floor, pool, w1, w2, dev, gps) in TABLES.items():
        shifts = [(w1, 6.0, 14.0)] + ([(w2, 14.0, 18.0)] if w2 else [])
        if station == 'Mail-Room1' and day == last_day: shifts = [(w1, 6.0, 9.0)]
        for worker, h0, h1 in shifts:
            t = dt.datetime.combine(day, dt.time(0)) + dt.timedelta(hours=h0, minutes=R.uniform(2, 14))
            end = dt.datetime.combine(day, dt.time(0)) + dt.timedelta(hours=h1)
            if station == 'Docking-7' and h0 == 6.0: end = dt.datetime.combine(day, dt.time(10, R.randint(20, 50)))
            first = True
            while t < end - dt.timedelta(minutes=12):
                # sign in, sometimes after a refused try
                if R.random() < .05:
                    ev(t, 'signin', station, ok=False, worker='')
                    t += dt.timedelta(seconds=R.uniform(8, 40))
                ev(t, 'signin', station, ok=True, worker=worker)
                t += dt.timedelta(seconds=R.uniform(15, 70))
                job = 'MI' if first and 'MI' in pool else R.choice([j for j in pool if j != 'MI'] or pool)
                first = False
                jname, subs = JOBS[job]
                ev(t, 'event', station, kind='job-chosen', worker=worker, detail=job)
                for sid, stext, base in subs:
                    f = monday * (1.3 if worker in NEW_STARTERS else 1.0)
                    if station in ('Cutter-2', 'Dispatch-1') and t.hour >= 14: f *= 1.9
                    spread = .65 if sid in ('CT-03', 'DL-03', 'LP-02') else .35
                    d = lognorm(base * f, spread) * 60
                    if sid == 'DL-03' and R.random() < .12: d += R.uniform(300, 700)
                    t += dt.timedelta(seconds=d)
                    retry = (R.random() < (.35 if sid == 'LP-02' else .03))
                    if retry:   # Press again!: the first press never reached the cloud; the second does, 5–20 s later
                        t += dt.timedelta(seconds=R.uniform(5, 20))
                    ev(t, 'tick', station, worker=worker, job=job, sub=sid, checked=True, **({'retry': True} if retry else {}))
                    redo = .12 if sid == 'LP-02' else .09 if sid == 'CT-03' else .015
                    if R.random() < redo:   # unticked, then done again
                        t += dt.timedelta(seconds=R.uniform(20, 90)); ev(t, 'tick', station, worker=worker, job=job, sub=sid, checked=False)
                        t += dt.timedelta(seconds=lognorm(base * .5, .4) * 60); ev(t, 'tick', station, worker=worker, job=job, sub=sid, checked=True)
                    if R.random() < .012:
                        mid = '%08x' % R.getrandbits(32)
                        ev(t + dt.timedelta(seconds=10), 'message', station, conv='c-' + station.lower(), mid=mid, text=R.choice(MESSAGES), worker=worker, task=jname)
                        if station == 'Packing-12' and R.random() < .5: pass
                if not emergency_done and day == dt.date(2026, 11, 12) and station == 'Cutter-2' and t.hour >= 15:
                    emergency_done = True
                    ev(t + dt.timedelta(seconds=30), 'emergency', station, conv='c-cutter-2', eid='e-%06x' % R.getrandbits(24), worker=worker, task=jname)
                t += dt.timedelta(seconds=lognorm(45, .6))
                if R.random() < .08:
                    ev(t, 'event', station, kind='signout-cancel', worker=worker, detail=job); t += dt.timedelta(seconds=R.uniform(10, 60))
                ev(t, 'event', station, kind='signout-confirm', worker=worker, detail=job)
                t += dt.timedelta(seconds=1)
                ev(t, 'complete', station, worker=worker, job=job)
                ev(t + dt.timedelta(seconds=1), 'signout', station, worker=worker, ended=True)
                t += dt.timedelta(minutes=lognorm(6, .7))
                if R.random() < .06: t += dt.timedelta(minutes=R.uniform(20, 45))   # a break

events.sort(key=lambda e: e['time'])
data = {
    'meta': {'kind': 'ccn-terminal-journal-sample', 'fake': True,
             'note': 'FAKE data for designing and testing the Journal. Made by journal/tools/make-sample.py; no real person or factory.',
             'from': '2026-11-10', 'to': '2026-11-24', 'tz': 'Europe/Dublin', 'events': len(events)},
    'tables': [{'id': k, 'floor': v[0], 'jobs': v[1]} for k, v in TABLES.items()],
    'workers': WORKERS,
    'jobs': {k: {'id': k, 'name': v[0], 'subtasks': [{'id': s[0], 'text': s[1]} for s in v[1]]} for k, v in JOBS.items()},
    'groups': GROUPS,
    'events': events,
}
with open(OUT, 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
print(len(events), 'events,', round(os.path.getsize(OUT) / 1e6, 2), 'MB')
