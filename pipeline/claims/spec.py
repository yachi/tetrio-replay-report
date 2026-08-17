"""A small predicate algebra with two renderers.

A claim family (see generators.py) never writes a Python string or a Dafny string.
It builds a *spec* — a nested dict describing the predicate — and this module renders
it to either backend. One definition, two outputs, so the checked predicate and the
proved lemma cannot drift apart.

Expressions
    lit               a literal integer
    round             one per-round stat        facts[...]        / m{mi}_r{ri}_{pl}_{f}
    lb                one match-level stat      leaderboard       / m{mi}_lb_{pl}_{f}
    score             a match score component   m['score'][pl]    / m{mi}_score{Pl}
    score_of_winner   that match's WINNER's score, selected by the winner const
    dur               one round's duration = max of the two players' lifetime
    nrounds           one match's round count   m{mi}_nrounds
    nmatches          matches in the session
    total_rounds      rounds in the session
    sum_round         a per-round stat summed over the whole session
    sum_round_where   the same, restricted to rounds satisfying a Cond
    sum_round_range   the same, restricted to a contiguous window of matches
    sum_sq_round      the same, squared (for the integer variance identity)
    sum_ge            queued incoming attack (garbage events), session- or round-scoped
    count_matches_won / count_rounds_won
    count_rounds      rounds satisfying a Cond
    count_rounds_range  the same, restricted to a contiguous window of matches
    count_rounds_window the same, over a window of FLAT round positions
    count_round_pairs   adjacent within-match round pairs satisfying two Conds
    count_matches_margin  matches whose score margin is exactly k
    sum_lb            a match-level stat summed over the session
    add / sub / mul

Predicates
    eq lt le gt ge    compare two expressions
    between           lo <= x < hi   (how a displayed rounded value is pinned)
    match_winner      m{mi}_winner == pl
    round_winner      m{mi}_r{ri}_winner == pl
    round_seq         a run of consecutive round winners (streaks)
    all_rounds        every round satisfies a Cond, rendered as a count equality so
                      the Dafny side stays ground (no quantifier)
    and               conjunction

Conds (a boolean about one round)
    winner            that round was won by pl
    field_cmp         a player's stat compared to a literal
    dur_cmp           round duration (max of both lifetimes) compared to a literal
    winner_gt_loser   the round's winner had a higher value of a field than the loser
    str_field         a player's string field equals a value (e.g. how they died)

Dafny rendering is fully ground: every sum is expanded over the actual rounds and
emitted as a BALANCED expression tree. Deep left-nested chains overflow Boogie's
recursive AST visitor, which is why bal() exists.

TWO WINDOW INDEX SPACES, and picking the wrong one silently changes the claim.
`sum_round_range` / `count_rounds_range` take a window of **matches**;
`count_rounds_window` takes a window of **flat round positions** across the whole
session. A run of consecutive round wins crosses match boundaries, so it can only be
stated in the flat space — asking `count_rounds_range` for it would silently restrict
the run to one match. Both are part of a claim's identity, not data, so both render by
emitting only the in-window terms (see rounds_in).

THE ALGEBRA IS DELIBERATELY CONJUNCTIVE. There is no `or` and no negation. A claim of
the form "the maximum is V" is therefore written as the pair
`count_rounds(f > V) == 0` and `count_rounds(f == V) >= 1`, which is exactly
equivalent and — unlike pinning a named witness round — does not quietly strengthen
the claim by naming a round its sentence never mentions. Where the sentence DOES name
the round, pin it. `count_matches_margin` emits `||` internally; that is an
implementation detail of one operator, not a disjunction constructor.
"""

# --------------------------------------------------------------------------- #
# field naming
# --------------------------------------------------------------------------- #
# A field is named by its facts.json path. Nested clear counters use a dotted
# name ("clears.quads"). The Dafny const suffix is that name with dots and the
# _x1000 marker removed, so `clears.quads` -> clears_quads and `apm_x1000` -> apm.
# codegen.py emits Facts.dfy using exactly this rule, so the two always agree.

def field_path(f):
    return f.split(".")


def dafny_suffix(f):
    return f.replace(".", "_").replace("_x1000", "")


def py_field_access(pl, f, r="r"):
    parts = "".join(f"[{k!r}]" for k in field_path(f))
    return f"{r}['players'][{pl!r}]{parts}"


def read_field(player_obj, f):
    v = player_obj
    for k in field_path(f):
        v = v[k]
    return v


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #

