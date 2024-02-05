import pytest

from ddapm_test_agent.trace import Span, root_span
from typing import Union
from utils import bug, missing_feature, irrelevant, context, scenarios
from utils.parametric.spec.otel_trace import SK_INTERNAL, OtelSpan
from utils.parametric.spec.trace import find_trace_by_root, find_span

# this global mark applies to all tests in this file.
#   DD_TRACE_OTEL_ENABLED=true is required in some tracers (.NET, Python?)
#   CORECLR_ENABLE_PROFILING=1 is required in .NET to enable auto-instrumentation
pytestmark = pytest.mark.parametrize(
    "library_env", [{"DD_TRACE_OTEL_ENABLED": "true", "CORECLR_ENABLE_PROFILING": "1"}],
)


@scenarios.parametric
class Test_Otel_Interoperability:
    def test_span_creation_using_otel(self, test_agent, test_library):
        """
            - A span created with the OTel API should be visible in the DD API
        """
        with test_library:
            with test_library.otel_start_span("otel_span") as otel_span:
                current_span = test_library.current_span()

                assert current_span is not None
                assert current_span.span_id == otel_span.span_id

                otel_span.end_span()

    def test_span_creation_using_datadog(self, test_agent, test_library):
        """
            - A span created with the DD API should be visible in the OTel API
        """
        with test_library:
            with test_library.start_span("dd_span") as dd_span:
                current_span = test_library.otel_current_span()

                assert current_span is not None
                assert current_span.span_id == dd_span.span_id

                dd_span.end_span()

    def test_has_ended(self, test_agent, test_library):
        """
            - Test that the ending status of a span is propagated across APIs
        """
        with test_library:
            with test_library.start_span("dd_span") as dd_span:
                current_span = test_library.otel_current_span()
                current_span.is_recording()

                has_ended = current_span.is_recording()
                assert has_ended is True

                dd_span.finish()

                has_ended = current_span.is_recording()
                assert has_ended is False

        traces = test_agent.wait_for_num_traces(1)
        trace = find_trace_by_root(traces, Span(name="dd_span"))
        assert len(trace) == 1

    def test_otel_start_after_datadog_span(self, test_agent, test_library):
        """
            - Start a span using the OTel API while a span created using the Datadog API already exists
        """
        with test_library:
            with test_library.start_span("dd_span") as dd_span:
                with test_library.otel_start_span(name="otel_span", span_kind=SK_INTERNAL, parent_id=dd_span.span_id) as otel_span:
                    current_span = test_library.current_span()
                    otel_context = otel_span.span_context()

                    assert current_span["trace_id"] == otel_context["trace_id"]
                    assert current_span["span_id"] == otel_context["span_id"]

                    assert dd_span["trace_id"] == current_span["trace_id"]
                    assert dd_span["span_id"] == current_span["parent_id"]

                    otel_span.end_span()
                dd_span.end_span()

        traces = test_agent.wait_for_num_traces(1)
        trace = find_trace_by_root(traces, Span(name="dd_span"))
        assert len(trace) == 2

        root = root_span(trace)
        span = find_span(trace, OtelSpan(resource="otel_span"))

        assert span.get("parent_id") == root.get("span_id")

    def test_datadog_start_after_otel_span(self, test_agent, test_library):
        """
            - Start a span using the Datadog API while a span created using the OTel API already exists
        """
        with test_library:
            with test_library.otel_start_span(name="otel_span", span_kind=SK_INTERNAL) as otel_span:
                with test_library.start_span(name="dd_span", parent_id=otel_span.span_id) as dd_span:
                    current_span = test_library.current_span()
                    otel_context = otel_span.span_context()

                    assert current_span["trace_id"] == otel_context["trace_id"]
                    assert current_span["span_id"] == otel_context["span_id"]

                    assert dd_span["trace_id"] == current_span["trace_id"]
                    assert dd_span["span_id"] == current_span["parent_id"]

                    dd_span.end_span()
                otel_span.end_span()

        traces = test_agent.wait_for_num_traces(1)
        trace = find_trace_by_root(traces, Span(name="dd_span"))
        assert len(trace) == 2

        root = root_span(trace)
        span = find_span(trace, OtelSpan(resource="otel_span"))

        assert span.get("parent_id") == root.get("span_id")

    def test_set_update_remove_meta(self, test_agent, test_library):
        """
            - Test that meta is set/updated/removed across APIs
        """
        with test_library:
            with test_library.start_span("dd_span") as dd_span:
                dd_span.set_meta("arg1", "val1")
                dd_span.set_meta("arg2", "val2")

                otel_span = test_library.otel_current_span()

                otel_span.set_attribute("arg3", "val3")
                otel_span.set_attribute("arg4", "val4")

                dd_span.set_meta("arg3", None)  # Remove the arg3/val3 pair (Created with the Otel API)
                assert dd_span.get_meta("arg3") is None
                assert otel_span.get_attribute("arg3") is None

                otel_span.set_attribute("arg1", None)  # Remove the arg1/val1 pair (Created with the DD API)
                assert dd_span.get_meta("arg1") is None
                assert otel_span.get_attribute("arg1") is None

                otel_span.set_attribute("arg2", "val3")  # Update the arg2/val2 pair (Created with the DD API)
                assert dd_span.get_meta("arg2") == "val3"
                assert otel_span.get_attribute("arg2") == "val3"

                dd_span.set_meta("arg4", "val5")  # Update the arg4/val4 pair (Created with the Otel API)
                assert dd_span.get_meta("arg4") == "val5"
                assert otel_span.get_attribute("arg4") == "val5"

                dd_span.finish()

                # The following calls should have no effect
                otel_span.set_attribute("arg5", "val5")  # Set a meta with the Otel API
                otel_span.set_attribute("arg2", "val4")  # Update the arg2/val2 pair (Created with the DD API)
                otel_span.set_attribute("arg2", None)  # Remove the arg2/val2 pair (Created with the DD API)

        traces = test_agent.wait_for_num_traces(1)
        trace = find_trace_by_root(traces, Span(name="dd_span"))
        assert len(trace) == 1

        dd_span = root_span(trace)
        meta = dd_span["meta"]

        # Span-life changes
        assert "arg1" not in meta
        assert meta["arg2"] == "val3"
        assert "arg3" not in meta
        assert meta["arg4"] == "val5"

        # Afterlife changes
        assert "arg5" not in meta

    def test_set_update_remove_metric(self, test_agent, test_library):
        """
            - Test that metrics are set/updated/removed across APIs
        """
        with test_library:
            with test_library.start_span("dd_span") as dd_span:
                dd_span.set_metric("m1", 1)  # Set a metric with the DD API
                dd_span.set_metric("m2", 2)

                otel_span = test_library.otel_current_span()

                otel_span.set_attribute("m3", 3)  # Set a metric with the Otel API
                otel_span.set_attribute("m4", 4)

                dd_span.set_metric("m3", None)  # Remove the m3/3 pair (Created with the Otel API)
                assert dd_span.get_metric("m3") is None
                assert otel_span.get_attribute("m3") is None

                otel_span.set_attribute("m1", None)  # Remove the m1/1 pair (Created with the DD API)
                assert dd_span.get_metric("m1") is None
                assert otel_span.get_attribute("m1") is None

                otel_span.set_attribute("m2", 3)  # Update the m2/2 pair (Created with the DD API)
                assert dd_span.get_metric("m2") == 3
                assert otel_span.get_attribute("m2") == 3

                dd_span.set_metric("m4", 5)  # Update the m4/4 pair (Created with the Otel API)
                assert dd_span.get_metric("m4") == 5
                assert otel_span.get_attribute("m4") == 5

                dd_span.finish()

                # The following calls should have no effect
                otel_span.set_attribute("m5", 5)  # Set a metric with the Otel API
                otel_span.set_attribute("m2", 4)  # Update the m2/2 pair (Created with the DD API)
                otel_span.set_attribute("m2", None)  # Remove the m2/2 pair (Created with the DD API)

        traces = test_agent.wait_for_num_traces(1)
        trace = find_trace_by_root(traces, Span(name="dd_span"))
        assert len(trace) == 1

        dd_span = root_span(trace)
        metrics = dd_span["metrics"]

        # Span-life changes
        assert "m1" not in metrics
        assert metrics["m2"] == 3
        assert "m3" not in metrics
        assert metrics["m4"] == 5

        # Afterlife changes
        assert "m5" not in metrics

    def test_update_resource(self, test_agent, test_library):
        """
            - Test that the resource is updated across APIs
        """
        with test_library:
            with test_library.otel_start_span("my_resource") as otel_span:
                dd_span = test_library.current_span()

                dd_span.set_resource("my_new_resource")
                assert dd_span.get_resource() == "my_new_resource"
                assert otel_span.get_resource() == "my_new_resource"

                otel_span.set_resource("my_new_resource2")
                assert dd_span.get_resource() == "my_new_resource2"
                assert otel_span.get_resource() == "my_new_resource2"

                dd_span.finish()

                otel_span.set_resource("my_new_resource3")
                assert dd_span.get_resource() == "my_new_resource2"
                assert otel_span.get_resource() == "my_new_resource2"

        traces = test_agent.wait_for_num_traces(1)
        trace = find_trace_by_root(traces, OtelSpan(resource="my_new_resource2"))
        assert len(trace) == 1

    def do_concurrent_traces_assertions(self, test_agent):
        traces = test_agent.wait_for_num_traces(2)
        trace1 = find_trace_by_root(traces, OtelSpan(resource="otel_root"))
        assert len(trace1) == 2
        trace2 = find_trace_by_root(traces, Span(name="dd_root"))
        assert len(trace2) == 2
        root1 = root_span(trace1)
        root2 = root_span(trace2)
        assert root1["resource"] == "otel_root"
        assert root2["name"] == "dd_root"
        child1 = find_span(trace1, OtelSpan(resource="otel_child"))
        child2 = find_span(trace2, Span(name="dd_child"))
        assert child1["resource"] == "otel_child"
        assert child2["name"] == "dd_child"
        assert child1["parent_id"] == root1["span_id"]
        assert child2["parent_id"] == root2["span_id"]
        assert root1["trace_id"] == child1["trace_id"]
        assert root2["trace_id"] == child2["trace_id"]
        assert root1["trace_id"] != root2["trace_id"]

    def test_concurrent_traces_in_order(self, test_agent, test_library):
        """
            - Basic concurrent traces and spans
        """
        with test_library:
            with test_library.otel_start_span("otel_root") as otel_root:
                with test_library.start_span(name="dd_child", parent_id=otel_root.span_id) as dd_child:
                    with test_library.start_span(name="dd_root", parent_id=0) as dd_root:
                        with test_library.otel_start_span(name="otel_child", parent_id=dd_root.span_id) as otel_child:
                            otel_child.finish()
                        dd_root.finish()
                    dd_child.finish()
                otel_root.finish()

        self.do_concurrent_traces_assertions(test_agent)

    def test_concurrent_traces_nested_otel_root(self, test_agent, test_library):
        """
            - Concurrent traces with nested start/end, with the first trace being opened with the OTel API
        """
        with test_library:
            with test_library.otel_start_span("otel_root") as otel_root:
                with test_library.start_span(name="dd_root", parent_id=0) as dd_root:
                    with test_library.otel_start_span(name="otel_child", parent_id=otel_root.span_id) as otel_child:
                        with test_library.start_span(name="dd_child", parent_id=dd_root.span_id) as dd_child:
                            otel_child.finish()

                            current_span = test_library.current_span()
                            assert current_span.span_id == dd_child.span_id
                        dd_child.finish()

                        current_span = test_library.current_span()
                        assert current_span.span_id == otel_root.span_id
                    dd_root.finish()

                    current_span = test_library.current_span()
                    assert current_span.span_id == otel_root.span_id
                otel_root.finish()

        self.do_concurrent_traces_assertions(test_agent)

    def test_concurrent_traces_nested_dd_root(self, test_agent, test_library):
        """
            - Concurrent traces with nested start/end, with the first trace being opened with the DD API
        """
        with test_library:
            with test_library.start_span(name="dd_root", parent_id=0) as dd_root:
                with test_library.otel_start_span("otel_root") as otel_root:
                    with test_library.otel_start_span(name="otel_child", parent_id=otel_root.span_id) as otel_child:
                        with test_library.start_span(name="dd_child", parent_id=dd_root.span_id) as dd_child:
                            otel_child.finish()

                            current_span = test_library.current_span()
                            assert current_span.span_id == dd_child.span_id
                        dd_child.finish()

                        current_span = test_library.current_span()
                        assert current_span.span_id == otel_root.span_id
                    dd_root.finish()

                    current_span = test_library.current_span()
                    assert current_span.span_id == otel_root.span_id
                otel_root.finish()

        self.do_concurrent_traces_assertions(test_agent)

