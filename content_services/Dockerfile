# Stage 1: Build Rust native extension
FROM --platform=linux/amd64 python:3.12-slim AS rust-builder

RUN apt-get update && \
    apt-get install -y curl build-essential libssl-dev pkg-config patchelf libgit2-dev && \
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ENV PATH="/root/.cargo/bin:${PATH}"

RUN pip install maturin

WORKDIR /build
COPY content_services/native /build/native
RUN cd /build/native && maturin build --release


# Stage 2: Runtime image
FROM --platform=linux/amd64 python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    POETRY_VERSION=2.1.3 \
    HATCHET_ENV=production

# Install runtime dependencies only (no build tools)
# libgit2-1.9 is the runtime library for pygit2 and analytics_native
RUN apt-get update && \
    apt-get install -y curl nano ripgrep ghostscript git libgit2-1.9 && \
    curl -sSL https://install.python-poetry.org | python3 - && \
    ln -s /root/.local/bin/poetry /usr/local/bin/poetry && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN python -m pip install --upgrade pip setuptools wheel

WORKDIR /app

COPY driver_db /driver_db
COPY packages /packages
COPY content_services /app
COPY backend/scripts/ /app/scripts/
COPY content_services/src/inspector/uctags-2024.10.02-linux-x86_64/bin/ctags /ctags

RUN poetry config virtualenvs.create false && \
    poetry install --no-root --no-interaction --no-ansi

# Copy and install the pre-built Rust wheel from builder stage
COPY --from=rust-builder /build/native/target/wheels/*.whl /tmp/
RUN pip install /tmp/*.whl && rm -rf /tmp/*.whl

COPY content_services/start.sh /start.sh
RUN chmod +x /start.sh

# Copy the setEnv.sh if using the deployment repo
COPY setEnv.sh* /

# Install tiktoken encodings for single-tenant envs without internet access
RUN poetry run python -c "import tiktoken; tiktoken.encoding_for_model('gpt-4'); tiktoken.encoding_for_model('gpt-4.1')"

# Capture Git info at build time
ARG GIT_COMMIT
ARG GIT_BRANCH

# Set environment variables
ENV GIT_COMMIT=${GIT_COMMIT}
ENV GIT_BRANCH=${GIT_BRANCH}

CMD [ "/bin/sh", "-c", "/start.sh" ]
