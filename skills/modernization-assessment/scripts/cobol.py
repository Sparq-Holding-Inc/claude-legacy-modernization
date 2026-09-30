#!/usr/bin/env python3
"""COBOL fixed-format reader and fact extractor. Python standard library only.

What it reads
-------------
Fixed format only: columns 7 to 72, a * or / in column 7 is a comment, a dash
in column 7 continues the line before. Free format source is reported as
unparsed. It does not guess.

What it finds, per program
--------------------------
CALL, EXEC CICS LINK and XCTL, COPY (expanded, so a statement inside a
copybook counts for every program that copies it), SELECT ... ASSIGN, OPEN
modes, FD layouts, READ INTO and WRITE FROM records, EXEC CICS file I/O,
EXEC SQL table references, and the literal MOVEs and VALUE clauses needed to
resolve a variable target.

Variable targets follow four rules (the same rules the CardDemo labelers used):
1. Constant: the name has a VALUE literal and is never the receiver of a
   MOVE, STRING, READ INTO, ACCEPT or similar. Treat it as that literal.
2. Literal moves: every literal moved to the name is a candidate.
3. Dynamic remainder: unless the name is a pure constant, the target set is
   not proven complete, so an unresolved dynamic edge is emitted as well.
4. Subscripted names are dynamic only.
"""

import bisect
import collections
import os
import re

Loc = collections.namedtuple("Loc", "file line via")

CODE_EXT = {".cbl", ".cob", ".cobol", ".pco", ".cbx"}
COPY_EXT = {".cpy", ".copy"}
MASK = "\x01"

NAME = r"[A-Z0-9][A-Z0-9_-]*"
_NB = r"(?<![A-Z0-9_-])"          # not inside a longer COBOL word
I = re.I

COPY_KW = re.compile(_NB + r"COPY(?=\s|$)", I)
COPY_STMT = re.compile(r"COPY\s+(?:(['\"])(" + MASK + r"+)\1|(" + NAME + r"))", I)
STMT_END = re.compile(r"\.(?:\s|$)")
FREE_FMT = re.compile(r"^\s*>>\s*SOURCE\s+FORMAT\s+(?:IS\s+)?FREE", I | re.M)
EXEC_BLOCK = re.compile(_NB + r"EXEC\s+(CICS|SQL|SQLIMS|DLI)\b(.*?)" + _NB + r"END-EXEC", I | re.S)
PROGRAM_ID = re.compile(_NB + r"PROGRAM-ID\s*\.?\s+(" + NAME + r")", I)
CALL_RE = re.compile(_NB + r"CALL\s+(?:(['\"])(" + MASK + r"*)\1|(" + NAME + r")(\s*\([^)]*\))?)", I)
SELECT_RE = re.compile(_NB + r"SELECT\s+(?:OPTIONAL\s+)?(" + NAME + r")\s+ASSIGN\s+(?:TO\s+)?"
                       r"(?:(['\"])(" + MASK + r"*)\2|(" + NAME + r"))", I)
ORG_RE = re.compile(r"ORGANI[SZ]ATION\s+(?:IS\s+)?(INDEXED|RELATIVE|SEQUENTIAL|LINE\s+SEQUENTIAL)", I)
FD_RE = re.compile(_NB + r"FD\s+(" + NAME + r")\b[^.]*\.", I)
FD_END = re.compile(_NB + r"(?:FD|SD)\s+" + NAME + r"\b[^.]*\.|" + _NB + r"(?:WORKING-STORAGE|LINKAGE|LOCAL-STORAGE"
                    r"|COMMUNICATION|REPORT)\s+SECTION|" + _NB + r"PROCEDURE\s+DIVISION", I)
REC01 = re.compile(_NB + r"01\s+(" + NAME + r")", I)
OPEN_RE = re.compile(_NB + r"OPEN\s+", I)
TOKEN = re.compile(r"\s*(" + NAME + r"|\.|\S)", I)
READ_INTO = re.compile(_NB + r"READ\s+(" + NAME + r")(?:\s+(?:NEXT|PREVIOUS|RECORD))*\s+INTO\s+(" + NAME + r")", I)
WRITE_FROM = re.compile(_NB + r"(?:WRITE|REWRITE)\s+(" + NAME + r")\s+FROM\s+(" + NAME + r")", I)
MOVE_RE = re.compile(_NB + r"MOVE\s+(?:CORR(?:ESPONDING)?\s+)?(?:(['\"])(" + MASK + r"*)\1|(" + NAME + r")"
                     r"(?:\s*\([^)]*\))?|(\S+))\s+TO\s+", I)
