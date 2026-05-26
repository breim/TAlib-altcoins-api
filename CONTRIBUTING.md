# Contributing

## Local setup

```bash
# install ta-lib C library (macOS)
brew install ta-lib

# or on Debian/Ubuntu, build from the vendored tarball as in the Dockerfile

# install uv (https://docs.astral.sh/uv/) then:
uv sync --all-extras
uv run pre-commit install
```

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

CI runs all of the above plus a multi-arch Docker build.

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
