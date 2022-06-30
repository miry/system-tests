import os
from typing import Any
from typing import Optional

import pytest

from .conftest import _TestTracer
from .conftest import dotnet_library_server_factory
from .conftest import golang_library_server_factory
from .conftest import python_library_server_factory
from .trace import SPAN_MEASURED_KEY


parametrize = pytest.mark.parametrize
snapshot = pytest.mark.snapshot


def all_libs() -> Any:
    libs = {
        "python": python_library_server_factory,
        "dotnet": dotnet_library_server_factory,
        "golang": golang_library_server_factory,
    }
    enabled = []
    for lang in os.getenv("CLIENTS_ENABLED", "python,dotnet").split(","):
        enabled.append(libs[lang])
    return parametrize("apm_test_server_factory", enabled)


def enable_tracestats(sample_rate: Optional[float] = None) -> Any:
    env = {"DD_TRACE_COMPUTE_STATS": "1", "DD_TRACE_STATS_COMPUTATION_ENABLED": "1"}
    if sample_rate is not None:
        assert 0 <= sample_rate <= 1.0
        env.update(
            {
                "DD_TRACE_SAMPLE_RATE": str(sample_rate),
            }
        )
    return parametrize("apm_test_server_env", [env])


@all_libs()
@enable_tracestats()
def test_top_level_TS005(apm_test_server_env, apm_test_server_factory, test_agent, test_client):
    """
    When top level (service entry) spans are created
        Each top level span has trace stats computed for it.
    """
    # Create a top level span.
    with test_client.start_span(name="web.request", resource="/users", service="webserver") as span:
        # Create another top level (service entry) span as a child of the web.request span.
        with test_client.start_span(
            name="postgres.query", resource="SELECT 1", service="postgres", parent_id=span.span_id
        ):
            pass
    test_client.flush()

    requests = test_agent.v06_stats_requests()
    assert len(requests) == 1, "Only one stats request is expected"
    request = requests[0]["body"]
    for key in ("Hostname", "Env", "Version", "Stats"):
        assert key in request, "%r should be in stats request" % key

    buckets = request["Stats"]
    assert len(buckets) == 1, "There should be one bucket containing the stats"
    bucket = buckets[0]
    assert "Start" in bucket
    assert "Duration" in bucket
    assert "Stats" in bucket
    stats = bucket["Stats"]
    assert len(stats) == 2, "There should be two stats entries in the bucket"

    postgres_stats = [s for s in stats if s["Name"] == "postgres.query"][0]
    assert postgres_stats["Resource"] == "SELECT 1"
    assert postgres_stats["Service"] == "postgres"
    assert postgres_stats["Type"] is None  # FIXME: add span type
    assert postgres_stats["Hits"] == 1
    assert postgres_stats["TopLevelHits"] == 1
    assert postgres_stats["Duration"] > 0

    web_stats = [s for s in stats if s["Name"] == "web.request"][0]
    assert web_stats["Resource"] == "/users"
    assert web_stats["Service"] == "webserver"
    assert web_stats["Type"] is None  # FIXME: add span type
    assert web_stats["Hits"] == 1
    assert web_stats["TopLevelHits"] == 1
    assert web_stats["Duration"] > 0

@parametrize(
    "apm_test_server_factory",
    [
        python_library_server_factory,
        # go_library_server_factory,
    ],
)
@parametrize(
    "apm_test_server_env",
    [
        {
            "DD_TRACE_COMPUTE_STATS": "1",
        },
    ],
)
def test_client_tracestats_distinctkey_per_dimension(apm_test_server_env, apm_test_server_factory, test_agent, test_client):
    """
    When spans are created with a unique set of dimensions
        Each span has stats computed for it and is in its own bucket
        The dimensions are: { service, type, name, resource, HTTP_status_code, synthetics }
    """
    NAME="name"
    RESOURCE="resource"
    SERVICE="service"
    TYPE="type"
    HTTP_STATUS_CODE="200"
    ORIGIN=""

    # Baseline
    with test_client.start_span(name=NAME, resource=RESOURCE, service=SERVICE) as span:
        span.set_meta(key="http.status_code", val=HTTP_STATUS_CODE)

    # Unique Name
    with test_client.start_span(name="unique-name", resource=RESOURCE, service=SERVICE) as span:
        span.set_meta(key="http.status_code", val=HTTP_STATUS_CODE)

    # Unique Resource
    with test_client.start_span(name=NAME, resource="unique-resource", service=SERVICE) as span:
        span.set_meta(key="http.status_code", val=HTTP_STATUS_CODE)

    # Unique Service
    with test_client.start_span(name=NAME, resource=RESOURCE, service="unique-service") as span:
        span.set_meta(key="http.status_code", val=HTTP_STATUS_CODE)

    # Unique Type
    # Unique HTTP Status Code
    with test_client.start_span(name=NAME, resource=RESOURCE, service=SERVICE) as span:
        span.set_meta(key="http.status_code", val="400")

    # Unique Synthetics

    test_client.flush()

    requests = test_agent.v06_stats_requests()
    assert len(requests) == 1, "Only one stats request is expected"
    request = requests[0]["body"]
    for key in ("Hostname", "Env", "Version", "Stats"):
        assert key in request, "%r should be in stats request" % key

    buckets = request["Stats"]
    assert len(buckets) == 1, "There should be one bucket containing the stats"

    bucket = buckets[0]
    assert "Start" in bucket
    assert "Duration" in bucket
    assert "Stats" in bucket
    stats = bucket["Stats"]
    assert len(stats) == 5, "There should be two stats entries in the bucket"

    for s in stats:
        assert s["Hits"] == 1
        assert s["TopLevelHits"] == 1
        assert s["Duration"] > 0

