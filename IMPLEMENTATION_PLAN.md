# Implementation plan

Provide `import JSON` and `JSON.parse(text)` so JSON objects support expressions
such as `obj[0].key.value`, with no runtime dependencies.

1. **Package and parser:** replace the placeholder package with the uppercase
   `JSON` package, configure the existing build backend, and use Python's standard
   `json` decoder. Convert every decoded object into a dictionary subclass that
   supports attribute access; retain ordinary lists and scalar values.
2. **Access and compatibility:** support bracket access for every key, prioritize
   JSON keys over ordinary dictionary attributes, preserve special Python
   attributes, and expose `loads`, `load`, `stringify`, and `dumps`. Keep missing
   attributes and keys distinguishable, and reject nonstandard numeric constants.
3. **Documentation:** describe installation, nested traversal, key collisions,
   mutation, errors, and the differences from JavaScript in `README.md`.
4. **Verification:** add standard-library `unittest` coverage under `tests/` for
   recursive traversal, scalars, arrays, key collisions, decoding failures, and
   serialization. Run the suite against the installed package, build a wheel,
   and verify that `import JSON` and `import json` work together.

Complete when the documented examples work, the test suite passes, and the built
package exposes the requested API. GitHub work is unavailable until this local
repository has a configured remote and an established task queue.

Completed: 33 tests pass against both the project installation and the wheel in
a clean environment. The source distribution and wheel build successfully;
all five Python examples in `README.md` pass against the installed wheel.
