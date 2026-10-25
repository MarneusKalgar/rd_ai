# Shared tooling: immutable Python/uv images keep builds reproducible.
FROM python:3.14-slim@sha256:a2b82f3c48559aa0a8446d9af49826b6e2b2016f4cd2afabfe6013ec53729170 AS tooling
COPY --from=ghcr.io/astral-sh/uv:0.12.11@sha256:79c6f4776b851471cc73b7d21d0cc834bb94383c292e83640d27eff512864df7 /uv /usr/local/bin/uv

# Read-only containers avoid bytecode writes and flush logs immediately.
# Use the image's Python and a copied virtualenv; never download another interpreter.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_LINK_MODE=copy \
    PYTHONPATH=/app/src \
    PATH="/app/.venv/bin:$PATH"
WORKDIR /app

# Cache production dependencies independently of source/data changes.
# The src package is imported through PYTHONPATH, so no project install is needed.
FROM tooling AS dependencies
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

# Public HW artifacts only. The .dockerignore allowlist excludes credentials,
# private workbooks, preparation tooling, model weights and generated results.
FROM dependencies AS artifacts
COPY src ./src
COPY schemas ./schemas
COPY data ./data
COPY config ./config
COPY prompts ./prompts

# App/setup image: production dependencies only, with non-root results storage.
# A fresh named results volume inherits this directory's ownership.
FROM artifacts AS runtime
RUN mkdir /app/results \
    && chown 10001:10001 /app/results
USER 10001:10001
# Safe default: validate artifacts offline; model execution must be explicit.
CMD ["python", "-m", "extraction_service", "preflight"]

# Separate test-tool dependencies so Ruff/mypy/pytest do not enter the runtime.
FROM tooling AS check-dependencies
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-install-project

# Check image reuses the exact public runtime artifacts and adds tests.
# Compose disables its network and provides temporary writable storage.
FROM check-dependencies AS checks
COPY --from=artifacts /app/src ./src
COPY --from=artifacts /app/schemas ./schemas
COPY --from=artifacts /app/data ./data
COPY --from=artifacts /app/config ./config
COPY --from=artifacts /app/prompts ./prompts
COPY tests ./tests
USER 10001:10001
CMD ["python", "-m", "extraction_service", "validate-gold"]

# Initialize empty volume ownership without adding a shell to Garage's scratch image.
FROM tooling AS garage-directories
RUN mkdir -p /garage-state/meta /garage-state/data \
    && chown -R 10001:10001 /garage-state

# Optional local archive storage; independent of all model runtime services.
FROM dxflrs/garage@sha256:9c96caa2612d3411acc5b0e6701fb238dbfba33e533a6d7d3d811a4b12d0d020 AS archive-store
COPY --from=garage-directories --chown=10001:10001 /garage-state /var/lib/garage
USER 10001:10001
CMD ["/garage", "server", "--single-node", "--default-bucket"]
