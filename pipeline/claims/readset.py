"""Which claims can observe a mutant — the relevance index behind `equiv.measure_modes`.

`equiv.py` asks, for every mutant of a session's `facts`, how every claim's predicate
evaluates. Most of those evaluations cannot change (how many is printed by every run —
`equiv.evals_line` — and typed nowhere): the mutant writes a slot the predicate never reads, so the predicate runs exactly as it did on the pristine tree and returns its
pristine verdict. This module says WHICH claims can read a written slot, so the sweep
evaluates only those and fills every other claim's bit with its pristine verdict.

That is exact, not a heuristic, but only under premises — and a premise nobody checks is a
comment. Each one is checked on every run, and a violation is an error, never a slow path:

  (a) a predicate is a pure `eval` over {facts, math, statistics}, deterministic, and its
      pristine run cannot raise (`equiv` raises `ClaimEvaluationError` if it does). So a
      claim none of whose read slots is written executes identically and returns its
      pristine bool.
  (b) a field-keyed slot `container[k]` is observable only through `Subscript(Constant k)`.
      `audit` proves that per predicate with a small kind system over the AST (below); a
      predicate outside that grammar raises `IndexUnsound` naming the claim and the node.
  (c) every claim's `python_check == spec.to_python(spec)`, so the grammar `audit` admits
      is the grammar the renderer emits — G1 in `equiv.check_index_premises`.
  (d) a control-flow change under a mutant (a flipped winner reading the other player)
      changes WHICH player dict is read, never which key NAME. So labels are key names,
      and a write is labelled by the key it writes (`key_labels`), except a write into a
      match's score dict, whose keys are player names, which takes its parent's label
      `score` — the only route to such a slot passes through `['score']`.

Nothing here is a dynamic trace. CPython fast paths (`{**d}`, `PyDict_Merge`) bypass
`__getitem__` on dict subclasses, so a proxy that logged reads could miss one and silently
prune a claim that mattered. The authority is static; the dynamic cross-check lives in
`equiv`'s stratified shadow tripwire and its `--selftest` differential, as the second
implementation.
"""
import ast

__all__ = ["IndexUnsound", "audit", "claim_keys", "key_labels", "build_readers"]


class IndexUnsound(Exception):
    """A predicate, or a write, falls outside what the relevance index can reason about."""


# --------------------------------------------------------------------------- the kind system
#
# Every sub-expression of a predicate gets a KIND. Containers (dicts and lists of the facts
# tree) may appear in exactly four positions: as the base of a subscript, as the iterable of a
# comprehension, as the receiver of `.values()`, and as the argument of `len()` (lists only).
# Everywhere else — a comparison, an arithmetic operand, a call argument, a generator element —
# only a scalar may appear. That rule is what makes premise (b) true: a comparison of two
# player dicts, `sum(p.values())`, `str(r)`, `{**r['players']}` or `p.get('pieces')` would
# each read a field without naming it, and each is a kind error here.

_DICTS = {"facts", "match", "round", "player", "lbplayer", "clears", "ge"}
_LIST_OF = {"list:match": "match", "list:round": "round", "list:ge": "ge"}
_MAP_OF = {"map:player": "player", "map:lb": "lbplayer", "map:score": "scalar"}

# Constant-key subscripts that lead to another container. Any other constant key on a dict
# kind is a scalar leaf; `facts` itself admits only 'matches'.
_CHILD = {
    ("facts", "matches"): "list:match",
    ("match", "rounds"): "list:round",
    ("match", "score"): "map:score",
    ("match", "leaderboard"): "map:lb",
    ("round", "players"): "map:player",
    ("player", "clears"): "clears",
    ("player", "garbage_events"): "list:ge",
}

_REDUCERS = {"sum", "max", "min"}
_CMP_OPS = (ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE)
_BIN_OPS = (ast.Add, ast.Sub, ast.Mult)