VALUE_RE = re.compile(_NB + r"(\d\d)\s+(" + NAME + r")\b[^.]*?" + _NB + r"VALUE\s+(?:IS\s+)?(['\"])(" + MASK + r"*)\3", I)
OTHER_RECV = [
    re.compile(_NB + r"ACCEPT\s+(" + NAME + r")", I),
    re.compile(_NB + r"INITIALIZE\s+(" + NAME + r")", I),
    re.compile(_NB + r"(?:STRING|UNSTRING)\b.*?\bINTO\s+(" + NAME + r")", I | re.S),
    re.compile(_NB + r"SET\s+(" + NAME + r")\s+TO\b", I),
]
STOP = frozenset("""MOVE IF ELSE END-IF PERFORM END-PERFORM EXEC CALL GO GOBACK STOP DISPLAY ADD SUBTRACT
COMPUTE MULTIPLY DIVIDE READ WRITE REWRITE OPEN CLOSE INITIALIZE STRING UNSTRING INSPECT EVALUATE WHEN
SET ACCEPT CONTINUE EXIT NEXT NOT AND OR END-EVALUATE END-READ END-WRITE AT INVALID SEARCH SORT START
DELETE RETURN RELEASE ALTER CANCEL COPY END-CALL END-STRING THEN WITH ROUNDED SIZE ON""".split())

CICS_VERB = re.compile(r"\s*([A-Z]+)", I)
CICS_PROGRAM = re.compile(_NB + r"PROGRAM\s*\(\s*(?:(['\"])(" + MASK + r"*)\1|(" + NAME + r")\s*(\([^)]*\))?)\s*\)", I)
CICS_FILE = re.compile(_NB + r"(?:FILE|DATASET)\s*\(\s*(?:(['\"])(" + MASK + r"*)\1|(" + NAME + r")\s*(\([^)]*\))?)\s*\)", I)
CICS_INTO = re.compile(_NB + r"INTO\s*\(\s*(" + NAME + r")", I)
CICS_FROM = re.compile(_NB + r"FROM\s*\(\s*(" + NAME + r")", I)
CICS_SET = re.compile(_NB + r"SET\s*\(\s*(" + NAME + r")", I)
CICS_MODE = {"READ": "read", "READNEXT": "read", "READPREV": "read", "STARTBR": "read",
             "ENDBR": "read", "RESETBR": "read", "UNLOCK": "read",
             "WRITE": "write", "REWRITE": "write", "DELETE": "write"}
OPEN_MODE = {"INPUT": "read", "OUTPUT": "write", "EXTEND": "write", "I-O": "read_write"}
DD_PREFIX = re.compile(r"^(?:UT-S-|DA-S-|AS-S-|UT-A-|DA-A-|S-|AS-|UT-|DA-)(.+)$", I)

SQL_TABLE = r"([A-Z][A-Z0-9_$#@.]*)"
SQL_READ = re.compile(_NB + r"FROM\s+" + SQL_TABLE + r"(?:\s+(?!WHERE|GROUP|ORDER|FOR|WITH|UNION|FETCH|HAVING|JOIN)"
                      r"[A-Z][A-Z0-9_]*)?((?:\s*,\s*" + SQL_TABLE + r"(?:\s+[A-Z][A-Z0-9_]*)?)*)", I)
SQL_JOIN = re.compile(_NB + r"JOIN\s+" + SQL_TABLE, I)
SQL_INSERT = re.compile(_NB + r"INSERT\s+INTO\s+" + SQL_TABLE, I)
SQL_UPDATE = re.compile(_NB + r"UPDATE\s+" + SQL_TABLE, I)
SQL_DELETE = re.compile(_NB + r"DELETE\s+FROM\s+" + SQL_TABLE, I)
SQL_INCLUDE = re.compile(_NB + r"INCLUDE\s+(" + NAME + r")", I)


# ------------------------------------------------------------------ reading

def read_text(path):
    with open(path, "rb") as fh:
        return fh.read().decode("latin-1")


def is_free_format(text):
    return bool(FREE_FMT.search(text))


def _open_quote(code):
    """Return the quote character still open at the end of code, else None."""
    q = None
    i = 0
    while i < len(code):
        ch = code[i]
        if q:
            if ch == q:
                if code[i + 1:i + 2] == q:
                    i += 1
                else:
                    q = None
        elif ch in "'\"":
            q = ch
        i += 1
    return q


