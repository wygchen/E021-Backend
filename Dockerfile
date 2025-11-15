FROM python:3.11-slim

WORKDIR /app

# Install build deps and runtime deps
COPY pyproject.toml .
COPY pyproject.lock .  # optional - will be ignored if not present
RUN pip install --upgrade pip
RUN pip install "hatchling"
RUN pip install -e .

COPY . .

ENV PORT=8080
EXPOSE 8080

CMD [ "uvicorn", "frontend.api:app", "--host", "0.0.0.0", "--port", "8080" ]