def _fail(cid, node, why):
    raise IndexUnsound(f"claim {cid}: {why}: `{ast.unparse(node)}` — the relevance index "
                       f"cannot prove which keys this reads; extend readset.audit (and its "
                       f"selftest) before admitting it")


class _Kinds:
    def __init__(self, cid):
        self.cid = cid

    def scalar(self, node, env, why):
        k = self.kind(node, env)
        if k not in ("scalar", "tuple"):
            _fail(self.cid, node, f"a container ({k}) is used where only a scalar may be, {why}")
        return k

    def iterate(self, it, env):
        """Kind of the elements a comprehension draws from `it`."""
        k = self.kind(it, env)
        if k in _LIST_OF:
            return _LIST_OF[k]
        if k.startswith("iter:"):
            return k[5:]
        if k in _MAP_OF:
            return "scalar"                  # iterating a map yields its keys: player names
        _fail(self.cid, it, f"iteration over a {k}")

    def comp(self, node, env):
        env = dict(env)
        for gen in node.generators:
            if gen.is_async or not isinstance(gen.target, ast.Name):
                _fail(self.cid, node, "a comprehension target that is not one plain name")
            env[gen.target.id] = self.iterate(gen.iter, env)
            for cond in gen.ifs:
                self.scalar(cond, env, "in a comprehension filter")
        return env

    def kind(self, node, env):  # noqa: C901 - one branch per admitted node type is the point
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (bool, int, str)):
                return "scalar"
            _fail(self.cid, node, "a constant of an unexpected type")
        if isinstance(node, ast.Name):
            if node.id == "facts":
                return "facts"
            if node.id in env:
                return env[node.id]
            _fail(self.cid, node, "a free name other than `facts`")
        if isinstance(node, ast.Subscript):
            base = self.kind(node.value, env)
            s = node.slice
            if base in _DICTS:
                if not (isinstance(s, ast.Constant) and isinstance(s.value, str)):
                    _fail(self.cid, node, f"a non-constant key into a {base} dict")
                if base == "facts" and s.value != "matches":
                    _fail(self.cid, node, "a key of `facts` other than 'matches'")
                return _CHILD.get((base, s.value), "scalar")
            if base in _LIST_OF:
                if isinstance(s, ast.Slice):
                    for part in (s.lower, s.upper, s.step):
                        if part is not None:
                            self.scalar(part, env, "as a slice bound")
                    return base
                self.scalar(s, env, "as a list index")
                return _LIST_OF[base]
            if base in _MAP_OF:
                if isinstance(s, ast.Slice):
                    _fail(self.cid, node, "a slice of a player-keyed map")
                self.scalar(s, env, "as a player key")
                return _MAP_OF[base]
            _fail(self.cid, node, f"a subscript into a {base}")
        if isinstance(node, ast.Call):
            if node.keywords:
                _fail(self.cid, node, "a keyword argument")
            f = node.func
            if isinstance(f, ast.Attribute):
                if f.attr != "values" or node.args:
                    _fail(self.cid, node, f"a method call `.{f.attr}()`")
                recv = self.kind(f.value, env)
                if recv not in _MAP_OF:
                    _fail(self.cid, node, f"`.values()` on a {recv}")
                return "iter:" + _MAP_OF[recv]
            if not isinstance(f, ast.Name) or f.id in env:
                _fail(self.cid, node, "a call to something other than a builtin")
            if f.id in _REDUCERS:
                if len(node.args) != 1:
                    _fail(self.cid, node, f"{f.id}() with other than one argument")
                (arg,) = node.args
                if isinstance(arg, ast.GeneratorExp):
                    self.scalar(arg.elt, self.comp(arg, env), f"as {f.id}()'s element")
                elif self.kind(arg, env) != "iter:scalar":
                    _fail(self.cid, node, f"{f.id}() over something other than a generator "
                                          f"or the score map's values")
                return "scalar"
            if f.id == "len":
                if len(node.args) != 1 or self.kind(node.args[0], env) not in _LIST_OF:
                    _fail(self.cid, node, "len() of something other than one list")
                return "scalar"
            if f.id == "range":
                for a in node.args:
                    self.scalar(a, env, "as a range bound")
                return "iter:scalar"
            _fail(self.cid, node, f"a call to `{f.id}`")
        if isinstance(node, ast.ListComp):
            env2 = self.comp(node, env)
            elt = self.kind(node.elt, env2)
            if elt not in _LIST_OF.values():
                _fail(self.cid, node, "a list comprehension of something other than rounds")
            return {v: k for k, v in _LIST_OF.items()}[elt]
        if isinstance(node, ast.Compare):
            if not all(isinstance(op, _CMP_OPS) for op in node.ops):
                _fail(self.cid, node, "a comparison operator outside == != < <= > >=")
            for x in [node.left, *node.comparators]:
                self.scalar(x, env, "as a comparison operand")
            return "scalar"
        if isinstance(node, ast.BoolOp):
            if not isinstance(node.op, ast.And):
                _fail(self.cid, node, "a boolean operator other than `and`")
            for x in node.values:
                self.scalar(x, env, "as a conjunct")
            return "scalar"
        if isinstance(node, ast.BinOp):
            if not isinstance(node.op, _BIN_OPS):
                _fail(self.cid, node, "an arithmetic operator outside + - *")
            self.scalar(node.left, env, "as an operand")
            self.scalar(node.right, env, "as an operand")
            return "scalar"
        if isinstance(node, ast.UnaryOp):
            if not isinstance(node.op, (ast.USub, ast.Not)):
                _fail(self.cid, node, "a unary operator other than - and not")
            self.scalar(node.operand, env, "as an operand")
            return "scalar"
        if isinstance(node, ast.Tuple):
            for x in node.elts:
                self.scalar(x, env, "as a tuple element")
            return "tuple"
        _fail(self.cid, node, f"a {type(node).__name__} node")


