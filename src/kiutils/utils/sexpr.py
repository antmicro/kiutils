#!/usr/bin/env python
# code extracted from: http://rosettacode.org/wiki/S-Expressions
# Originally taken from: https://gitlab.com/kicad/libraries/kicad-library-utils/-/blob/master/common/sexpr.py

import re
from typing import List, Any, Union, Tuple, ClassVar, Self, Optional, get_args, get_origin, get_type_hints
from dataclasses import fields

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


def from_sexpr(cls: Any, full_exp: Any, w_name: bool = True) -> Any:
    """Deserialization implementation for standard types"""
    exp = full_exp[1:] if w_name else full_exp
    if get_origin(cls) == list:
        obj = []
        for i in exp:
            obj.append(from_sexpr(get_args(cls)[0], i, False))
        return obj
    if get_origin(cls) is Union and type(None) in get_args(cls):
        # Optional[..]
        return from_sexpr(get_args(cls)[0], full_exp)
    if cls == str:
        obj = ""
        for i in exp:
            obj = obj + str(i)
        return obj
    if cls == Rstr:
        obj = Rstr("")
        for i in exp:
            obj = Rstr(obj + str(i) + "\n")
        return obj
    if cls == int or cls == float:
        return cls(exp[0] if isinstance(exp, list) else exp)
    if cls == bool:
        return parse_bool(full_exp)
    return cls.from_sexpr(full_exp)


class SexprAuto:
    """Class that automatically implements Sexpr Ser/Deser for dataclass."""
    sexpr_prefix: ClassVar[str] = ""
    positional_args: ClassVar[List[str]] = []

    @classmethod
    def from_sexpr(cls, exp: list) -> Self:
        """Convert the given S-Expression into a Self object

        Args:
            - exp (list): Part of parsed S-Expression

        Returns:
            - Self: Object of the class initialized with the given S-Expression
        """

        obj = cls()
        positional_idx = 0
        types=get_type_hints(cls)
        for item in exp[1:]:
            if not isinstance(item, list):
                fname = obj.positional_args[positional_idx]
                f = getattr(obj, fname)
                setattr(obj, fname, from_sexpr(type(f), item, False))
                positional_idx += 1
                continue
            for f in fields(obj):
                fval=getattr(obj, f.name)
                if (
                    item[0] == f.name
                    or getattr(fval, "sexpr_prefix", None) == item[0]
                ):
                    setattr(obj, f.name, from_sexpr(types[f.name], item))
        return obj

    def _sexpr_inter_tuple(
        self, name: str, no_name: bool
    ) -> Union[Tuple[Any, str], Any]:
        val = getattr(self, name)
        return val if hasattr(val, "to_sexpr") or no_name else (val, name)

    def to_sexpr(self, indent=0, newline=False) -> str:
        """Generate the S-Expression representing this object

        Args:
            - indent (int): Number of whitespaces used to indent the output. Defaults to 0.
            - newline (bool): Adds a newline to the end of the output. Defaults to False.

        Returns:
            - str: S-Expression of this object
        """
        return maybe_to_sexpr(
            [
                self._sexpr_inter_tuple(f.name, f.name in self.positional_args)
                for f in fields(self)
            ],
            name=self.sexpr_prefix,
            indent=indent,
            newline=newline,
        )
