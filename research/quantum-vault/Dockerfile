FROM python:3.12.14-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f
WORKDIR /app
COPY sandbox-requirements.txt ./
RUN --mount=type=secret,id=pip_ca \
    if [ -r /run/secrets/pip_ca ]; then export PIP_CERT=/run/secrets/pip_ca; fi && \
    python -m pip install --no-cache-dir -r sandbox-requirements.txt
COPY super_quantum_z/ ./super_quantum_z/
COPY schema.json test_contract.py test_super_quantum_z.py ./
ENV PYTHONDONTWRITEBYTECODE=1
USER 65532:65532
CMD ["python", "-m", "pytest", "-p", "no:cacheprovider", "-q"]