def audit(claim):
    """G2: raise `IndexUnsound` unless `claim['python_check']` is inside the admitted grammar.

    Returns the predicate's key set (`claim_keys`) so callers parse it once.
    """
    cid = claim.get("id", "?")
    try:
        tree = ast.parse(claim["python_check"], mode="eval")
    except SyntaxError as exc:
        raise IndexUnsound(f"claim {cid}: predicate does not parse: {exc}") from exc
    top = _Kinds(cid).kind(tree.body, {})
    if top != "scalar":
        _fail(cid, tree.body, f"the predicate evaluates to a {top}, not a verdict")
    return claim_keys(claim, tree)


def claim_keys(claim, tree=None):
    """Every string-constant subscript key in the predicate: the labels it can observe.

    `.values()` is only admitted on `['players']` and `['score']`, and both of those names
    are themselves constant subscripts, so they are already in this set — no special case.
    """
    tree = tree or ast.parse(claim["python_check"], mode="eval")
    return frozenset(n.slice.value for n in ast.walk(tree)
                     if isinstance(n, ast.Subscript) and isinstance(n.slice, ast.Constant)
                     and isinstance(n.slice.value, str))


def key_labels(writes, score_ids):
    """The labels one mutant writes: each write's key, or `score` for a score-dict write.

    `score_ids` is the set of `id()`s of every match's score dict, computed from the pristine
    tree. A score dict is keyed by player NAME, and a player name is not a key any predicate
    spells — the only route to a score value is through `['score']` — so its label is the
    parent's. G3 (`equiv._check_labels`) refuses a player name as a label, which is the
    mutant this function's obvious simplification produces.
    """
    return frozenset("score" if id(c) in score_ids else k for c, k, _ in writes)


def build_readers(keysets):
    """label -> sorted tuple of claim indices whose predicate names that label."""
    readers = {}
    for i, keys in enumerate(keysets):
        for k in keys:
            readers.setdefault(k, []).append(i)
    return {k: tuple(v) for k, v in readers.items()}
