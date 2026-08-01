"""The spec algebra's third renderer: SMT-LIB 2.6.

`spec.py` renders one predicate to a Python expression and to a Dafny `ensures`.
This adds a third target, for the same reason there are two extractors: a claim
checked by two independently implemented solvers is a stronger statement than one
checked by a single toolchain. The three renderers share one spec, so what Python
evaluates, what Dafny proves, and what an SMT solver refutes cannot drift apart.

Const names are **identical to the Dafny backend's** (`m3_r2_yachi_apm`), so a
reader can put `Facts.dfy` and `facts.smt2` side by side and check them off.

Three differences from the Dafny renderer:

* sums are emitted **n-ary** — `(+ t1 t2 … t79)`. `spec.bal` exists to keep the
  Dafny AST shallow enough for Boogie's recursive visitor; an s-expression needs no
  such trick, so the balancing is dropped rather than imitated.
* a claim is discharged by asserting its **negation** and requiring `unsat`, which
  is the SMT idiom for "this holds", and mirrors what Boogie does internally.
* **strings are encoded as integer codes.** Dafny compares player names as strings;
  here `m0_winner` is `1` or `2` with the mapping written into the file's header.
  Only equality is ever used on these, so nothing is lost — and it keeps the file
  inside quantifier-free linear integer arithmetic, which every SMT-LIB solver
  implements. Using the `String` sort restricted the artefact to the few solvers
  with a string theory (z3, cvc5), which defeats the point of emitting a standard
  format so that an *independent* solver can check it.

Integer division: Dafny's `/` on `int` and SMT-LIB's `div` are both Euclidean, and
every value here is non-negative, so the two agree with floor. The algebra emits no
division today; if a family ever needs one, that equivalence is the thing to re-check
before trusting the two backends to agree.
"""
from .spec import c_winner, dafny_field, dafny_suffix, rounds_in, rounds_of

# Every string value in the corpus, mapped to an integer code. Populated by
# `code_table()` from facts.json before rendering, so the codes are derived from
# the data rather than hard-coded, and the emitter can print the legend.
CODES = {}


def code_table(facts):
    """{string value: code} for every string a claim can compare against.

    Player names first (1, 2, in `players` order) so the common case reads
    predictably, then any other string field's values in sorted order.
    """
    codes = {pl: i + 1 for i, pl in enumerate(facts["players"])}
    others = set()
    for m in facts["matches"]:
        for r in m["rounds"]:
            for p in r["players"].values():
                for k, v in p.items():
                    if isinstance(v, str):
                        others.add(v)
    for v in sorted(others - set(codes)):
        codes[v] = len(codes) + 1
    CODES.clear()
    CODES.update(codes)
    return codes


def code(value):
    """The integer code for a string value, or a loud failure."""
    if value not in CODES:
        raise KeyError(f"no code for {value!r} — call code_table(facts) first")
    return CODES[value]

# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #


def nary(op, terms, unit="0"):
    """`(+ a b c)` — flat, because there is no AST-depth limit to work around."""
    terms = list(terms)
    if not terms:
        return unit
    if len(terms) == 1:
        return terms[0]
    return f"({op} " + " ".join(terms) + ")"


def _cap(pl):
    return pl[:1].upper() + pl[1:]


def _ite(cond, a, b):
    return f"(ite {cond} {a} {b})"


# A Cond's comparison operator is written the way Python and Dafny spell it, and
# those two agree on every operator — which is why passing it through to SMT-LIB
# went unnoticed until the first `==` appeared in a spec: SMT-LIB spells equality
# `=`, and z3/cvc5 answered `unknown constant ==` rather than a verdict. An op the
# emitter does not know is a hard error, never a pass-through: the whole point of
# the third backend is that a solver independently re-checks the same claim, and a
# file it cannot parse checks nothing.
_OPS = {"==": "=", "=": "=", "<": "<", "<=": "<=", ">": ">", ">=": ">=", "!=": "distinct"}


def _op(op):
    try:
        return _OPS[op]
    except KeyError:
        raise SystemExit(f"smt: no SMT-LIB spelling for comparison operator {op!r} "
                         f"(known: {', '.join(sorted(_OPS))})") from None


# --------------------------------------------------------------------------- #
# Cond / expression / predicate
# --------------------------------------------------------------------------- #


def smt_cond(facts, mi, ri, cond):
    k = cond["c"]
    if k == "winner":
        return f'(= m{mi}_r{ri}_winner {code(cond["pl"])})'
    if k == "field_cmp":
        return (f"({_op(cond['op'])} {dafny_field(mi, ri, cond['pl'], cond['f'])} "
                f"{cond['v']})")
    if k == "dur_cmp":
        a = dafny_field(mi, ri, "yachi", "lifetime")
        b = dafny_field(mi, ri, "pinglamb", "lifetime")
        return f"({_op(cond['op'])} {_ite(f'(>= {a} {b})', a, b)} {cond['v']})"
    if k == "winner_gt_loser":
        f = cond["f"]
        y, p = dafny_field(mi, ri, "yachi", f), dafny_field(mi, ri, "pinglamb", f)
        # Selected by the winner const, exactly as the Dafny renderer does, so a
        # mutated winner genuinely re-selects which datum is compared.
        return _ite(f'(= m{mi}_r{ri}_winner {code("yachi")})',
                    f"(> {y} {p})", f"(> {p} {y})")
    if k == "str_field":
        return (f'(= {dafny_field(mi, ri, cond["pl"], cond["f"])} '
                f'{code(cond["v"])})')
    if k == "and":
        return nary("and", [smt_cond(facts, mi, ri, x) for x in cond["xs"]], "true")
    raise ValueError(f"unknown cond {k}")


