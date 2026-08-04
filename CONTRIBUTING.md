# Contributing

## Local setup

Install [uv](https://docs.astral.sh/uv/), then:

```bash
uv sync --all-extras
uv run pre-commit install
```

TA-Lib installs from a prebuilt wheel on macOS, Linux and Windows. Only if no wheel
matches your platform do you need the C library, built from the vendored tarball as
the Dockerfile does.

`pyproject.toml` carries a `[tool.uv] override-dependencies` block that lifts ccxt's
exact pins on `aiohttp` and `cryptography` to versions without known advisories. It
applies to `uv sync` and `uv.lock`, so install with uv rather than pip; the Docker
image is built from the lockfile for the same reason.

## Running the API

```bash
uv run talib-altcoins-api
# or with autoreload during development
RELOAD=true uv run talib-altcoins-api
```

Open `http://localhost:5001/docs` for the interactive OpenAPI UI.

## Quality gates

Before opening a PR:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest --cov
```

CI runs all of the above on Python 3.11 and 3.12, plus a dependency audit, a wheel and
sdist build, and a Docker build that boots the image and smoke tests its endpoints. The
multi-arch build runs only on release tags.

## Branches

- `master` is protected. Merge through pull requests only.
- Feature branches: `feat/<short-name>` or `fix/<short-name>`.

## Commits

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): subject

[optional body]
```

`type` is one of `feat`, `fix`, `docs`, `refactor`, `chore`, `test`, `style`, `perf`, `build`, `ci`. Subject is imperative, lowercase, no trailing period.

## Releases

Tag `vX.Y.Z` on `master` to trigger the publish workflow, which builds a multi-arch image and pushes it to GHCR.
