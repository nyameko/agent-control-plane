"""One fixed, bounded, read-only tool; neither caller nor LLM supplies PromQL."""

import json
import math
from datetime import UTC, datetime

import httpx

QUERY = 'sum by (condition) (kube_pod_status_ready{namespace="quantum-platform"})'
MAX_BYTES = 65536


class DiagnosticFailure(Exception):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def pod_readiness(base_url, *, transport=None):
    try:
        with httpx.Client(
            timeout=8,
            follow_redirects=False,
            trust_env=False,
            transport=transport,
        ) as client:
            with client.stream(
                "GET",
                base_url + "/api/v1/query",
                params={"query": QUERY, "timeout": "5s"},
                headers={"Accept": "application/json"},
            ) as response:
                if response.status_code != 200:
                    raise DiagnosticFailure("prometheus_unavailable")
                body = bytearray()
                for chunk in response.iter_bytes(chunk_size=4096):
                    body.extend(chunk)
                    if len(body) > MAX_BYTES:
                        raise DiagnosticFailure("prometheus_response_too_large")
        payload = json.loads(body)
        if payload["status"] != "success" or payload["data"]["resultType"] != "vector":
            raise ValueError
        rows = payload["data"]["result"]
        if not rows:
            raise DiagnosticFailure("diagnostic_no_data")
        if len(rows) > 3:
            raise ValueError
        counts, sample_times = {}, []
        for row in rows:
            condition = row["metric"]["condition"]
            value = float(row["value"][1])
            timestamp = float(row["value"][0])
            if (
                condition not in {"true", "false", "unknown"}
                or condition in counts
                or not math.isfinite(value)
                or value < 0
                or not value.is_integer()
                or value > 10_000_000
                or not math.isfinite(timestamp)
            ):
                raise ValueError
            counts[condition] = int(value)
            sample_times.append(timestamp)
        return {
            "tool": "quantum-platform-pod-readiness",
            "namespace": "quantum-platform",
            "query": QUERY,
            "observed_at": datetime.now(UTC).isoformat(),
            "evaluation_timestamps": sample_times,
            "counts": counts,
            "limitation": "Ready counts only; does not measure app health or scrape freshness.",
        }
    except DiagnosticFailure:
        raise
    except httpx.HTTPError:
        raise DiagnosticFailure("prometheus_unavailable") from None
    except (ValueError, KeyError, TypeError, IndexError):
        raise DiagnosticFailure("prometheus_invalid_response") from None