def _count(facts, cond):
    return nary("+", [_ite(smt_cond(facts, mi, ri, cond), "1", "0")
                      for mi, ri in rounds_of(facts)])


def _round_terms(facts, pl, f, square=False):
    out = []
    for mi, ri in rounds_of(facts):
        v = dafny_field(mi, ri, pl, f)
        out.append(f"(* {v} {v})" if square else v)
    return out


def _ge_terms(facts, pl, mi=None, ri=None):
    pairs = [(mi, ri)] if mi is not None else rounds_of(facts)
    out = []
    for a, b in pairs:
        n = len(facts["matches"][a]["rounds"][b]["players"][pl]["garbage_events"])
        out.extend(f"m{a}_r{b}_{pl}_ge{k}" for k in range(n))
    return out


def smt_expr(facts, e):
    k = e["e"]
    if k == "lit":
        v = e["v"]
        return str(v) if v >= 0 else f"(- {abs(v)})"
    if k == "round":
        return dafny_field(e["mi"], e["ri"], e["pl"], e["f"])
    if k == "lb":
        return f"m{e['mi']}_lb_{e['pl']}_{dafny_suffix(e['f'])}"
    if k == "score":
        return f"m{e['mi']}_score{_cap(e['pl'])}"
    if k == "total_rounds":
        # The sum of the per-match consts, never the literal count — a literal turns
        # "the session had 50 rounds" into 50 = 50, which is unsat-on-negation while
        # proving nothing about the data.
        return nary("+", [f"m{mi}_nrounds" for mi in range(len(facts["matches"]))])
    if k == "sum_round":
        return nary("+", _round_terms(facts, e["pl"], e["f"]))
    if k == "sum_round_where":
        return nary("+", [_ite(smt_cond(facts, mi, ri, e["cond"]),
                               dafny_field(mi, ri, e["pl"], e["f"]), "0")
                          for mi, ri in rounds_of(facts)])
    if k == "sum_round_range":
        return nary("+", [dafny_field(mi, ri, e["pl"], e["f"])
                          for mi, ri in rounds_in(facts, e["lo"], e["hi"])])
    if k == "sum_sq_round":
        return nary("+", _round_terms(facts, e["pl"], e["f"], square=True))
    if k == "sum_ge":
        return nary("+", _ge_terms(facts, e["pl"], e["mi"], e["ri"]))
    if k == "count_matches_won":
        return nary("+", [_ite(f'(= m{mi}_winner {code(e["pl"])})', "1", "0")
                          for mi in range(len(facts["matches"]))])
    if k == "count_rounds_won":
        return _count(facts, c_winner(e["pl"]))
    if k == "count_rounds":
        return _count(facts, e["cond"])
    if k == "count_rounds_range":
        return nary("+", [_ite(smt_cond(facts, mi, ri, e["cond"]), "1", "0")
                          for mi, ri in rounds_in(facts, e["lo"], e["hi"])])
    if k == "sum_lb":
        return nary("+", [f"m{mi}_lb_{e['pl']}_{dafny_suffix(e['f'])}"
                          for mi in range(len(facts["matches"]))])
    if k == "count_matches_margin":
        mg = e["margin"]
        terms = []
        for mi in range(len(facts["matches"])):
            y, p = f"m{mi}_scoreYachi", f"m{mi}_scorePinglamb"
            terms.append(_ite(f"(or (= (- {y} {p}) {mg}) (= (- {p} {y}) {mg}))",
                              "1", "0"))
        return nary("+", terms)
    if k in ("add", "sub", "mul"):
        op = {"add": "+", "sub": "-", "mul": "*"}[k]
        return f"({op} {smt_expr(facts, e['a'])} {smt_expr(facts, e['b'])})"
    raise ValueError(f"unknown expr {k}")


def smt_pred(facts, p):
    k = p["p"]
    if k in ("eq", "lt", "le", "gt", "ge"):
        op = {"eq": "=", "lt": "<", "le": "<=", "gt": ">", "ge": ">="}[k]
        return f"({op} {smt_expr(facts, p['a'])} {smt_expr(facts, p['b'])})"
    if k == "between":
        x = smt_expr(facts, p["x"])
        return f"(and (<= {p['lo']} {x}) (< {x} {p['hi']}))"
    if k == "match_winner":
        return f'(= m{p["mi"]}_winner {code(p["pl"])})'
    if k == "round_winner":
        return f'(= m{p["mi"]}_r{p["ri"]}_winner {code(p["pl"])})'
    if k == "round_seq":
        return nary("and", [f'(= m{mi}_r{ri}_winner {code(w)})'
                            for (mi, ri), w in zip(p["pairs"], p["winners"])], "true")
    if k == "all_rounds":
        return f"(= {_count(facts, p['cond'])} {len(rounds_of(facts))})"
    if k == "and":
        return nary("and", [smt_pred(facts, x) for x in p["xs"]], "true")
    raise ValueError(f"unknown pred {k}")


def to_smt(facts, spec):
    """Render a spec as an SMT-LIB boolean term over the flat fact definitions."""
    return smt_pred(facts, spec)