def mask(code):
    """Blank out literal contents and inline *> comments. Length is preserved."""
    out = []
    q = None
    i = 0
    n = len(code)
    while i < n:
        ch = code[i]
        if q:
            if ch == q:
                if code[i + 1:i + 2] == q:
                    out.append(MASK * 2)
                    i += 2
                    continue
                q = None
                out.append(ch)
            else:
                out.append(MASK)
        elif ch in "'\"":
            q = ch
            out.append(ch)
        elif ch == "*" and code[i:i + 2] == "*>":
            out.append(" " * (n - i))
            break
        else:
            out.append(ch)
        i += 1
    return "".join(out)


class Chunk:
    """One logical code line and where it physically came from.

    via is the (file, line) of the top level COPY statement that pulled this line in,
    or None when the line belongs to the program itself.
    """
    __slots__ = ("file", "line", "code", "masked", "via")

    def __init__(self, file, line, code, via=None):
        self.file, self.line, self.code, self.via = file, line, code, via
        self.masked = mask(code)

    def clone_via(self, via):
        c = Chunk.__new__(Chunk)
        c.file, c.line, c.code, c.masked, c.via = self.file, self.line, self.code, self.masked, via
        return c


def logical_chunks(rel, text):
    """Fixed format text to logical lines. Comments dropped, continuations joined."""
    segs = []            # [line, code, open_quote]
    for i, raw in enumerate(text.replace("\r\n", "\n").replace("\r", "\n").split("\n"), start=1):
        line = raw.expandtabs(8)
        ind = line[6] if len(line) > 6 else " "
        code = line[7:72] if len(line) > 7 else ""
        if ind in "*/":
            continue
        if ind == "-" and segs:
            prev = segs[-1]
            piece = code.lstrip(" ")
            if prev[2] and piece[:1] == prev[2]:
                piece = piece[1:]
                prev[1] += piece
            elif prev[2]:
                prev[1] += piece
            else:
                prev[1] = prev[1].rstrip() + " " + piece
            prev[2] = _open_quote(prev[1])
            continue
        if not code.strip():
            continue
        oq = _open_quote(code)
        segs.append([i, code if oq else code.rstrip(), oq])
    return [Chunk(rel, s[0], s[1]) for s in segs]


def count_loc(text):
    n = 0
    for raw in text.replace("\r\n", "\n").split("\n"):
        line = raw.expandtabs(8)
        if len(line) > 7 and line[6] not in "*/" and line[7:72].strip():
            n += 1
    return n


# ------------------------------------------------------------ copybook library

class CopyLibrary:
    """Copybooks found in the tree, keyed by upper case member name."""

    def __init__(self, root, rel_paths):
        self.root = root
        self.by_name = {}
        self.path_to_id = {}
        for rel in sorted(rel_paths):
            stem = os.path.splitext(os.path.basename(rel))[0].upper()
            if stem not in self.by_name:
                self.by_name[stem] = rel
                self.path_to_id[rel] = "cpy:" + stem
        self._chunks = {}
        self._records = {}

    def find(self, name):
        rel = self.by_name.get(name.upper())
        return (self.path_to_id[rel], rel) if rel else None

    def raw_chunks(self, rel):
        if rel not in self._chunks:
            self._chunks[rel] = logical_chunks(rel, read_text(os.path.join(self.root, rel)))
        return self._chunks[rel]

    def records(self, rel):
        """01 level names a copybook defines."""
        if rel not in self._records:
            text = "\n".join(c.masked for c in self.raw_chunks(rel))
            self._records[rel] = {m.group(1).upper() for m in REC01.finditer(text)}
        return self._records[rel]


