#!/usr/bin/env python
# code extracted from: http://rosettacode.org/wiki/S-Expressions
# Originally taken from: https://gitlab.com/kicad/libraries/kicad-library-utils/-/blob/master/common/sexpr.py

import re
from typing import List, Optional, Any

dbg = False

term_regex = r'''(?mx)
    \s*(?:
        (?P<brackl>\()|
        (?P<brackr>\))|
        (?P<num>[+-]?\d+\.\d+(?=[\ \)])|\-?\d+(?=[\ \)]))|
        (?P<sq>"(?:[^"]|(?<=\\)")*"(?:(?=\))|(?=\s)))|
        (?P<s>[^(^)\s]+)
       )'''

def parse_sexp(sexp):
    stack = []
    out = []
    if dbg: print("%-6s %-14s %-44s %-s" % tuple("term value out stack".split()))
    for termtypes in re.finditer(term_regex, sexp):
        term, value = [(t,v) for t,v in termtypes.groupdict().items() if v][0]
        if dbg: print("%-7s %-14s %-44r %-r" % (term, value, out, stack))
        if   term == 'brackl':
            stack.append(out)
            out = []
        elif term == 'brackr':
            assert stack, "Trouble with nesting of brackets"
            tmpout, out = out, stack.pop(-1)
            out.append(tmpout)
        elif term == 'num':
            v = float(value)
            if v.is_integer(): v = int(v)
            out.append(v)
        elif term == 'sq':
            out.append(value[1:-1].replace(r'\"', '"'))
        elif term == 's':
            out.append(value)
        else:
            raise NotImplementedError("Error: %r" % (term, value))
    assert not stack, "Trouble with nesting of brackets"
    return out[0]


def parse_bool(arr: List[str]) -> bool:
    # KiCad8 syntax uses `(key "yes")`, but KiCad7 may use `(key "true")` or `key`
    if len(arr) == 1 or arr[1] == "yes" or arr[1] == "true":
        return True
    else:
        return False


def val_to_str(val: Any) -> str:
    if isinstance(val, bool):
        if val:
            return "yes"
        else:
            return "no"

    if isinstance(val, list):
        ret = ""
        for elem in val:
            ret += maybe_to_sexpr(elem)
        return ret
    if isinstance(val, float):
        return f"{round(val,6):.6f}".rstrip("0").rstrip(".")
    if isinstance(val, int) or isinstance(val, Rstr) or isinstance(val, bytes):
        return str(val)
    if isinstance(val, str):
        val = val.replace('"', '\\"')
        return f'"{val}"'

    return val.to_sexpr()  # This will throw exceptions if type does not have to_sexpr()


def maybe_to_sexpr(val: Any, name: str = "", indent=1, newline=False) -> str:
    if val is None:
        return ""

    if isinstance(val, tuple):
        v = maybe_to_sexpr(val[0], val[1])
        if v == "":
            return ""
    else: 
        v = val_to_str(val)

    indents = " " * indent
    if name == "":
        return f"{indents}{v}"
    else:
        endline = "\n" if newline else ""
        return f"{indents}({name} {v}){endline}"

class Rstr(str):
    """Bare wrapper around `str` to enable maybe_to_sexpr serialization without quotes."""
    pass