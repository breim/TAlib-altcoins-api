# TA-Lib Altcoins API

A small FastAPI service that exposes [TA-Lib](https://ta-lib.org/) technical indicators over OHLCV data fetched from any exchange supported by [CCXT](https://github.com/ccxt/ccxt).

## Endpoints

| Path                       | Description                                         |
| -------------------------- | --------------------------------------------------- |
| `GET /indicators`          | Compute indicators for `exchange`, `symbol`, etc.   |
| `GET /healthz`             | Liveness probe.                                     |
| `GET /readyz`              | Readiness probe. The service is stateless, so this mirrors `/healthz`. |
| `GET /metrics`             | Prometheus metrics (disable with `METRICS_ENABLED=false`). |
| `GET /docs`                | Interactive OpenAPI (Swagger UI).                   |

### `GET /indicators`

| Query    | Required | Default | Description                                                   |
| -------- | -------- | ------- | ------------------------------------------------------------- |
| exchange | yes      |         | CCXT exchange id (lowercase, e.g. `binance`).                 |
| symbol   | yes      |         | Symbol in `BASE/QUOTE` form (e.g. `BTC/USDT`).                |
| interval | no       | `30m`   | One of `1m,3m,5m,15m,30m,1h,2h,4h,6h,8h,12h,1d,3d,1w,1M`.     |
| limit    | no       | `200`   | OHLCV bars to fetch, `50..1000`.                              |

```bash
curl 'http://localhost:5001/indicators?exchange=binance&symbol=BTC/USDT&interval=1h'
```

## Run with Docker

```bash
docker build -t talib-altcoins-api .
docker run --rm -p 5001:5001 talib-altcoins-api
# or
docker compose up --build
```

Pre-built images are published to `ghcr.io/<owner>/talib-altcoins-api:<version>` on each `vX.Y.Z` tag.

## Local development

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/). TA-Lib publishes prebuilt wheels for macOS, Linux and Windows, so no system library is needed on those platforms. Build the C library from the vendored tarball, as the Dockerfile does, only if no wheel matches your platform.

```bash
uv sync --all-extras
uv run pre-commit install

# run the API
uv run talib-altcoins-api

# checks
uv run ruff check .
uv run mypy src
uv run pytest --cov
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for branches, commits, and release process.

## Configuration

All settings come from environment variables (see [.env.example](.env.example)). Highlights:

| Variable             | Default      | Notes                                                       |
| -------------------- | ------------ | ----------------------------------------------------------- |
| `HOST`               | `0.0.0.0`    |                                                             |
| `PORT`               | `5001`       |                                                             |
| `WORKERS`            | `2`          | Ignored when `RELOAD=true`.                                 |
| `RELOAD`             | `false`      | Dev only.                                                   |
| `LOG_LEVEL`          | `INFO`       |                                                             |
| `LOG_JSON`           | `true`       | `false` for human-readable logs.                            |
| `CORS_ALLOW_ORIGINS` | (empty)      | Comma-separated; do not use `*` in production.              |
| `SENTRY_DSN`         | (empty)      | Enables Sentry when set.                                    |
| `METRICS_ENABLED`    | `true`       | Set `false` to stop serving `/metrics` publicly.            |
| `RATE_LIMIT`         | `60/minute`  | Per-IP, applies to `/indicators`.                           |
| `RATE_LIMIT_STORAGE_URI` | `memory://` | Per-process by default; use `redis://…` across workers.  |
| `FORWARDED_ALLOW_IPS`| `127.0.0.1`  | Proxies whose `X-Forwarded-For` is trusted for client IPs.  |
| `CACHE_TTL_SECONDS`  | `30`         | Response cache for `(exchange, symbol, interval, limit)`.   |
| `CCXT_TIMEOUT_MS`    | `10000`      | Per-request timeout to upstream exchange.                   |
| `CCXT_MAX_RETRIES`   | `3`          | Transient-error retries (exponential backoff).              |
| Indicator periods    | TA-Lib stds  | See `.env.example` for the full list.                       |

### Rate limiting behind a proxy

`RATE_LIMIT` is keyed on the client IP. With the default `memory://` storage each worker
keeps its own counter, so the effective limit is `RATE_LIMIT × WORKERS`; point
`RATE_LIMIT_STORAGE_URI` at Redis to share one budget. Behind a reverse proxy, set
`FORWARDED_ALLOW_IPS` to the proxy address so real client IPs are used instead of the
proxy's — otherwise every caller shares a single bucket.

## License

MIT. See [LICENSE](LICENSE).
