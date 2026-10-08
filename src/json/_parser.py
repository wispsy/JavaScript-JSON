"""Decode and encode JSON with attribute access for object properties."""

from __future__ import annotations

import json as _json
from typing import Any, BinaryIO, Never, TextIO


def _is_special_attribute(name: str) -> bool:
    return name.startswith("__") and name.endswith("__")


class JSONObject(dict[str, Any]):
    """A dictionary whose JSON keys also support attribute access.

    JSON keys take precedence over ordinary dictionary attributes. Special
    Python attributes keep their normal meaning; use brackets for those keys.
    Attribute assignment and deletion operate on the dictionary itself.
    """

    __slots__ = ()

    def __getattribute__(self, name: str) -> Any:
        if not _is_special_attribute(name) and dict.__contains__(self, name):
            return dict.__getitem__(self, name)
        return dict.__getattribute__(self, name)

    def __setattr__(self, name: str, value: Any) -> None:
        if _is_special_attribute(name):
            raise AttributeError(f"Use brackets to assign JSON key {name!r}")
        dict.__setitem__(self, name, value)

    def __delattr__(self, name: str) -> None:
        if _is_special_attribute(name):
            raise AttributeError(f"Use brackets to delete JSON key {name!r}")
        try:
            dict.__delitem__(self, name)
        except KeyError:
            raise AttributeError(f"No JSON key named {name!r}") from None


type JSONValue = JSONObject | list[JSONValue] | str | int | float | bool | None


def _reject_constant(value: str) -> Never:
    raise ValueError(f"{value} is not a valid JSON numeric constant")


def parse(source: str | bytes | bytearray) -> JSONValue:
    """Parse JSON text, converting every object to a :class:`JSONObject`.

    Arrays remain lists; strings, numbers, booleans, and null become native
    Python values. Syntax errors raise ``json.JSONDecodeError``. Nonstandard
    constants such as ``NaN`` and ``Infinity`` raise ``ValueError``.
    """
    return _json.loads(
        source,
        object_hook=JSONObject,
        parse_constant=_reject_constant,
    )


loads = parse


def load(source: TextIO | BinaryIO) -> JSONValue:
    """Read and parse a JSON document from an open text or binary file."""
    return parse(source.read())


def _plain_containers(value: object, memo: dict[int, Any]) -> Any:
    """Remove attribute access without losing shared or circular references."""
    if isinstance(value, (dict, list, tuple)):
        identity = id(value)
        if identity in memo:
            return memo[identity]
        if isinstance(value, dict):
            result: dict[Any, Any] = {}
            memo[identity] = result
            for key, child in dict.items(value):
                result[key] = _plain_containers(child, memo)
            return result
        sequence: list[Any] = []
        memo[identity] = sequence
        sequence.extend(_plain_containers(child, memo) for child in value)
        return sequence
    return value


def stringify(
    value: object,
    *,
    indent: int | str | None = None,
    ensure_ascii: bool = True,
) -> str:
    """Serialize JSON-compatible values, including keys that shadow methods."""
    return _json.dumps(
        _plain_containers(value, {}),
        indent=indent,
        ensure_ascii=ensure_ascii,
        allow_nan=False,
    )


dumps = stringify
