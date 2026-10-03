#!/usr/bin/env python3
"""Adjudicate the frame checkers' disagreements for one player's clips.

    python3 adjudicate.py <work>/<player>/clips-chosen.json <player>/verify-out > <player>/adjudication.json

Two jobs, kept apart because they answer different questions.

1. An independent rebuild of every frame in clips-chosen.json, BOTH sides, from nothing but the
   frames themselves: each step's `before` is the previous step's `after` (the clip's start field for
   step 1); the piece's four cells are in bounds, empty, and resting on the floor or on a filled cell;
   placing it and removing full rows gives exactly `lines` rows; and `after` is that board pushed up
   by exactly `garbage` new rows, each a full garbage row with one hole. On Cold Clear's side the
   garbage rows must follow the page's stated rule: the rows the player received on a step (its own
   inserted rows, same count, same hole columns) are queued, and the queue goes in after Cold Clear's
   next piece that clears nothing - possibly that same step.

2. A reading of the four checkers' SAVED re-run outputs (verify-out/batch-*.txt, written by
   run-verifiers.sh). Every mismatch line they print is listed and classified. The one class this
   script can settle is `src garbage_in X != schedule sum Y`: that checker compares the rows Cold
   Clear INSERTED on a step with the rows the player RECEIVED on it, which differ by design whenever
   the rows wait. Such a line is `explained` only if job 1 found that clip's Cold Clear side clean,
   i.e. the insertion it disputes is the stated rule's. Anything else is `unresolved`, and the page
   says so - this script never turns a disagreement it does not understand into agreement.
"""
import glob, json, os, re, sys

clips = json.load(open(sys.argv[1]))
vdir = sys.argv[2]
W = 10


def full(r): return '.' not in r


def check_side(ci, side, seq, start, sched=None):
    """Return (frames_checked, problems, inserted-per-step). sched: per-step list of hole columns received."""
    probs, ins_log, frames = [], [], 0
    board = list(start)
    queue = []
    for k, st in enumerate(seq):
        tag = f'clip {ci} {side} step {k + 1}'
        if st.get('dead'):
            ins_log.append(None); continue
        frames += 1
        if st['before'] != board: probs.append(f'{tag}: before != previous after')
        b = [list(r) for r in st['before']]
        cells = st['cells']
        if len(cells) != 4 or len({tuple(c) for c in cells}) != 4: probs.append(f'{tag}: not 4 distinct cells')
        own = {tuple(c) for c in cells}
        for x, y in cells:
            if not (0 <= x < W and 0 <= y < len(b)): probs.append(f'{tag}: cell {x},{y} out of bounds'); continue
            if b[y][x] != '.': probs.append(f'{tag}: cell {x},{y} occupied')
        if not any(y + 1 == len(b) or (b[y + 1][x] != '.' and (x, y + 1) not in own) for x, y in cells):
            probs.append(f'{tag}: piece floating')
        for x, y in cells: b[y][x] = st['piece']
        rows = [''.join(r) for r in b]
        kept = [r for r in rows if not full(r)]
        n = len(rows) - len(kept)
        if n != st['lines']: probs.append(f'{tag}: rebuilt clears {n} != lines {st["lines"]}')
        cleared = ['.' * W] * n + kept
        g = st['garbage']
        holes = []
        for r in st['after'][len(st['after']) - g:] if g else []:
            if r.count('.') != 1 or set(r) - {'G', '.'}: probs.append(f'{tag}: inserted row {r!r} is not one-hole garbage')
            holes.append(r.index('.') if '.' in r else -1)
        if cleared[:g] != ['.' * W] * g: probs.append(f'{tag}: garbage pushed blocks out of the top')
        if st['after'][:len(st['after']) - g] != cleared[g:]: probs.append(f'{tag}: after != cleared board pushed up by {g}')
        if sched is not None:                     # Cold Clear: the stated deferral rule
            queue += sched[k]
            want = queue if st['lines'] == 0 else []
            if sorted(holes) != sorted(want):
                probs.append(f'{tag}: inserted holes {holes} but the rule inserts {want}')
            if st['lines'] == 0: queue = []
        ins_log.append(holes)
        board = st['after']
    return frames, probs, ins_log, queue


out = {'clips': [], 'frames': 0, 'problems': [], 'verifier': []}
clean_cc = set()
for ci, c in enumerate(clips):
    fh, ph, ins_h, _ = check_side(ci, 'human', c['human'], c['start']['field'])
    fc, pc, _, left = check_side(ci, 'cc', c['cc'], c['start']['field'], [h or [] for h in ins_h])
    out['frames'] += fh + fc
    out['problems'] += ph + pc
    if not pc: clean_cc.add(ci)
    out['clips'].append({'clip': ci, 'id': c['id'], 'frames': fh + fc, 'problems': len(ph) + len(pc),
                         'cc_rows_pending_at_end': len(left)})

GARB = re.compile(r'clip ?(\d+) cc step ?\d+: src garbage_in \d+ != schedule sum \d+')
for f in sorted(glob.glob(os.path.join(vdir, 'batch-*.txt'))):
    txt = open(f).read()
    lines = [m.group(1) for m in re.finditer(r'^\s*MISMATCH (.*)$', txt, re.M)]
    j = txt.find('[\n')
    if j >= 0:
        for r in json.loads(txt[j:]): lines += r.get('mismatches', [])
    rows = []
    for m in lines:
        g = GARB.match(m)
        ok = bool(g) and int(g.group(1)) in clean_cc
        rows.append({'line': m, 'verdict': 'explained' if ok else 'unresolved',
                     **({'why': 'inserted vs received: the rows waited for a piece that clears nothing, and the rebuild above confirms that insertion'} if ok else {})})
    out['verifier'].append({'file': os.path.basename(f), 'mismatch_lines': len(rows), 'lines': rows})
out['unresolved'] = sum(r['verdict'] == 'unresolved' for v in out['verifier'] for r in v['lines'])
json.dump(out, sys.stdout, indent=1, ensure_ascii=False)
print()
print(f"frames {out['frames']}, rebuild problems {len(out['problems'])}, verifier mismatch lines "
      f"{sum(v['mismatch_lines'] for v in out['verifier'])}, unresolved {out['unresolved']}", file=sys.stderr)
