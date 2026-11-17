"""The INPUT CLOSURE of a CI job: every file whose bytes can change what the job prints.

Since 2026-11-17 (yachi's decision) a PR or main push may SKIP a job whose closure is
unchanged since a green run of it; a daily schedule runs everything.  That trade is only
safe while the closure is a superset of what the job reads, so it is built from two halves
and checked from a third:

  * CODE, derived.  Python by an `ast` import walk from every `python3 -m X` / script named
    in the job's own `run:` blocks (read through `bin/verify-repo`'s scanner, so nothing is
    copied); a Python module's sibling data files come with it (prose JSON, transcriptions);
    TS and Rust by the tree rule `pipeline/sim/oracle-cache.ts` already uses (all of
    `pipeline/sim` and `pipeline/openers`, plus every file a relative import reaches outside
    them) whenever a block runs bun, node or cargo; shell scripts a block names, scanned for
    the same tokens; and all of `bin/`.
  * DATA, declared.  `roots` on each `PLAN` entry in `bin/verify-repo`: coarse directories
    (`sessions/`, `analysis/`, …) or glob patterns, with `{session}` standing for the matrix
    value's session directory.  Coarse on purpose: a new file under a root moves the hash.
  * Always in: the job's own YAML block (with a matrix job's VALUE LIST taken out and the
    value itself put in, so adding a session does not re-run every other entry), the
    workflow's text before `jobs:` (the tool pins and the triggers), and the job name.

Checked by `bin/verify-repo --check` (every entry point a block names resolves into the
closure), `bin/verify-repo --audit-inputs` (strace: a tracked file opened outside the
closure is an error) and the daily `bin/input-hash audit` (inotify, on the runner).

The hash is sha256 over the sorted `(path, blob sha)` pairs from `git ls-files -s`; a file
modified or untracked in the working tree goes through `git hash-object`, so a local edit
moves the hash before it is committed.
"""
import ast
import fnmatch
import hashlib
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FORMAT = "input-closure/1"

# The TS/Rust tree rule: oracle-cache.ts hashes all of pipeline/sim; the openers tests and
# emitters live in pipeline/openers and import across the two.
TS_TREES = ("pipeline/sim/", "pipeline/openers/")
TS_RUNNERS = re.compile(r"(?:^|[\s;&|(])(?:bun|bunx|node|cargo|tsc)(?:\s|$)", re.M)
TS_EXT = (".ts", ".tsx", ".mts", ".js", ".mjs", ".cjs")
LOCKFILES = ("Cargo.lock", "Cargo.toml", "bun.lock", "bun.lockb", "package.json",
             "tsconfig.json")

_PY_M = re.compile(r"python3?\s+(?:-[IuBO]+\s+)*-m\s+([A-Za-z_][\w.]*)")
_PY_S = re.compile(r"python3?\s+(?:-[IuBO]+\s+)*([\w./-]+\.py)\b")
_INTERP_S = re.compile(r"(?:bash|sh|Rscript|bun(?:\s+run)?|node)\s+(?:-\S+\s+)*([\w./-]+\.(?:sh|R|ts|mjs|js))\b")
_PATHISH = re.compile(r"(?<![\w$/.-])((?:\./)?[A-Za-z0-9_.@-]+(?:/[A-Za-z0-9_.*@-]+)+/?)")


def git(*args, cwd=REPO):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True,
                          check=True).stdout


class Tree:
    """Tracked files with their blob ids, overlaid by the working tree's edits."""

    def __init__(self, repo=REPO):
        self.repo = Path(repo)
        self.blob = {}
        for ln in git("ls-files", "-s", "-z", cwd=self.repo).split("\0"):
            if ln:
                meta, path = ln.split("\t", 1)
                self.blob[path] = meta.split()[1]
        dirty = []
        for ln in git("status", "--porcelain=v1", "-z", "--untracked-files=all",
                      cwd=self.repo).split("\0"):
            if len(ln) > 3 and ln[2] == " ":
                dirty.append(ln[3:])
        live = [p for p in dirty if (self.repo / p).is_file()]
        for p in set(dirty) - set(live):
            self.blob.pop(p, None)
        if live:
            out = subprocess.run(["git", "hash-object", "--stdin-paths"], cwd=self.repo,
                                 input="\n".join(live) + "\n", capture_output=True,
                                 text=True, check=True).stdout.split()
            self.blob.update(zip(live, out))
        self.files = sorted(self.blob)

    def under(self, root):
        """Every file a root names: a directory (trailing `/`), a glob, or one file."""
        if any(c in root for c in "*?["):
            return [f for f in self.files if fnmatch.fnmatchcase(f, root)]
        if root.endswith("/"):
            return [f for f in self.files if f.startswith(root)]
        if root in self.blob:
            return [root]
        pre = root.rstrip("/") + "/"
        return [f for f in self.files if f.startswith(pre)]


