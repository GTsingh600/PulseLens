"""Render `client/src/shared/types.ts` from the pydantic models in `models.py`.

Pure function: `render()` returns the file text. `scripts/gen_types.py` writes it and
`tests/test_types_sync.py` checks the committed file matches.
"""

from __future__ import annotations

import types
import typing
from typing import Any, Literal, get_args, get_origin

from pydantic import BaseModel

from pulselens import models

HEADER = """\
// GENERATED FILE: do not edit by hand.
// Source: server/pulselens/models.py. Regenerate with `make types`.
// Client times are performance.now() ms on the one client clock (CLAUDE.md rule 1).
"""


def _literal_aliases() -> dict[Any, str]:
    """Module-level `Name = Literal[...]` aliases in models.py, keyed by the Literal object."""
    out: dict[Any, str] = {}
    for name, value in vars(models).items():
        if not name.startswith("_") and get_origin(value) is Literal:
            out[value] = name
    return out


def _literal_union(values: tuple[Any, ...]) -> str:
    parts = []
    for v in values:
        if isinstance(v, bool):
            parts.append("true" if v else "false")
        elif isinstance(v, str):
            parts.append('"' + v.replace('"', '\\"') + '"')
        else:
            parts.append(str(v))
    return " | ".join(parts)


def ts_type(tp: Any, aliases: dict[Any, str]) -> str:
    if tp in aliases:
        return aliases[tp]
    if tp is type(None) or tp is None:
        return "null"
    if tp is str:
        return "string"
    if tp is bool:
        return "boolean"
    if tp in (int, float):
        return "number"
    if tp is Any:
        return "unknown"
    if isinstance(tp, type) and issubclass(tp, BaseModel):
        return tp.__name__
    origin = get_origin(tp)
    args = get_args(tp)
    if origin is Literal:
        return _literal_union(args)
    if origin in (typing.Union, types.UnionType):
        return " | ".join(ts_type(a, aliases) for a in args)
    if origin is list:
        inner = ts_type(args[0], aliases) if args else "unknown"
        return f"({inner})[]" if " | " in inner else f"{inner}[]"
    if origin is dict:
        value = ts_type(args[1], aliases) if len(args) == 2 else "unknown"
        return f"Record<string, {value}>"
    raise TypeError(f"tsgen: unsupported type {tp!r}")


def render() -> str:
    aliases = _literal_aliases()
    lines = [HEADER]
    for lit, name in aliases.items():
        lines.append(f"export type {name} = {_literal_union(get_args(lit))};")
    lines.append("")
    for model in models.EXPORTED_MODELS:
        doc = (model.__doc__ or "").strip().splitlines()
        if doc and model.__doc__ is not BaseModel.__doc__:
            lines.append(f"/** {doc[0]} */")
        lines.append(f"export interface {model.__name__} {{")
        for fname, field in model.model_fields.items():
            optional = "" if field.is_required() else "?"
            lines.append(f"  {fname}{optional}: {ts_type(field.annotation, aliases)};")
        lines.append("}")
        lines.append("")
    return "\n".join(lines)
