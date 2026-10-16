# JavaScript-JSON

Parse JSON in Python and traverse its objects with JavaScript-style dot access:

```python
import JSON

obj = JSON.parse('[{"key": {"value": "hello"}}]')

assert obj[0].key.value == "hello"
assert obj[0]["key"]["value"] == "hello"
```

Requires Python 3.14 or later and has no runtime dependencies. The import name is
uppercase `JSON`; Python's lowercase `json` remains available. The distribution
name is `JavaScript-JSON`.

## Install

```sh
python -m pip install JavaScript-JSON
```

The Python import remains `import JSON`.

## Installation and tests

From the project directory:

```sh
uv sync
uv run python -m unittest discover -s tests -v
uv build
```

Alternatively, install with `python -m pip install -e .` and run
`python -m unittest discover -s tests -v` in that environment.

## How it works

`parse()` uses Python's standard `json` decoder with an object hook. Every JSON
object, including objects nested inside arrays, becomes a `JSONObject`, which is
a `dict` subclass. Arrays remain ordinary lists and scalar values remain native
Python values.

```python
data = JSON.loads('''{
    "users": [
        {"name": "Ada", "profile": {"active": true}},
        {"name": "Lin", "profile": {"active": false}}
    ],
    "next": null
}''')

assert data.users[0].profile.active is True
assert data.next is None
assert [user.name for user in data.users] == ["Ada", "Lin"]
assert len(data.users) == 2
```

| JSON value | Python value |
| --- | --- |
| Object | `JSONObject` (`dict` subclass) |
| Array | `list` |
| String | `str` |
| Integer / fractional number | `int` / `float` |
| `true` / `false` | `True` / `False` |
| `null` | `None` |

This provides JavaScript-style object traversal within Python. Use Python's
`len()`, loops, and list operations; indices, slicing, and negative indices follow
Python's rules. Top-level arrays and scalar JSON documents are supported too.

## Keys, dictionary methods, and mutation

Use brackets for keys containing spaces or punctuation, Python keywords, and
special Python attribute names such as `__class__`:

```python
data = JSON.parse('''{
    "display-name": "Ada",
    "class": "example",
    "items": [{"value": 7}],
    "__class__": "stored value"
}''')

assert data["display-name"] == "Ada"
assert data["class"] == "example"
assert data.items[0].value == 7
assert data["__class__"] == "stored value"
assert data.__class__ is JSON.JSONObject
```

JSON keys take precedence over ordinary dictionary attributes, so an `items` key
is available as `data.items`. Call dictionary methods through the class if a key
shadows them: `dict.items(data)`, `dict.keys(data)`, or `dict.get(data, "missing")`.
Otherwise the usual dictionary methods are available directly.

Attribute assignment and deletion update the dictionary:

```python
data = JSON.parse('{"profile": {"name": "Ada"}}')
data.profile.name = "Grace"
assert data["profile"]["name"] == "Grace"

data.profile.active = True
del data.profile.active
assert "active" not in data.profile
```

Values added after parsing retain their Python types. Inserting a plain `dict`
does not convert it to a `JSONObject`; use brackets to traverse it, or parse the
new JSON value before inserting it. Special Python attributes are protected from
attribute assignment and deletion; their JSON keys can still be changed through
brackets.

## API and errors

| Function | Behavior |
| --- | --- |
| `JSON.parse(text)` | Parse `str`, `bytes`, or `bytearray` JSON input. |
| `JSON.loads(text)` | Alias for `parse()`. |
| `JSON.load(file)` | Read and parse an open text or binary file. |
| `JSON.stringify(value, *, indent=None, ensure_ascii=True)` | Serialize parsed objects or ordinary JSON-compatible Python values. |
| `JSON.dumps(value, **options)` | Alias for `stringify()` with the same supported options. |

```python
with open("example.json", encoding="utf-8") as source:
    data = JSON.load(source)

text = JSON.stringify(data, indent=2, ensure_ascii=False)
assert JSON.parse(text) == data
```

Missing dot attributes raise `AttributeError`; missing bracket keys raise
`KeyError`. Array indices out of range raise `IndexError`. Names inherited from
`dict` still resolve to dictionary attributes when there is no matching JSON key.
Malformed JSON raises `JSON.JSONDecodeError` (the same exception class as
`json.JSONDecodeError`). `NaN`, `Infinity`, and `-Infinity` are rejected with
`ValueError`. Invalid input types raise `TypeError`.

Serialization follows `json.dumps` formatting and Unicode escaping, rejects
non-finite numbers with `ValueError`, and rejects unsupported Python objects
with `TypeError`. Use `JSON.stringify()` or `JSON.dumps()` to serialize parsed
objects: they convert containers to plain dictionaries and lists before
encoding, so JSON keys such as `items` do not interfere with the encoder.