# ------------------------------------------------------------------ python walk

def _module_file(tree, mod, base=""):
    rel = mod.replace(".", "/")
    for cand in (f"{base}{rel}.py", f"{base}{rel}/__init__.py"):
        if cand in tree.blob:
            return cand
    return None


_IMPORTS = {}


def _python_imports(tree, path):
    """Files one Python file reaches by import, memoised on (repo, path, blob)."""
    key = (str(tree.repo), path, tree.blob.get(path))
    if key not in _IMPORTS:
        _IMPORTS[key] = frozenset(_python_imports_uncached(tree, path))
    return set(_IMPORTS[key])


def _python_imports_uncached(tree, path):
    try:
        src = (tree.repo / path).read_text()
        mod = ast.parse(src)
    except (OSError, SyntaxError, UnicodeDecodeError):
        return set()
    here = path.rsplit("/", 1)[0] + "/" if "/" in path else ""
    pkg = path[:-3].replace("/", ".") if path.endswith(".py") else ""
    out = set()

    def add(name, sibling_ok=True):
        for base in ("", here) if sibling_ok else ("",):
            parts = name.split(".")
            # `from a.b import c` may name a module `a.b.c` or an attribute of `a.b`.
            for k in range(len(parts), 0, -1):
                f = _module_file(tree, ".".join(parts[:k]), base)
                if f:
                    out.add(f)
                    # every package __init__ on the way runs too
                    for j in range(1, k):
                        g = _module_file(tree, ".".join(parts[:j]), base)
                        if g and g.endswith("__init__.py"):
                            out.add(g)
                    return

    for node in ast.walk(mod):
        if isinstance(node, ast.Import):
            for a in node.names:
                add(a.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                package = pkg.split(".")[:-1]
                parent = package[: len(package) - (node.level - 1)]
                stem = ".".join(parent + ([node.module] if node.module else []))
                for a in node.names:
                    add(f"{stem}.{a.name}" if stem else a.name, sibling_ok=False)
                if stem:
                    add(stem, sibling_ok=False)
            elif node.module:
                for a in node.names:
                    add(f"{node.module}.{a.name}")
                add(node.module)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            v = node.value
            # importlib.import_module("pipeline.x") / runpy / a module named in a table
            if re.fullmatch(r"(?:pipeline|spec|analysis)(?:\.\w+)+", v):
                add(v, sibling_ok=False)
            # a script path or data path spelled in full from the repo root
            elif re.fullmatch(r"[\w.-]+(?:/[\w.@-]+)+", v) and v in tree.blob:
                out.add(v)
    return out


def _is_python(tree, path):
    if path.endswith(".py"):
        return True
    try:
        with open(tree.repo / path, "rb") as fh:
            first = fh.readline()
    except OSError:
        return False
    return first.startswith(b"#!") and b"python" in first


def _python_closure(tree, seeds):
    seen, todo = set(), list(seeds)
    while todo:
        p = todo.pop()
        if p in seen or p not in tree.blob:
            continue
        seen.add(p)
        if _is_python(tree, p):
            todo.extend(_python_imports(tree, p) - seen)
    # sibling data: a module reads files beside itself through Path(__file__).parent
    data = set()
    for p in seen:
        if p.endswith(".py") and "/" in p:
            d = p.rsplit("/", 1)[0] + "/"
            data.update(f for f in tree.files
                        if f.startswith(d) and "/" not in f[len(d):] and not f.endswith(".py"))
    return seen | data


# ------------------------------------------------------------------- TS walk

_TS_IMPORT = re.compile(r"""(?:from|import|require)\s*\(?\s*['"](\.{1,2}/[^'"]+)['"]""")


def _ts_closure(tree):
    files = {f for t in TS_TREES for f in tree.under(t)}
    files |= {f for f in tree.files if f.rsplit("/", 1)[-1] in LOCKFILES}
    todo = [f for f in files if f.endswith(TS_EXT)]
    while todo:
        f = todo.pop()
        try:
            src = (tree.repo / f).read_text()
        except (OSError, UnicodeDecodeError):
            continue
        base = f.rsplit("/", 1)[0]
        for spec in _TS_IMPORT.findall(src):
            tgt = str(Path(base, spec)).replace("\\", "/")
            tgt = "/".join(_norm(tgt.split("/")))
            cands = [tgt] + [tgt + e for e in TS_EXT] + [tgt + "/index" + e for e in TS_EXT]
            for c in cands:
                if c in tree.blob and c not in files:
                    files.add(c)
                    if c.endswith(TS_EXT):
                        todo.append(c)
                    break
            else:
                # a directory import (`../vendor/x`) brings the whole directory
                more = [x for x in tree.under(tgt + "/") if x not in files]
                files.update(more)
                todo.extend(x for x in more if x.endswith(TS_EXT))
    return files


def _norm(parts):
    out = []
    for p in parts:
        if p in ("", "."):
            continue
        if p == "..":
            if out:
                out.pop()
            continue
        out.append(p)
    return out


# ------------------------------------------------------------- the closure

class Closure:
    def __init__(self, files, texts, unresolved):
        self.files = files            # set of repo-relative paths
        self.texts = texts            # [(label, text)] hashed beside the files
        self.unresolved = unresolved  # [(step name, token, why)]

    def digest(self, tree):
        h = hashlib.sha256(FORMAT.encode() + b"\n")
        for label, text in self.texts:
            h.update(f"text\0{label}\0{hashlib.sha256(text.encode()).hexdigest()}\n".encode())
        for f in sorted(self.files):
            h.update(f"file\0{f}\0{tree.blob[f]}\n".encode())
        return h.hexdigest()


def session_dir(value):
    m = re.search(r"(\d{4}-\d{2}-\d{2})", value or "")
    return f"sessions/{m.group(1)}/" if m else None


def job_texts(job, matrix_dim, matrix_val, workflows):
    """The job's own YAML block (matrix value list removed) and the workflow head."""
    text = (workflows / job.file).read_text()
    lines = text.split("\n")
    head = text[: text.index("\njobs:\n")]
    start = job.line - 1
    end = start + 1
    while end < len(lines) and not re.match(r"^  [A-Za-z0-9_-]+: *$", lines[end]) \
            and not (lines[end] and not lines[end].startswith(" ")):
        end += 1
    block = lines[start:end]
    if matrix_dim:
        out, i = [], 0
        while i < len(block):
            ln = block[i]
            m = re.match(rf"^        {re.escape(matrix_dim)}: *(.*)$", ln)
            if not m:
                out.append(ln)
                i += 1
                continue
            out.append(f"        {matrix_dim}: <value>")
            i += 1
            inline = m.group(1).split(" #")[0].strip()
            if inline.startswith("["):              # flow sequence, maybe wrapped
                while not inline.rstrip().endswith("]") and i < len(block):
                    inline = block[i].strip()
                    i += 1
            else:                                   # block sequence at indent 10
                while i < len(block) and (block[i].startswith("          ")
                                          or not block[i].strip()):
                    i += 1
        block = out
    return [(f"{job.file}#head", head),
            (f"{job.file}#job:{job.name}", "\n".join(block)),
            ("matrix", f"{matrix_dim}={matrix_val}")]


def _run_texts(job, entry, interpolate, matrix_dim, matrix_val):
    for s in job.steps:
        if s.run is None:
            continue
        try:
            yield s, interpolate(s.run, job.env, matrix_dim, matrix_val)
        except Exception:
            yield s, s.run


def entry_points(text):
    """(kind, token) for every program a run block hands to an interpreter."""
    for m in _PY_M.finditer(text):
        yield "module", m.group(1)
    for m in _PY_S.finditer(text):
        yield "script", m.group(1)
    for m in _INTERP_S.finditer(text):
        yield "script", m.group(1)
    for m in re.finditer(r"(?:^|[\s;&|(`])((?:\./)?bin/[\w.-]+)", text):
        yield "script", m.group(1)


def closure(job, entry, interpolate, matrix_dim=None, matrix_val=None, tree=None,
            workflows=None):
    tree = tree or Tree()
    workflows = workflows or REPO / ".github" / "workflows"
    files, unresolved, seeds = set(), [], set()
    files.update(tree.under("bin/"))
    seeds.update(tree.under("bin/"))
    sess = session_dir(matrix_val)
    for root in getattr(entry, "roots", ()) or ():
        if "{session}" in root:
            if not sess:
                unresolved.append(("(roots)", root, "no session in the matrix value"))
                continue
            root = root.replace("{session}", sess)
        hit = tree.under(root)
        if not hit:
            unresolved.append(("(roots)", root, "root names no tracked file"))
        files.update(hit)
    uses_ts = False
    scanned_sh = set()
    # (step, text, working directory, the directory of the script the text came from — a
    # script that does `cd "$(dirname "$0")"` names its neighbours relative to itself)
    todo = [(s, txt, s.workdir or "", "") for s, txt in _run_texts(job, entry, interpolate,
                                                                   matrix_dim, matrix_val)]
    while todo:
        s, txt, wd, here = todo.pop()
        if TS_RUNNERS.search(txt):
            uses_ts = True
        for kind, tok in entry_points(txt):
            if kind == "module":
                f = _module_file(tree, tok)
                if not f:
                    unresolved.append((s.name, tok, "python -m names no module in the repo"))
                    continue
                seeds.add(f)
                parts = tok.split(".")
                for j in range(1, len(parts)):
                    g = _module_file(tree, ".".join(parts[:j]))
                    if g:
                        seeds.add(g)
            else:
                t = tok[2:] if tok.startswith("./") else tok
                cands = [t] + ([f"{wd.rstrip('/')}/{t}"] if wd else []) + \
                    ([f"{here}/{t}"] if here else [])
                f = next((c for c in cands if c in tree.blob), None)
                if not f:
                    unresolved.append((s.name, tok, "names no tracked file"))
                    continue
                seeds.add(f)
                if f.endswith(".sh") and f not in scanned_sh:
                    scanned_sh.add(f)
                    todo.append((s, (tree.repo / f).read_text(), wd,
                                 f.rsplit("/", 1)[0] if "/" in f else ""))
        # every other path-shaped token that names tracked files: data the block passes in
        for m in _PATHISH.finditer(txt):
            t = m.group(1)
            t = t[2:] if t.startswith("./") else t
            for base in ("", wd.rstrip("/") + "/" if wd else ""):
                hit = tree.under(base + t) if (base + t).split("/")[0] in _TOP(tree) else []
                files.update(hit)
                seeds.update(h for h in hit if h.endswith((".py", ".sh")))
    files |= _python_closure(tree, seeds)
    if uses_ts:
        files |= _ts_closure(tree)
    return Closure(files, job_texts(job, matrix_dim, matrix_val, workflows), unresolved)


_TOPS = {}


def _TOP(tree):
    k = id(tree)
    if k not in _TOPS:
        _TOPS[k] = {f.split("/")[0] for f in tree.files}
    return _TOPS[k]


def green_dir(repo=REPO):
    """Where a LOCAL green mark lives: `verify-green/` in the git COMMON dir, so every
    worktree of one clone shares it (in a worktree `.git` is a file, not a directory)."""
    d = git("rev-parse", "--git-common-dir", cwd=repo).strip()
    return (Path(repo) / d if not Path(d).is_absolute() else Path(d)) / "verify-green"


def artifact_name(job, matrix_val, digest):
    mv = re.sub(r"[^A-Za-z0-9._-]+", "_", matrix_val or "").strip("_") or "-"
    return f"green-{job}-{mv}-{digest}"


# ------------------------------------------------------------------ the audit

CODE_EXT = (".py", ".pyc", ".ts", ".tsx", ".js", ".mjs", ".cjs", ".rs", ".sh", ".lean")


def audit(cl, tree, opened, listed):
    """Problems for one observed run: a tracked file opened outside the closure, or a
    directory listed whose tracked data files the closure does not wholly contain.

    A listing is held to its DATA files only.  Python's import finder and bun's resolver
    list every directory on their search path (the repo root, `pipeline/`), and that is
    resolution, not reading: what they then open is caught by the first rule.  The repo
    root is exempt for the same reason — every interpreter started there lists it."""
    bad = []
    for f in sorted(set(opened)):
        if f in tree.blob and f not in cl.files:
            bad.append(f"opened outside the closure: {f}")
    for d in sorted(set(listed)):
        d = d.strip("/")
        if not d:
            continue
        kids = [f for f in tree.files if f.startswith(d + "/") and "/" not in f[len(d) + 1:]
                and not f.endswith(CODE_EXT)]
        miss = [f for f in kids if f not in cl.files]
        if miss:
            bad.append(f"listed {d}/ but the closure lacks {len(miss)} of its files "
                       f"(e.g. {miss[0]})")
    return bad


def parse_strace(lines, repo=REPO, cwd=REPO):
    opened, listed = set(), set()
    root = str(repo)
    for ln in lines:
        m = re.search(r'\b(openat|open|execve)\((?:AT_FDCWD, |\d+, )?"([^"]+)"(.*)\)\s+= (-?\d+)', ln)
        if not m or m.group(4).startswith("-"):
            continue
        p, flags = m.group(2), m.group(3)
        p = p if p.startswith("/") else str(Path(cwd, p))
        p = str(Path(p).resolve()) if ".." in p else p
        if not p.startswith(root + "/") and p != root:
            continue
        rel = p[len(root) + 1:]
        if "__pycache__" in rel or rel.startswith(".git/"):
            continue
        (listed if "O_DIRECTORY" in flags else opened).add(rel)
    return opened, listed


def parse_inotify(lines, repo=REPO):
    opened, listed = set(), set()
    root = str(repo)
    for ln in lines:
        ev, _, p = ln.rstrip("\n").partition(" ")
        if "OPEN" not in ev.split(","):
            continue
        p = p.rstrip("/")
        if not p.startswith(root):
            continue
        rel = p[len(root) + 1:]
        if not rel or rel.startswith(".git/") or "__pycache__" in rel:
            if not rel and "ISDIR" in ev:
                listed.add("")
            continue
        (listed if "ISDIR" in ev else opened).add(rel)
    return opened, listed
