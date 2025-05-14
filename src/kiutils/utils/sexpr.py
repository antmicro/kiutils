#!/usr/bin/env python
# code extracted from: http://rosettacode.org/wiki/S-Expressions
# Originally taken from: https://gitlab.com/kicad/libraries/kicad-library-utils/-/blob/master/common/sexpr.py

import re
from typing import (
    List,
    Any,
    Union,
    Dict,
    Tuple,
    ClassVar,
    Self,
    Optional,
    get_args,
    get_origin,
    get_type_hints as tp_get_type_hints,
)
from dataclasses import fields, Field
from functools import lru_cache

dbg = False
PFIELD = "sexpr_prefix"

term_regex = r"""(?mx)
    \s*(?:
        (?P<brackl>\()|
        (?P<brackr>\))|
        (?P<num>[+-]?\d+\.\d+(?=[\ \)])|\-?\d+(?=[\ \)]))|
        (?P<sq>"(?:[^"]|(?<=\\)")*"(?:(?=\))|(?=\s)))|
        (?P<s>[^(^)\s]+)
       )"""

@lru_cache(maxsize=256)
def get_type_hints(cls) -> Dict[str, Any]:
    return tp_get_type_hints(cls)

def parse_sexp(sexp):
    stack = []
    out = []
    if dbg:
        print("%-6s %-14s %-44s %-s" % tuple("term value out stack".split()))
    for termtypes in re.finditer(term_regex, sexp):
        term, value = [(t, v) for t, v in termtypes.groupdict().items() if v][0]
        if dbg:
            print("%-7s %-14s %-44r %-r" % (term, value, out, stack))
        if term == "brackl":
            stack.append(out)
            out = []
        elif term == "brackr":
            assert stack, "Trouble with nesting of brackets"
            tmpout, out = out, stack.pop(-1)
            out.append(tmpout)
        elif term == "num":
            v = float(value)
            if v.is_integer():
                v = int(v)
            out.append(v)
        elif term == "sq":
            out.append(value[1:-1].replace(r"\"", '"'))
        elif term == "s":
            out.append(value)
        else:
            raise NotImplementedError("Error: %r" % (term, value))
    assert not stack, "Trouble with nesting of brackets"
    return out[0]


def parse_bool(arr: List[str] | str) -> bool:
    # KiCad8 syntax uses `(key "yes")`, but KiCad7 may use `(key "true")` or `key`
    if isinstance(arr, str) or len(arr) == 1 or arr[1] == "yes" or arr[1] == "true":
        return True
    else:
        return False


def val_to_str(val: Any, typ=None) -> str:
    if hasattr(typ, "to_sexpr"):
        if isinstance(val, list):
            return typ.to_sexpr(val)
        else:
            return typ(**val.__dict__).to_sexpr()
    if hasattr(val, "to_sexpr"):
        return val.to_sexpr()
    if (
        typ
        and val is not None
        and get_origin(typ) is Union
        and type(None) in get_args(typ)
    ):
        # Optional[..]
        return val_to_str(val, [i for i in get_args(typ) if not type(None) == i][0])
    if isinstance(val, bool):
        if val:
            return "yes"
        else:
            return "no"

    if isinstance(val, list):
        ret = ""
        t = get_args(typ)[0] if typ else None
        for elem in val:
            ret += maybe_to_sexpr(elem, typ=t)
        return ret
    if isinstance(val, dict):
        ret = ""
        for k, v in val.items():
            prefix = getattr(v, PFIELD)[0]
            if prefix:
                v.key = k
                ret += maybe_to_sexpr(v)
            else:
                ret += maybe_to_sexpr(v, k)
        return ret
    if isinstance(val, float):
        return f"{round(val,6):.6f}".rstrip("0").rstrip(".")
    if isinstance(val, (int, Rstr, bytes)) or typ == Rstr:
        return str(val)
    if isinstance(val, str):
        val = val.replace('"', '\\"')
        return f'"{val}"'

    return ""


