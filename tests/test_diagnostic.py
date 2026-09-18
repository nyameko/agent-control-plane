import httpx
import pytest

from agent_control_plane.diagnostic import QUERY, DiagnosticFailure, pod_readiness


def response(rows):
    return {"status": "success", "data": {"resultType": "vector", "result": rows}}


def test_fixed_query_and_bounded_evidence():
    def handler(request):
        assert request.method == "GET"
        assert request.url.path == "/api/v1/query"
        assert request.url.params["query"] == QUERY
        return httpx.Response(
            200,
            json=response(
                [
                    {
                        "metric": {"condition": "true", "pod": "do not disclose"},
                        "value": [12345, "3"],
                    },
                    {"metric": {"condition": "false"}, "value": [12345, "1"]},
                ]
            ),
        )

    result = pod_readiness("http://prometheus", transport=httpx.MockTransport(handler))
    assert result["counts"] == {"true": 3, "false": 1}
    assert "do not disclose" not in str(result)


@pytest.mark.parametrize(
    "result,code",
    [
        (httpx.Response(302, headers={"Location": "http://unexpected"}), "prometheus_unavailable"),
        (httpx.Response(200, content=b"x" * 70000), "prometheus_response_too_large"),
        (httpx.Response(200, json=response([])), "diagnostic_no_data"),
        (
            httpx.Response(
                200,
                json=response(
                    [
                        {"metric": {"condition": "true"}, "value": [12345, "NaN"]},
                    ]
                ),
            ),
            "prometheus_invalid_response",
        ),
    ],
)
def test_upstream_failures_are_not_reported_as_healthy(result, code):
    with pytest.raises(DiagnosticFailure) as exc:
        pod_readiness("http://prometheus", transport=httpx.MockTransport(lambda _: result))
    assert exc.value.code == code
