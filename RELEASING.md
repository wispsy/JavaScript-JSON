# Publishing JavaScript-JSON

The v0.1.0 distribution name is `JavaScript-JSON`; its Python import is `JSON`.
Requires Python 3.14 or later.

## One-time PyPI setup

At https://pypi.org/manage/account/publishing/ add a pending GitHub publisher:

| Field | Value |
| --- | --- |
| PyPI project name | `JavaScript-JSON` |
| Owner | `outside-labs` |
| Repository | `JavaScript-JSON` |
| Workflow filename | `release.yaml` |
| Environment | `pypi` |

For an existing project, add the same publisher under the project's Publishing
settings instead. Names must match the GitHub repository, workflow and environment
exactly. A pending publisher does not reserve the package name.

The GitHub repository uses an environment named `pypi`. No PyPI API token is needed.

## Release v0.1.0

1. Ensure CI passes on the intended commit and `pyproject.toml` has version `0.1.0`.
2. Create a GitHub release with tag `v0.1.0` targeting that commit and publish it.
3. Monitor the Release workflow. It checks the tag, builds an sdist and a wheel
   from that sdist, validates metadata, and tests the installed wheel before
   publishing through the `pypi` environment using OpenID Connect.
4. Verify installation with `python -m pip install JavaScript-JSON==0.1.0`.

Publishing a GitHub release triggers the upload; pushing a tag alone does not.
PyPI versions cannot be overwritten. Future releases must update the version
and lockfile, and use the corresponding `v`-prefixed tag.
