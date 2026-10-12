# Self-hosted webhook service: docker build -t ci-triage . && docker run -p 8080:8080 --env-file ci-triage.env ci-triage
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY ci_triage ./ci_triage
RUN pip install --no-cache-dir . && useradd --create-home --uid 10001 citriage && mkdir -p /data && chown citriage /data
USER citriage
ENV CI_TRIAGE_AUDIT_LOG=/data/audit.jsonl CI_TRIAGE_STORE=/data/flaky.db
VOLUME ["/data"]
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/healthz')" || exit 1
CMD ["ci-triage", "serve", "--port", "8080"]