def bal(op, terms):
    """Balanced (log-depth) associative expression tree.

    A 1000-term `a+b+c+...` built left-nested is a 1000-deep AST and overflows
    Boogie's Duplicator. Splitting in half keeps depth logarithmic.
    """
    terms = list(terms)
    if not terms:
        return "0"
    if len(terms) == 1:
        return terms[0]
    mid = len(terms) // 2
    return f"({bal(op, terms[:mid])} {op} {bal(op, terms[mid:])})"


def rounds_of(facts):
    return [(mi, ri) for mi, m in enumerate(facts["matches"]) for ri in range(len(m["rounds"]))]


def rounds_window(facts, lo, hi):
    """A window of FLAT round positions — `rounds_of(facts)[lo:hi]`.

    Not the same index space as rounds_in, which windows by match. A streak of round
    wins runs across match boundaries, so the flat space is the only one that can
    state it; a match window would silently truncate the run at the match edge.
    """
    return rounds_of(facts)[lo:hi]


def round_pairs(facts):
    """Every adjacent (previous, current) round pair, WITHIN a match.

    Pairs never straddle a match boundary: the last round of one match and the first
    of the next are not consecutive in play, and counting them as a pair would invent
    a break of serve that never happened.
    """
    return [(mi, ri - 1, ri)
            for mi, m in enumerate(facts["matches"])
            for ri in range(1, len(m["rounds"]))]


def rounds_in(facts, lo, hi):
    """The rounds of matches [lo, hi) by position, not by the file's index field.

    A window is part of a claim's identity ("the first two matches"), the way sum_ge's
    mi/ri already are — it is not a datum. So it is rendered by emitting only the terms
    inside it, never as `if <window> then x else 0`: a folded-away `if false` leaves the
    const referenced in the text but unread by the proof, which is precisely the dead
    const that mutation testing can never kill.
    """
    return [(mi, ri) for mi, ri in rounds_of(facts) if lo <= mi < hi]


def dafny_field(mi, ri, pl, f):
    return f"m{mi}_r{ri}_{pl}_{dafny_suffix(f)}"


def _cap(pl):
    return pl[:1].upper() + pl[1:]


# --------------------------------------------------------------------------- #
# expression constructors (what generators call)
# --------------------------------------------------------------------------- #

def lit(v):                       return {"e": "lit", "v": int(v)}
def rnd(mi, ri, pl, f):           return {"e": "round", "mi": mi, "ri": ri, "pl": pl, "f": f}
def lb(mi, pl, f):                return {"e": "lb", "mi": mi, "pl": pl, "f": f}
def score(mi, pl):                return {"e": "score", "mi": mi, "pl": pl}
def score_of_winner(mi):          return {"e": "score_of_winner", "mi": mi}
def dur(mi, ri):                  return {"e": "dur", "mi": mi, "ri": ri}
def nrounds(mi):                  return {"e": "nrounds", "mi": mi}
def nmatches():                   return {"e": "nmatches"}
def total_rounds():               return {"e": "total_rounds"}
def sum_round(pl, f):             return {"e": "sum_round", "pl": pl, "f": f}
def sum_round_where(pl, f, cond): return {"e": "sum_round_where", "pl": pl, "f": f, "cond": cond}
def sum_round_range(pl, f, lo, hi):
    return {"e": "sum_round_range", "pl": pl, "f": f, "lo": int(lo), "hi": int(hi)}
def sum_sq_round(pl, f):          return {"e": "sum_sq_round", "pl": pl, "f": f}
def sum_ge(pl, mi=None, ri=None): return {"e": "sum_ge", "pl": pl, "mi": mi, "ri": ri}
def count_matches_won(pl):        return {"e": "count_matches_won", "pl": pl}
def count_rounds_won(pl):         return {"e": "count_rounds_won", "pl": pl}
def count_rounds(cond):           return {"e": "count_rounds", "cond": cond}
def count_rounds_range(cond, lo, hi):
    return {"e": "count_rounds_range", "cond": cond, "lo": int(lo), "hi": int(hi)}
def count_rounds_window(cond, lo, hi):
    return {"e": "count_rounds_window", "cond": cond, "lo": int(lo), "hi": int(hi)}
def count_round_pairs(prev, cur=None):
    return {"e": "count_round_pairs", "prev": prev, "cur": cur}
