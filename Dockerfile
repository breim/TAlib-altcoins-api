FROM python:3.14-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        file \
        wget \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

COPY ta-lib-0.4.0-src.tar.gz ./
RUN tar -xzf ta-lib-0.4.0-src.tar.gz \
    && cd ta-lib \
    && ./configure --prefix=/usr/local \
    && make \
    && make install \
    && cd .. \
    && rm -rf ta-lib ta-lib-0.4.0-src.tar.gz

COPY --from=ghcr.io/astral-sh/uv:0.11.16 /uv /usr/local/bin/uv

# Installing from the lockfile rather than `pip install .` keeps the image
# identical to the audited environment. pip cannot see [tool.uv]
# override-dependencies, so it would resolve ccxt's pinned aiohttp and
# cryptography and ship the versions those overrides exist to avoid.
ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    LD_LIBRARY_PATH="/usr/local/lib:${LD_LIBRARY_PATH}"

COPY pyproject.toml uv.lock README.md LICENSE ./
COPY src ./src
RUN uv sync --frozen --no-dev --no-editable


FROM python:3.14-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    LD_LIBRARY_PATH="/usr/local/lib:${LD_LIBRARY_PATH}" \
    PORT=5001 \
    HOST=0.0.0.0 \
    WORKERS=2

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system app \
    && useradd --system --gid app --home-dir /home/app --shell /usr/sbin/nologin app \
    && mkdir -p /home/app \
    && chown app:app /home/app

COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /usr/local/lib/libta_lib* /usr/local/lib/
RUN ldconfig

USER app
WORKDIR /home/app

EXPOSE 5001

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl --fail --silent --show-error "http://127.0.0.1:${PORT}/healthz" || exit 1

CMD ["talib-altcoins-api"]
