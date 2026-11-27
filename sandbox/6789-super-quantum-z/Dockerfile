FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt requirements-quantum.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-quantum.txt
COPY sqz ./sqz
RUN useradd -r -u 10001 sqz && mkdir -p /data && chown sqz /data
USER sqz
ENV SQZ_DB_PATH=/data/sqz.db SQZ_WORKER=1 SQZ_SELFTEST_INTERVAL_S=300
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python -c "import urllib.request,sys;sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health/ready').status==200 else 1)"
CMD ["uvicorn", "sqz.api:app_from_env", "--factory", "--host", "0.0.0.0", "--port", "8000"]