def maybe_to_sexpr(val: Any, name: str = "", indent=1, newline=False, typ=None) -> str:
    if val is None:
        return ""

    if isinstance(val, tuple):
        if not isinstance(val[1], str):
            v = maybe_to_sexpr(val[0], typ=val[1])
        elif len(val) == 3:
            v = maybe_to_sexpr(val[0], val[1], typ=val[2])
        else:
            v = maybe_to_sexpr(val[0], val[1])

    else:
        v = val_to_str(val, typ)

    if v == "":
        return ""

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
    obj: Any
    if hasattr(cls, "from_sexpr"):
        return cls.from_sexpr(full_exp)
    if get_origin(cls) == list:
        obj = []
        for i in exp:
            obj.append(from_sexpr(get_args(cls)[0], i, False))
        return obj
    if get_origin(cls) == dict:
        obj = {}
        for i in exp:
            obj[exp[0]] = from_sexpr(get_args(cls)[1], i, False)
        return obj
    if get_origin(cls) is Union and type(None) in get_args(cls):
        # Optional[..]
        return from_sexpr(
            [i for i in get_args(cls) if not type(None) == i][0], full_exp
        )
    if cls == str:
        obj = ""
        for i in exp:
            obj = obj + str(i)
        return obj
    if cls == Rstr:
        obj = Rstr("")
        if isinstance(exp, list):
            for i in exp:
                obj = Rstr(obj + str(i) + "\n")
        else:
            obj = Rstr(exp)
        return obj
    if cls == int or cls == float:
        return cls(exp[0] if isinstance(exp, list) else exp)
    if cls == bool:
        return parse_bool(full_exp)


class SexprAuto:
    """Class that automatically implements Sexpr Ser/Deser for dataclass."""

    sexpr_prefix: ClassVar[List[str]] = []
    positional_args: ClassVar[List[str]] = []
    sexpr_case_convert: ClassVar[Optional[str]] = None

    @classmethod
    def _get_sexpr_name(cls, field: Field) -> str:
        name = field.name
        match field.metadata.get("case", cls.sexpr_case_convert):
            case "lower":
                name = name.lower()
            case "snake":
                name = re.sub(r"([A-Z][a-z])", r"_\1", name).lower()
        return field.metadata.get("alias", name)

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
        types = get_type_hints(cls)
        flags = [
            f.name
            for f in fields(obj)
            if types[f.name] == Optional[bool] or types[f.name] == bool
        ]
        for item in exp[1:]:
            if not isinstance(item, list) and positional_idx < len(obj.positional_args):
                fname = obj.positional_args[positional_idx]
                f = getattr(obj, fname)
                setattr(obj, fname, from_sexpr(type(f), item, False))
                positional_idx += 1
                continue
            if isinstance(item, str) and item in flags:
                setattr(obj, item, True)
                continue
            for f in fields(obj):
                ser_name = cls._get_sexpr_name(f)

                fval = getattr(obj, f.name)
                ftype = types[f.name]

                if f.metadata.get("flatten", False):
                    otype = get_origin(ftype)
                    itypes = get_args(ftype)
                    if otype == list and item[0] in getattr(itypes[0], PFIELD, []):
                        fval.append(from_sexpr(itypes[0], item))
                        setattr(obj, f.name, fval)
                        break
                    if otype == dict and item[0] in getattr(itypes[1], PFIELD, []):
                        fval[item[1]] = from_sexpr(itypes[1], item)
                        setattr(obj, f.name, fval)
                        break
                elif item[0] == ser_name or item[0] in getattr(fval, PFIELD, []):
                    setattr(obj, f.name, from_sexpr(ftype, item))
                    break
                elif (
                    get_origin(ftype) is Union
                    and type(None) in get_args(ftype)
                    and item[0]
                    in getattr(
                        [i for i in get_args(ftype) if not type(None) == i][0],
                        PFIELD,
                        [],
                    )
                ):
                    setattr(obj, f.name, from_sexpr(ftype, item))
                    break

        return obj

    def _sexpr_inter_tuple(
        self, f: Field, no_name: bool
    ) -> Union[Rstr, Tuple[Any, Any], Tuple[Any, str, Any]]:
        val = getattr(self, f.name)
        types = get_type_hints(self.__class__)
        val_type = types[f.name]
        ser_name = self._get_sexpr_name(f)
        if (
            f.metadata.get("force_empty", False)
            and isinstance(val, list)
            and len(val) == 0
        ):
            return Rstr(f"({ser_name})")

        precision = f.metadata.get("precision", None)
        if precision and isinstance(val, float):
            val = Rstr(f"{val:.{precision}f}")
            val_type = Rstr

        if (
            hasattr(val, "to_sexpr")
            or hasattr(val_type, "to_sexpr")
            or no_name
            or f.metadata.get("flatten", False)
        ):
            return (val, val_type)
        return (val, ser_name, val_type)

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
                self._sexpr_inter_tuple(f, f.name in self.positional_args)
                for f in fields(self)
            ],
            name=self.sexpr_prefix[0],
            indent=indent,
            newline=newline,
        )
