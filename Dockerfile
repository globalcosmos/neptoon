# Stage 1 - builder
FROM python:3.12-slim-bookworm AS builder
WORKDIR /build
RUN apt-get update \
    && apt-get install -y --no-install-recommends python3-tk \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY neptoon/ ./neptoon
RUN pip wheel . -w /wheels --no-cache-dir


# Stage 2
FROM python:3.12-slim-bookworm
WORKDIR /neptoon

COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/neptoon-*.whl
RUN rm -rf /root/.cache /usr/local/lib/python*/**/__pycache__

## WIP - for version numbering
ARG PACKAGE_VERSION=0.0.0
LABEL version="${PACKAGE_VERSION}"


ENTRYPOINT [ "neptoon" ]
CMD ["--help"]