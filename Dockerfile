FROM --platform=linux/amd64 python:3.12-slim

WORKDIR /app/

RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry

# Configure Poetry to not create virtual environments
RUN poetry config virtualenvs.create false

# Copy the driver-db package first
COPY driver_db /driver_db
COPY packages /packages
COPY ./backend/app /app

# Copy pyproject.toml and poetry.lock first for better caching
COPY backend/pyproject.toml backend/poetry.lock /app/


ENV PYTHONPATH=/app

# Install dependencies
ARG INSTALL_DEV=false
RUN bash -c "if [ $INSTALL_DEV == 'true' ] ; then poetry install --no-root ; else poetry install --no-root --only main ; fi"

# Install start scripts
COPY backend/scripts/start-reload.sh /start-reload.sh
COPY backend/scripts/start.sh /start.sh
COPY backend/scripts/gunicorn_conf.py /gunicorn_conf.py
RUN chmod +x /start-reload.sh
RUN chmod +x /start.sh

# Copy the rest of the application
COPY backend/scripts/ /app/scripts/
COPY backend/prestart.sh /app/
COPY backend/tests-start.sh /app/
COPY backend/app /app/app

# # Install Node.js and Mermaid CLI --- FOR MERMAID CLI
# RUN apt-get update && apt-get install -y curl gnupg \
#     && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
#     && apt-get install -y nodejs \
#     # Debug: check node & npm
#     && node -v \
#     && npm -v \
#     # Now install Mermaid CLI
#     && npm install -g @mermaid-js/mermaid-cli

# # Aaaaand we need a headless browser to render the diagrams
# # Here's a list of dependencies that are required by puppeteer
# RUN apt-get update && apt-get install -y \
#     libglib2.0-0 \
#     libx11-6 \
#     libx11-xcb1 \
#     libxcomposite1 \
#     libxcursor1 \
#     libxdamage1 \
#     libxext6 \
#     libxi6 \
#     libxtst6 \
#     libnss3 \
#     libxrandr2 \
#     libatk1.0-0 \
#     libatk-bridge2.0-0 \
#     libpangocairo-1.0-0 \
#     libgtk-3-0 \
#     libdrm2 \
#     libgbm1 \
#     xdg-utils \
#     libasound2

RUN apt-get purge -y --auto-remove build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

CMD [ "/bin/sh", "-c", "if [ \"$INSTALL_DEV\" = 'true' ]; then exec /start-reload.sh \"$@\"; else exec /start.sh \"$@\"; fi" ]
