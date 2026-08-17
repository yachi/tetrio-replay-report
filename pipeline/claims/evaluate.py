"""The one evaluator for a claim's `python_check`.

Four gates run claim predicates — `pipeline.check_claims` (which `bin/verify-session`
step 2 invokes, i.e. the repo's primary claim gate), `claims.equiv`,
`claims.build_claims` and `check_rate_coverage` — and until this module existed each
carried its own `eval` call. They did not agree about the environment, in two ways:

    eval(src, {"facts": facts, "math": math, "statistics": statistics})   # lenient
    eval(src, {"__builtins__": __builtins__}, {"facts": facts})           # strict
    eval(src, {"facts": facts})                                           # no modules

The third is a latent divergence rather than a live one — no committed predicate reaches
for `math` or `statistics` — but it is the same class, and in `check_rate_coverage` a
raising predicate counts as falsified, i.e. it would have hidden a hole. The first two
diverge on real committed data, and not cosmetically.

An `eval`'s *locals* mapping is visible only to the
top-level expression: a nested scope — a lambda body, or the body of a comprehension or
generator other than its leftmost iterable — resolves a free name through enclosing
*function* scopes and then globals, and an eval's locals mapping is neither of those. So
a predicate that reads `facts` inside a lambda raises `NameError: name 'facts' is not
defined` under the strict form while evaluating perfectly well under the lenient one.
Two committed predicates were in exactly that shape (2026-07-22 C021, since ported to the
spec algebra; 2026-07-24 proof C018, which still is).

**The binding is lenient: `facts` goes in globals.** The reason is containment, not
taste. Strict ⊆ lenient — a top-level name lookup tries locals, then globals, then
builtins, so moving the single binding `facts` from the locals mapping into the globals
mapping cannot change how any expression that already resolved resolves; it can only add
resolution where strict had none. Adopting lenient therefore leaves every pre-existing
verdict untouched (checked: over every committed ledger in every session, exactly one
predicate resolves differently, and it is one that strict could not evaluate at all)
while removing the silent-NameError class outright. Adopting strict instead would have
made a committed artefact start failing, which moves the problem rather than closing it.

Predicates get the real builtins — they are written with `sum`, `max`, `min`, `sorted`,
`abs` and `len`. This is not a sandbox and was never one under either form; `eval`
injects `__builtins__` into a globals mapping that lacks it.
"""
import math
import statistics


class ClaimEvaluationError(Exception):
    """A predicate raised where raising is not a legitimate outcome."""


class ClaimEvaluator:
    """Evaluates predicates against one `facts` tree.

    The environment is built once and reused. That is deliberate rather than incidental:
    `claims.equiv` mutates `facts` in place (make/unmake, see `pipeline.perturb`) instead
    of copying it, so the binding stays correct across millions of evaluations while the
    values underneath it change.

    `predicate` may be source text or an already-compiled code object; `equiv` compiles
    each ledger once up front and passes code objects.
    """

    def __init__(self, facts):
        self.env = {"facts": facts, "math": math, "statistics": statistics}

    def __call__(self, predicate):
        return eval(predicate, self.env)