def count_matches_margin(m):      return {"e": "count_matches_margin", "margin": int(m)}
def sum_lb(pl, f):                return {"e": "sum_lb", "pl": pl, "f": f}
def add(a, b):                    return {"e": "add", "a": a, "b": b}
def sub(a, b):                    return {"e": "sub", "a": a, "b": b}
def mul(a, b):                    return {"e": "mul", "a": a, "b": b}


# predicate constructors
def eq(a, b):                     return {"p": "eq", "a": a, "b": b}
def lt(a, b):                     return {"p": "lt", "a": a, "b": b}
def le(a, b):                     return {"p": "le", "a": a, "b": b}
def gt(a, b):                     return {"p": "gt", "a": a, "b": b}
def ge_(a, b):                    return {"p": "ge", "a": a, "b": b}
def between(x, lo, hi):           return {"p": "between", "x": x, "lo": int(lo), "hi": int(hi)}
def match_winner(mi, pl):         return {"p": "match_winner", "mi": mi, "pl": pl}
def round_winner(mi, ri, pl):     return {"p": "round_winner", "mi": mi, "ri": ri, "pl": pl}
def round_seq(pairs, winners):    return {"p": "round_seq", "pairs": pairs, "winners": winners}
def all_rounds(cond):             return {"p": "all_rounds", "cond": cond}
def conj(*xs):                    return {"p": "and", "xs": [x for x in xs if x is not None]}


# cond constructors
#
# A Cond's operator is written the Python/Dafny way, and every backend needs a
# spelling for it. Rejecting an unknown one HERE rather than at render time is the
# difference between a family that refuses to build and a claims.smt2 that a solver
# answers `unknown constant ==` on: the first `==` in a spec shipped as the latter,
# because Python and Dafny both accept it verbatim and only the SMT gate noticed.
_COND_OPS = ("==", "<", "<=", ">", ">=", "!=")


def _check_op(op):
    if op not in _COND_OPS:
        raise ValueError(f"unsupported cond operator {op!r} "
                         f"(supported: {', '.join(_COND_OPS)})")
    return op


def c_winner(pl):                 return {"c": "winner", "pl": pl}
def c_field(pl, f, op, v):        return {"c": "field_cmp", "pl": pl, "f": f, "op": _check_op(op), "v": int(v)}
def c_dur(op, v):                 return {"c": "dur_cmp", "op": _check_op(op), "v": int(v)}
def c_winner_gt_loser(f):         return {"c": "winner_gt_loser", "f": f}
def c_and(*xs):                   return {"c": "and", "xs": list(xs)}
def c_str(pl, f, v):              return {"c": "str_field", "pl": pl, "f": f, "v": v}


# --------------------------------------------------------------------------- #
# Python renderer
# --------------------------------------------------------------------------- #

_PY_ROUNDS = "for m in facts['matches'] for r in m['rounds']"


def py_cond(cond, r="r"):
    """Render a Cond as a Python expression over a round.

    `r` is the text naming that round — the loop variable `r` everywhere a Cond runs
    over a comprehension, and an explicit subscript like `m['rounds'][i-1]` where
    count_round_pairs needs to talk about two different rounds in one expression.
    """
    k = cond["c"]
    if k == "winner":
        return f"{r}['winner']=={cond['pl']!r}"
    if k == "field_cmp":
        return f"{py_field_access(cond['pl'], cond['f'], r)} {cond['op']} {cond['v']}"
    if k == "dur_cmp":
        return f"max(d['lifetime'] for d in {r}['players'].values()) {cond['op']} {cond['v']}"
    if k == "winner_gt_loser":
        parts = "".join(f"[{k!r}]" for k in field_path(cond["f"]))
        return (f"{r}['players'][{r}['winner']]{parts} > "
                f"min({r}['players'][p]{parts} for p in {r}['players'] if p!={r}['winner'])")
    if k == "str_field":
        return f"{py_field_access(cond['pl'], cond['f'], r)} == {cond['v']!r}"
    if k == "and":
        return " and ".join(f"({py_cond(x, r)})" for x in cond["xs"])
    raise ValueError(f"unknown cond {k}")