def expand(chunks, lib, includes, used, depth=0, stack=(), do_expand=True):
    """Replace COPY statements by the copybook text. Record includes and used copybooks.

    includes: list of (name, file, line) for COPY statements found in these chunks.
    used: ordered list of copybook ids expanded anywhere below.
    """
    out = []
    i, n = 0, len(chunks)
    while i < n:
        ch = chunks[i]
        m = COPY_KW.search(ch.masked)
        if not m:
            out.append(ch)
            i += 1
            continue
        parts = [ch.masked[m.start():]]
        j = i
        while not STMT_END.search(" ".join(parts)) and j + 1 < n and j - i < 30:
            j += 1
            parts.append(chunks[j].masked)
        stmt = " ".join(parts)
        sm = COPY_STMT.match(stmt)
        if not sm:
            out.append(ch)
            i += 1
            continue
        if sm.group(1):      # COPY 'MEMBER' or COPY "MEMBER": the name sits in a masked literal
            orig_stmt = " ".join([ch.code[m.start():]] + [chunks[k].code for k in range(i + 1, j + 1)])
            name = orig_stmt[sm.start(2):sm.end(2)].strip().upper()
        else:
            name = sm.group(3).upper()
        includes.append((name, ch.file, ch.line))
        prefix = ch.code[:m.start()]
        if prefix.strip():
            out.append(Chunk(ch.file, ch.line, prefix))
        last = chunks[j]
        em = STMT_END.search(last.masked, m.end() if j == i else 0)
        suffix = last.code[em.end():] if em else ""
        found = lib.find(name) if do_expand else None
        if found and name not in stack and depth < 8:
            cid, rel = found
            if cid not in used:
                used.append(cid)
            # nested COPY statements are cpy to cpy includes, found when the copybook itself is parsed
            sub = expand(lib.raw_chunks(rel), lib, [], used, depth + 1, stack + (name,), do_expand)
            if depth == 0:
                sub = [c if c.via else c.clone_via((ch.file, ch.line)) for c in sub]
            out.extend(sub)
        if suffix.strip():
            out.append(Chunk(last.file, last.line, suffix))
        i = j + 1
    return out


# ------------------------------------------------------------------ facts

class Facts:
    def __init__(self, rel):
        self.path = rel
        self.program_id = None
        self.has_cics = False
        self.includes = []       # (name, file, line), direct COPY statements only
        self.calls = []          # dict(verb, literal, var, subscripted, file, line)
        self.cics_files = []     # dict(verb, mode, literal, var, subscripted, into, from_, file, line)
        self.sql = []            # dict(table, mode, file, line)
        self.sql_includes = []   # (name, file, line)
        self.selects = {}        # file name -> dict(dd, org, file, line)
        self.opens = {}          # file name -> dict(modes:set, lines:[(file,line)])
        self.fd_layout = {}      # file name -> [cpy ids]
        self.fd_records = {}     # 01 name -> file name
        self.rec_uses = []       # (file name or None, fd record or None, record var)
        self.values = {}         # NAME -> (literal, (file,line))
        self.literal_moves = {}  # NAME -> [(literal, (file,line))]
        self.moves_from_name = []  # (source NAME, receiver NAME, (file,line))
        self.receivers = set()   # names that can receive a non literal value
        self.used_copybooks = []
        self.local_records = set()
        self.cpy_records = {}

    # ----- variable target resolution -----
    def _const_value(self, name):
        up = name.upper()
        if up in self.values and up not in self.receivers and up not in self.literal_moves:
            return self.values[up]
        return None

    def resolve(self, var, subscripted=False):
        """Return (kind, [(literal, [(file,line)...])...]). kind is constant, var-literal or dynamic."""
        if subscripted:
            return "dynamic", []
        up = var.upper()
        const = self._const_value(up)
        if const:
            return "constant", [(const[0], [const[1]])]
        cands = {}
        for lit, at in self.literal_moves.get(up, []):
            cands.setdefault(lit, []).append(at)
        for src, recv, at in self.moves_from_name:
            if recv == up:
                c = self._const_value(src)
                if c:
                    cands.setdefault(c[0], []).extend([at, c[1]])
        if cands:
            return "var-literal", [(k, v) for k, v in sorted(cands.items())]
        return "dynamic", []


def _slice(orig, m, gq, gb, gn, gsub):
    """Return (literal or None, name or None, subscripted) from a match."""
    if m.group(gq):
        return orig[m.start(gb):m.end(gb)], None, False
    return None, m.group(gn), bool(m.group(gsub))


