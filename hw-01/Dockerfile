FROM python:3.14-slim@sha256:a2b82f3c48559aa0a8446d9af49826b6e2b2016f4cd2afabfe6013ec53729170 AS tooling
COPY --from=ghcr.io/astral-sh/uv:0.12.11@sha256:79c6f4776b851471cc73b7d21d0cc834bb94383c292e83640d27eff512864df7 /uv /usr/local/bin/uv

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_LINK_MODE=copy \
    PYTHONPATH=/app/src \
    PATH="/app/.venv/bin:$PATH"
WORKDIR /app

FROM tooling AS checks
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-install-project
COPY src ./src
COPY tests ./tests
COPY schemas ./schemas
COPY data ./data
COPY config ./config
COPY prompts ./prompts

USER 10001:10001
CMD ["python", "-m", "hw01", "validate-gold"]