def py_expr(e):
    k = e["e"]
    if k == "lit":
        return str(e["v"])
    if k == "round":
        parts = "".join(f"[{k!r}]" for k in field_path(e["f"]))
        return (f"facts['matches'][{e['mi']}]['rounds'][{e['ri']}]"
                f"['players'][{e['pl']!r}]{parts}")
    if k == "lb":
        return f"facts['matches'][{e['mi']}]['leaderboard'][{e['pl']!r}][{e['f']!r}]"
    if k == "score":
        return f"facts['matches'][{e['mi']}]['score'][{e['pl']!r}]"
    if k == "score_of_winner":
        m = f"facts['matches'][{e['mi']}]"
        return f"{m}['score'][{m}['winner']]"
    if k == "dur":
        return (f"max(d['lifetime'] for d in facts['matches'][{e['mi']}]"
                f"['rounds'][{e['ri']}]['players'].values())")
    if k == "nrounds":
        return f"len(facts['matches'][{e['mi']}]['rounds'])"
    if k == "nmatches":
        return "len(facts['matches'])"
    if k == "total_rounds":
        return "sum(len(m['rounds']) for m in facts['matches'])"
    if k == "sum_round":
        return f"sum({py_field_access(e['pl'], e['f'])} {_PY_ROUNDS})"
    if k == "sum_round_where":
        return (f"sum({py_field_access(e['pl'], e['f'])} {_PY_ROUNDS} "
                f"if {py_cond(e['cond'])})")
    if k == "sum_round_range":
        return (f"sum({py_field_access(e['pl'], e['f'])} "
                f"for m in facts['matches'][{e['lo']}:{e['hi']}] for r in m['rounds'])")
    if k == "sum_sq_round":
        acc = py_field_access(e["pl"], e["f"])
        return f"sum({acc}*{acc} {_PY_ROUNDS})"
    if k == "sum_ge":
        if e["mi"] is None:
            return (f"sum(g['amt'] {_PY_ROUNDS} "
                    f"for g in r['players'][{e['pl']!r}]['garbage_events'])")
        return (f"sum(g['amt'] for g in facts['matches'][{e['mi']}]['rounds'][{e['ri']}]"
                f"['players'][{e['pl']!r}]['garbage_events'])")
    if k == "count_matches_won":
        return f"sum(1 for m in facts['matches'] if m['winner']=={e['pl']!r})"
    if k == "count_rounds_won":
        return f"sum(1 {_PY_ROUNDS} if r['winner']=={e['pl']!r})"
    if k == "count_rounds":
        return f"sum(1 {_PY_ROUNDS} if {py_cond(e['cond'])})"
    if k == "count_rounds_range":
        return (f"sum(1 for m in facts['matches'][{e['lo']}:{e['hi']}] for r in m['rounds'] "
                f"if {py_cond(e['cond'])})")
    if k == "count_rounds_window":
        return (f"sum(1 for r in [x for m in facts['matches'] for x in m['rounds']]"
                f"[{e['lo']}:{e['hi']}] if {py_cond(e['cond'])})")
    if k == "count_round_pairs":
        prev = py_cond(e["prev"], "m['rounds'][i-1]")
        tail = ""
        if e["cur"] is not None:
            tail = " and (" + py_cond(e["cur"], "m['rounds'][i]") + ")"
        return (f"sum(1 for m in facts['matches'] for i in range(1, len(m['rounds'])) "
                f"if ({prev}){tail})")
    if k == "count_matches_margin":
        return ("sum(1 for m in facts['matches'] if "
                f"max(m['score'].values())-min(m['score'].values())=={e['margin']})")
    if k == "sum_lb":
        return (f"sum(m['leaderboard'][{e['pl']!r}][{e['f']!r}] "
                "for m in facts['matches'])")
    if k in ("add", "sub", "mul"):
        op = {"add": "+", "sub": "-", "mul": "*"}[k]
        return f"({py_expr(e['a'])} {op} {py_expr(e['b'])})"
    raise ValueError(f"unknown expr {k}")


def py_pred(p):
    k = p["p"]
    if k in ("eq", "lt", "le", "gt", "ge"):
        op = {"eq": "==", "lt": "<", "le": "<=", "gt": ">", "ge": ">="}[k]
        return f"({py_expr(p['a'])} {op} {py_expr(p['b'])})"
    if k == "between":
        return f"({p['lo']} <= {py_expr(p['x'])} < {p['hi']})"
    if k == "match_winner":
        return f"(facts['matches'][{p['mi']}]['winner']=={p['pl']!r})"
    if k == "round_winner":
        return (f"(facts['matches'][{p['mi']}]['rounds'][{p['ri']}]"
                f"['winner']=={p['pl']!r})")
    if k == "round_seq":
        seq = ", ".join(
            f"facts['matches'][{mi}]['rounds'][{ri}]['winner']" for mi, ri in p["pairs"]
        )
        want = ", ".join(repr(w) for w in p["winners"])
        return f"(({seq},) == ({want},))"
    if k == "all_rounds":
        # count-equality form: as many rounds satisfy the cond as there are rounds
        return f"({py_expr(count_rounds(p['cond']))} == {py_expr(total_rounds())})"
    if k == "and":
        return " and ".join(py_pred(x) for x in p["xs"])
    raise ValueError(f"unknown pred {k}")