def parse_program(root, rel, lib):
    """Parse one COBOL source. Returns Facts, the string 'free-format', or None."""
    text = read_text(os.path.join(root, rel))
    if is_free_format(text):
        return "free-format"
    own = logical_chunks(rel, text)
    if not own:
        return None
    includes, used = [], []
    chunks = expand(own, lib, includes, used)
    f = Facts(rel)
    f.includes = [(nm, fl, ln) for nm, fl, ln in includes if fl == rel]
    f.used_copybooks = used
    orig = "\n".join(c.code for c in chunks)
    masked = "\n".join(c.masked for c in chunks)
    starts, origins, pos = [], [], 0
    for c in chunks:
        starts.append(pos)
        origins.append(Loc(c.file, c.line, c.via))
        pos += len(c.masked) + 1

    def at(off):
        return origins[bisect.bisect_right(starts, off) - 1]

    pm = PROGRAM_ID.search("\n".join(c.masked for c in own))
    if not pm:
        return None
    f.program_id = pm.group(1).upper()

    own_masked = "\n".join(c.masked for c in own)
    f.local_records = {m.group(1).upper() for m in REC01.finditer(own_masked)}
    for cid in used:
        rel_c = next((r for r, i in lib.path_to_id.items() if i == cid), None)
        if rel_c:
            f.cpy_records[cid] = lib.records(rel_c)

    # blank EXEC blocks for the statements that must not see them
    nonexec = list(masked)
    for m in EXEC_BLOCK.finditer(masked):
        for k in range(m.start(), m.end()):
            if nonexec[k] != "\n":
                nonexec[k] = " "
    nonexec = "".join(nonexec)

    # ---- data division facts
    for m in VALUE_RE.finditer(masked):
        if m.group(1) == "88":
            continue
        nm = m.group(2).upper()
        if nm not in f.values:
            f.values[nm] = (orig[m.start(4):m.end(4)].rstrip(), at(m.start()))

    for m in MOVE_RE.finditer(nonexec):
        k = m.end()
        recvs = []
        while True:
            tm = TOKEN.match(nonexec, k)
            if not tm:
                break
            tok = tm.group(1)
            if tok == "." or tok.upper() in STOP or not re.match(NAME + "$", tok, I):
                break
            recvs.append(tok.upper())
            k = tm.end()
            sub = re.compile(r"\s*\([^)]*\)").match(nonexec, k)
            if sub:
                k = sub.end()
        where = at(m.start())
        lit = orig[m.start(2):m.end(2)] if m.group(1) else None
        for r in recvs:
            if lit is not None:
                f.literal_moves.setdefault(r, []).append((lit.rstrip(), where))
            elif m.group(3):
                f.moves_from_name.append((m.group(3).upper(), r, where))
                f.receivers.add(r)
            else:
                f.receivers.add(r)
    # a MOVE of a name that is later resolved as a constant is not a non-literal receiver, so the
    # receivers set above is only used to test constants, and constants are never MOVE receivers.
    for rx in OTHER_RECV:
        for m in rx.finditer(nonexec):
            f.receivers.add(m.group(1).upper())
    for m in READ_INTO.finditer(nonexec):
        f.receivers.add(m.group(2).upper())
    for m in EXEC_BLOCK.finditer(masked):
        if m.group(1).upper() == "CICS":
            for rx in (CICS_INTO, CICS_SET):
                for im in rx.finditer(masked, m.start(), m.end()):
                    f.receivers.add(im.group(1).upper())

    # ---- SELECT / FD / OPEN
    for m in SELECT_RE.finditer(nonexec):
        fname = m.group(1).upper()
        if m.group(2):
            dd = orig[m.start(3):m.end(3)].strip().upper()
        else:
            dd = m.group(4).upper()
        pfx = DD_PREFIX.match(dd)
        if pfx:
            dd = pfx.group(1).upper()
        em = STMT_END.search(nonexec, m.end())
        region = nonexec[m.start():em.end() if em else m.end() + 200]
        om = ORG_RE.search(region)
        f.selects[fname] = {"dd": dd, "org": om.group(1).upper().replace("  ", " ") if om else None,
                            "at": at(m.start())}

    fds = list(FD_RE.finditer(nonexec))
    for m in fds:
        fname = m.group(1).upper()
        em = FD_END.search(nonexec, m.end())
        end = em.start() if em else len(nonexec)
        recs = [r.group(1).upper() for r in REC01.finditer(nonexec, m.end(), end)]
        for r in recs:
            f.fd_records[r] = fname
        lo = bisect.bisect_right(starts, m.end()) - 1
        hi = bisect.bisect_right(starts, max(end - 1, m.end())) - 1
        cpys = []
        for k in range(max(lo, 0), hi + 1):
            cid = lib.path_to_id.get(origins[k][0])
            if cid and cid not in cpys:
                cpys.append(cid)
        f.fd_layout[fname] = cpys

    for m in OPEN_RE.finditer(nonexec):
        k, mode = m.end(), None
        while True:
            tm = TOKEN.match(nonexec, k)
            if not tm:
                break
            up = tm.group(1).upper()
            if up in OPEN_MODE:
                mode = OPEN_MODE[up]
            elif up in f.selects and mode:
                o = f.opens.setdefault(up, {"modes": set(), "lines": []})
                o["modes"].add(mode)
                o["lines"].append(at(m.start()))
            else:
                break
            k = tm.end()

    for m in READ_INTO.finditer(nonexec):
        f.rec_uses.append((m.group(1).upper(), None, m.group(2).upper()))
    for m in WRITE_FROM.finditer(nonexec):
        f.rec_uses.append((None, m.group(1).upper(), m.group(2).upper()))

    # ---- CALL
    for m in CALL_RE.finditer(nonexec):
        lit, var, sub = _slice(orig, m, 1, 2, 3, 4)
        f.calls.append({"verb": "CALL", "literal": lit.strip().upper() if lit is not None else None,
                        "var": var, "subscripted": sub, "at": at(m.start())})

    # ---- EXEC blocks
    for m in EXEC_BLOCK.finditer(masked):
        kind = m.group(1).upper()
        where = at(m.start())
        if kind == "CICS":
            f.has_cics = True
            vm = CICS_VERB.match(masked, m.start(2))
            verb = vm.group(1).upper() if vm else ""
            if verb in ("LINK", "XCTL"):
                pm2 = CICS_PROGRAM.search(masked, m.start(2), m.end(2))
                if pm2:
                    lit, var, sub = _slice(orig, pm2, 1, 2, 3, 4)
                    f.calls.append({"verb": verb, "literal": lit.strip().upper() if lit is not None else None,
                                    "var": var, "subscripted": sub, "at": where})
            elif verb in CICS_MODE:
                fm = CICS_FILE.search(masked, m.start(2), m.end(2))
                if fm:
                    lit, var, sub = _slice(orig, fm, 1, 2, 3, 4)
                    im = CICS_INTO.search(masked, m.start(2), m.end(2))
                    fr = CICS_FROM.search(masked, m.start(2), m.end(2))
                    f.cics_files.append({"verb": verb, "mode": CICS_MODE[verb],
                                         "literal": lit.strip().upper() if lit is not None else None,
                                         "var": var, "subscripted": sub,
                                         "rec": (im or fr).group(1).upper() if (im or fr) else None,
                                         "at": where})
        elif kind == "SQL":
            body = masked[m.start(2):m.end(2)]
            inc = SQL_INCLUDE.match(body.lstrip())
            if inc:
                f.sql_includes.append((inc.group(1).upper(), where[0], where[1]))
                continue
            tables = {}
            for rm in SQL_READ.finditer(body):
                tables.setdefault(rm.group(1).upper(), set()).add("read")
                for extra in re.findall(SQL_TABLE, rm.group(2) or "", I):
                    tables.setdefault(extra.upper(), set()).add("read")
            for rm in SQL_JOIN.finditer(body):
                tables.setdefault(rm.group(1).upper(), set()).add("read")
            for rx in (SQL_INSERT, SQL_UPDATE):
                for rm in rx.finditer(body):
                    tables.setdefault(rm.group(1).upper(), set()).add("write")
            for rm in SQL_DELETE.finditer(body):
                tables.setdefault(rm.group(1).upper(), set()).add("write")
                tables[rm.group(1).upper()].discard("read")
            for t, modes in tables.items():
                if t in ("DUAL",):
                    continue
                f.sql.append({"table": t, "mode": "read_write" if len(modes) > 1 else next(iter(modes)),
                              "at": where})
    return f


def parse_copybook_includes(root, rel, lib):
    """Direct COPY statements inside a copybook, and its line count."""
    text = read_text(os.path.join(root, rel))
    chunks = logical_chunks(rel, text)
    includes = []
    expand(chunks, lib, includes, [], do_expand=False)
    return [(nm, fl, ln) for nm, fl, ln in includes if fl == rel], count_loc(text)


def ev(loc):
    """Evidence tuples for a Loc: where the text is, plus the COPY line that pulled it in."""
    return [(loc.file, loc.line)] + ([loc.via] if loc.via else [])


def layouts_for(f, file_name):
    """Copybook ids that define the record layout of a batch file."""
    out = list(f.fd_layout.get(file_name, []))
    for fname, fdrec, rec in f.rec_uses:
        owner = fname or f.fd_records.get(fdrec)
        if owner != file_name:
            continue
        out += layout_of_record(f, rec)
    return sorted(set(out))


def layout_of_record(f, rec):
    """Copybooks that define the 01 record rec. A record the program defines itself has none."""
    if rec is None or rec in f.local_records:
        return []
    return sorted(cid for cid, names in f.cpy_records.items() if rec in names)
