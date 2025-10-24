FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
 POETRY_VERSION=1.4.2 \
 HATCHET_ENV=production
 
# Install system dependencies and Poetry
RUN apt-get update && \
 apt-get install -y curl && \
 curl -sSL https://install.python-poetry.org | python3 - && \
 ln -s /root/.local/bin/poetry /usr/local/bin/poetry && \
 apt-get clean && \
 rm -rf /var/lib/apt/lists/\*

 RUN python -m pip install --upgrade pip setuptools wheel
 
WORKDIR /app
 
COPY pyproject.toml poetry.lock\* /app/

# Copy the driver-db package first
COPY driver_db /driver_db
COPY packages /packages
COPY content_services/auto_toml /auto_toml
 
RUN poetry config virtualenvs.create false && \
 poetry install --no-interaction --no-ansi
 
COPY content_services/hatchet_worker/src /app

COPY content_services/hatchet_worker/start.sh /start.sh
RUN chmod +x /start.sh

# Copy the setEnv.sh if using the deployment repo
COPY setEnv.sh* / 

# Capture Git info at build time
ARG GIT_COMMIT
ARG GIT_BRANCH

# Set environment variables
ENV GIT_COMMIT=${GIT_COMMIT}
ENV GIT_BRANCH=${GIT_BRANCH}

CMD [ "/bin/sh", "-c", "/start.sh" ]