# --------------------------------------------------------------------------- #
# Dafny renderer — fully ground, balanced trees
# --------------------------------------------------------------------------- #

def _dfy_round_terms(facts, pl, f, square=False):
    terms = []
    for mi, ri in rounds_of(facts):
        v = dafny_field(mi, ri, pl, f)
        terms.append(f"({v} * {v})" if square else v)
    return terms


def _dfy_ge_terms(facts, pl, mi=None, ri=None):
    terms = []
    pairs = [(mi, ri)] if mi is not None else rounds_of(facts)
    for a, b in pairs:
        n = len(facts["matches"][a]["rounds"][b]["players"][pl]["garbage_events"])
        terms.extend(f"m{a}_r{b}_{pl}_ge{k}" for k in range(n))
    return terms


def _dfy_dur(mi, ri):
    """One round's duration: the larger of the two players' lifetime.

    The Cond (`dur_cmp`) and the expression (`dur`) both come through here, so the two
    cannot render different notions of "how long that round was".
    """
    a = dafny_field(mi, ri, "yachi", "lifetime")
    b = dafny_field(mi, ri, "pinglamb", "lifetime")
    return f"(if {a} >= {b} then {a} else {b})"


def dfy_cond(facts, mi, ri, cond):
    """Render a Cond for one concrete round, as a ground boolean."""
    k = cond["c"]
    if k == "winner":
        return f'(m{mi}_r{ri}_winner == "{cond["pl"]}")'
    if k == "field_cmp":
        return f"({dafny_field(mi, ri, cond['pl'], cond['f'])} {cond['op']} {cond['v']})"
    if k == "dur_cmp":
        return f"({_dfy_dur(mi, ri)} {cond['op']} {cond['v']})"
    if k == "winner_gt_loser":
        f = cond["f"]
        y, p = dafny_field(mi, ri, "yachi", f), dafny_field(mi, ri, "pinglamb", f)
        # winner-relative read: select by the winner const so a mutated winner
        # genuinely re-selects the datum
        return (f'(if m{mi}_r{ri}_winner == "yachi" then {y} > {p} else {p} > {y})')
    if k == "str_field":
        return (f'({dafny_field(mi, ri, cond["pl"], cond["f"])} == "{cond["v"]}")')
    if k == "and":
        return "(" + " && ".join(dfy_cond(facts, mi, ri, x) for x in cond["xs"]) + ")"
    raise ValueError(f"unknown cond {k}")


def _dfy_count(facts, cond):
    terms = [f"(if {dfy_cond(facts, mi, ri, cond)} then 1 else 0)"
             for mi, ri in rounds_of(facts)]
    return bal("+", terms)


