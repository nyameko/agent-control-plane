FROM python:3.12-slim AS builder

WORKDIR /build
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN python -m pip install --no-cache-dir --prefix=/install .

FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN addgroup --system --gid 10001 agentcp && adduser --system --ingroup agentcp --uid 10001 agentcp
COPY --from=builder /install /usr/local

USER 10001:10001
EXPOSE 8080

ENTRYPOINT ["uvicorn", "agent_control_plane.api:app"]
CMD ["--host", "0.0.0.0", "--port", "8080", "--proxy-headers"]