@all_libs()
@enable_tracestats()
def test_measured_spans(apm_test_server_env, apm_test_server_factory, test_agent, test_client):
    """
    When spans are marked as measured
        Each has stats computed for it
    """
    with test_client.start_span(name="web.request", resource="/users", service="webserver") as span:
        # Use the same service so these spans are not top-level
        with test_client.start_span(name="child.op1", resource="", service="webserver", parent_id=span.span_id) as op1:
            op1.set_metric(SPAN_MEASURED_KEY, 1)
        with test_client.start_span(name="child.op2", resource="", service="webserver", parent_id=span.span_id) as op2:
            op2.set_metric(SPAN_MEASURED_KEY, 1)
        # Don't measure this one to ensure no stats are computed
        with test_client.start_span(name="child.op3", resource="", service="webserver", parent_id=span.span_id):
            pass
    test_client.flush()

    requests = test_agent.v06_stats_requests()
    stats = requests[0]["body"]["Stats"][0]["Stats"]
    assert len(stats) == 3

    web_stats = [s for s in stats if s["Name"] == "web.request"][0]
    assert web_stats["TopLevelHits"] == 1
    op1_stats = [s for s in stats if s["Name"] == "child.op1"][0]
    assert op1_stats["Hits"] == 1
    assert op1_stats["TopLevelHits"] == 0
    op2_stats = [s for s in stats if s["Name"] == "child.op2"][0]
    assert op2_stats["Hits"] == 1
    assert op2_stats["TopLevelHits"] == 0


@all_libs()
@enable_tracestats(sample_rate=0.0)
def test_sample_rate_0(apm_test_server_env, apm_test_server_factory, test_agent, test_client):
    """
    When the sample rate is 0 and trace stats is enabled
        non-P0 traces should be dropped
        trace stats should be produced
    """
    with test_client.start_span(name="web.request", resource="/users", service="webserver") as span:
        pass
    test_client.flush()

    traces = test_agent.traces()
    assert len(traces) == 0, "No traces should be emitted with the sample rate set to 0"
    requests = test_agent.v06_stats_requests()

    stats = requests[0]["body"]["Stats"][0]["Stats"]
    assert len(stats) == 1, "Only one stats aggregation is expected"
    web_stats = [s for s in stats if s["Name"] == "web.request"][0]
    assert web_stats["TopLevelHits"] == 1
    assert web_stats["Hits"] == 1


@snapshot(
    ignores=[
        "error",
        "type",
        "meta.language",
        "metrics.process_id",
        "metrics._dd.agent_psr",
        "metrics._dd.tracer_kr",
        "metrics._sampling_priority_v1",
    ],
    # Specify a custom token so all parameterizations use the same snapshots
    token="apm_client.test_client_stats.test_client_snapshot",
)
@all_libs()
def test_client_snapshot(apm_test_server_factory, test_agent, test_client: _TestTracer):
    """Ensure clients mostly submit the same data for a trace.

    Data which is inconsistent enough between clients is ignored
    with the snapshot `ignores` argument.
    """
    with test_client.start_span(name="web.request", resource="/users", service="webserver") as span:
        span.set_meta("key", "val")
        with test_client.start_span(
            name="postgres.query", resource="SELECT 1", service="postgres", parent_id=span.span_id
        ):
            pass