def dfy_expr(facts, e):
    k = e["e"]
    if k == "lit":
        return str(e["v"])
    if k == "round":
        return dafny_field(e["mi"], e["ri"], e["pl"], e["f"])
    if k == "lb":
        return f"m{e['mi']}_lb_{e['pl']}_{dafny_suffix(e['f'])}"
    if k == "score":
        return f"m{e['mi']}_score{_cap(e['pl'])}"
    if k == "score_of_winner":
        a, b = facts["players"]
        return (f'(if m{e["mi"]}_winner == "{a}" then m{e["mi"]}_score{_cap(a)} '
                f"else m{e['mi']}_score{_cap(b)})")
    if k == "dur":
        return _dfy_dur(e["mi"], e["ri"])
    if k == "nrounds":
        return f"m{e['mi']}_nrounds"
    if k == "nmatches":
        return "nmatches"
    if k == "total_rounds":
        # MUST be the sum of the per-match nrounds consts, not the literal count.
        # Rendering it as a literal turns "the session had 50 rounds" into 50 == 50,
        # which verifies while proving nothing.
        return bal("+", [f"m{mi}_nrounds" for mi in range(len(facts["matches"]))])
    if k == "sum_round":
        return bal("+", _dfy_round_terms(facts, e["pl"], e["f"]))
    if k == "sum_round_where":
        terms = [f"(if {dfy_cond(facts, mi, ri, e['cond'])} then "
                 f"{dafny_field(mi, ri, e['pl'], e['f'])} else 0)"
                 for mi, ri in rounds_of(facts)]
        return bal("+", terms)
    if k == "sum_round_range":
        return bal("+", [dafny_field(mi, ri, e["pl"], e["f"])
                         for mi, ri in rounds_in(facts, e["lo"], e["hi"])])
    if k == "sum_sq_round":
        return bal("+", _dfy_round_terms(facts, e["pl"], e["f"], square=True))
    if k == "sum_ge":
        return bal("+", _dfy_ge_terms(facts, e["pl"], e["mi"], e["ri"]))
    if k == "count_matches_won":
        return bal("+", [f'(if m{mi}_winner == "{e["pl"]}" then 1 else 0)'
                         for mi in range(len(facts["matches"]))])
    if k == "count_rounds_won":
        return _dfy_count(facts, c_winner(e["pl"]))
    if k == "count_rounds":
        return _dfy_count(facts, e["cond"])
    if k == "count_rounds_range":
        return bal("+", [f"(if {dfy_cond(facts, mi, ri, e['cond'])} then 1 else 0)"
                         for mi, ri in rounds_in(facts, e["lo"], e["hi"])])
    if k == "count_rounds_window":
        return bal("+", [f"(if {dfy_cond(facts, mi, ri, e['cond'])} then 1 else 0)"
                         for mi, ri in rounds_window(facts, e["lo"], e["hi"])])
    if k == "count_round_pairs":
        terms = []
        for mi, pi, ci in round_pairs(facts):
            t = dfy_cond(facts, mi, pi, e["prev"])
            if e["cur"] is not None:
                t = f"({t} && {dfy_cond(facts, mi, ci, e['cur'])})"
            terms.append(f"(if {t} then 1 else 0)")
        return bal("+", terms)
    if k == "sum_lb":
        return bal("+", [f"m{mi}_lb_{e['pl']}_{dafny_suffix(e['f'])}"
                         for mi in range(len(facts["matches"]))])
    if k == "count_matches_margin":
        mg = e["margin"]
        terms = []
        for mi in range(len(facts["matches"])):
            y, p = f"m{mi}_scoreYachi", f"m{mi}_scorePinglamb"
            terms.append(f"(if {y} - {p} == {mg} || {p} - {y} == {mg} then 1 else 0)")
        return bal("+", terms)
    if k in ("add", "sub", "mul"):
        op = {"add": "+", "sub": "-", "mul": "*"}[k]
        return f"({dfy_expr(facts, e['a'])} {op} {dfy_expr(facts, e['b'])})"
    raise ValueError(f"unknown expr {k}")


def dfy_pred(facts, p):
    k = p["p"]
    if k in ("eq", "lt", "le", "gt", "ge"):
        op = {"eq": "==", "lt": "<", "le": "<=", "gt": ">", "ge": ">="}[k]
        return f"({dfy_expr(facts, p['a'])} {op} {dfy_expr(facts, p['b'])})"
    if k == "between":
        x = dfy_expr(facts, p["x"])
        return f"({p['lo']} <= {x} && {x} < {p['hi']})"
    if k == "match_winner":
        return f'(m{p["mi"]}_winner == "{p["pl"]}")'
    if k == "round_winner":
        return f'(m{p["mi"]}_r{p["ri"]}_winner == "{p["pl"]}")'
    if k == "round_seq":
        parts = [f'(m{mi}_r{ri}_winner == "{w}")'
                 for (mi, ri), w in zip(p["pairs"], p["winners"])]
        return bal("&&", parts)
    if k == "all_rounds":
        return (f"({_dfy_count(facts, p['cond'])} == {len(rounds_of(facts))})")
    if k == "and":
        return bal("&&", [dfy_pred(facts, x) for x in p["xs"]])
    raise ValueError(f"unknown pred {k}")


# --------------------------------------------------------------------------- #
# public entry points
# --------------------------------------------------------------------------- #

def to_python(spec):
    """Render a spec as a Python expression over a dict named `facts`."""
    return py_pred(spec)


def to_dafny(facts, spec):
    """Render a spec as a ground Dafny boolean over the flat Facts consts."""
    return dfy_pred(facts, spec)
