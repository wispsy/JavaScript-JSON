"""Parse JSON into dictionaries with JavaScript-style attribute access."""

from json import JSONDecodeError

from ._parser import JSONObject, JSONValue, dumps, load, loads, parse, stringify

__all__ = [
    "JSONDecodeError",
    "JSONObject",
    "JSONValue",
    "dumps",
    "load",
    "loads",
    "parse",
    "stringify",
]
