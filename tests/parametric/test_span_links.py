import json
import pytest

from utils.parametric.spec.trace import ORIGIN
from utils.parametric.spec.trace import SAMPLING_PRIORITY_KEY
from utils.parametric.spec.trace import AUTO_DROP_KEY
from utils.parametric.spec.trace import span_has_no_parent
from utils.parametric.spec.tracecontext import TRACECONTEXT_FLAGS_SET
from utils import scenarios, missing_feature
from utils.parametric._library_client import Link


@scenarios.parametric
class Test_Span_Links:
    @staticmethod
    def _get_span_links(span):
        """Return the span links for the given span.
        This method is used to abstract the differences between the trace API v0.4 and v0.5.
        """
        if span.get("span_links"):
            # trace API v0.4
            return span["span_links"]

        encoded_span_links = span.get("meta", {}).get("_dd.span_links")
        if not encoded_span_links:
            # no span links found
            return None

        # trace API v0.5
        span_links = json.loads(encoded_span_links)
        # convert v0.5 span_link span ids and trace ids to the v0.4 format.
        # This will simplify tests and reduce duplication.
        for link in span_links:
            tid_high = int(link["trace_id"][:16], 16)
            if tid_high:
                link["trace_id_high"] = tid_high
            link["trace_id"] = int(link["trace_id"][16:], 16)
            link["span_id"] = int(link["span_id"], 16)
            # If set, the high bit (bit 31) should be set according the RFC
            link["flags"] = 0 if link.get("flags") is None else (link.get("flags") | TRACECONTEXT_FLAGS_SET)
        return span_links

    @pytest.mark.parametrize("library_env", [{"DD_TRACE_API_VERSION": "v0.4"}])
    def test_span_started_with_link_v04(self, test_agent, test_library):
        """Test adding a span link created from another span and serialized in the expected v0.4 format.
        This tests the functionality of "create a direct link between two spans
        given two valid span (or SpanContext) objects" as specified in the RFC.
        """
        with test_library:
            with test_library.start_span("root") as parent:
                with test_library.start_span(
                    "child",
                    parent_id=parent.span_id,
                    links=[Link(parent_id=parent.span_id, attributes={"foo": "bar", "array": ["a", "b", "c"]})],
                ):
                    pass

        traces = test_agent.wait_for_num_traces(1)
        assert len(traces[0]) == 2

        root = traces[0][0]
        span = traces[0][1]

        assert span["parent_id"] == root["span_id"]

        span_links = span["span_links"]
        assert len(span_links) == 1
        link = span_links[0]
        assert link["span_id"] == root["span_id"]
        assert link["trace_id"] == root["trace_id"]
        root_tid = root.get("meta", {}).get("_dd.p.tid", 0)
        assert (link.get("trace_id_high") or 0) == int(root_tid, 16)
        assert link["attributes"].get("foo") == "bar"
        assert link["attributes"].get("array.0") == "a"
        assert link["attributes"].get("array.1") == "b"
        assert link["attributes"].get("array.2") == "c"
        # Some languages do not set tracestate on all spans (ex: java, php)
        # If tracestate is set ensure the value is correct (ex: python)
        if link.get("tracestate"):
            assert link.get("tracestate") == "dd=s:1;t.dm:-0"
        assert link.get("flags", 0) == 1 | TRACECONTEXT_FLAGS_SET  # Sampled and Set (31 bit according the RFC)

    @pytest.mark.parametrize("library_env", [{"DD_TRACE_API_VERSION": "v0.5"}])
    def test_span_started_with_link_v05(self, test_agent, test_library):
        """Test adding a span link created from another span and serialized in the expected v0.5 format.
        This tests the functionality of "create a direct link between two spans
        given two valid span (or SpanContext) objects" as specified in the RFC.
        """
        with test_library:
            # create a span that will be sampled
            with test_library.start_span("root") as parent:
                with test_library.start_span(
                    "child",
                    parent_id=parent.span_id,
                    links=[Link(parent_id=parent.span_id, attributes={"foo": "bar", "array": ["a", "b", "c"]})],
                ):
                    pass

        traces = test_agent.wait_for_num_traces(1)
        assert len(traces[0]) == 2

        root = traces[0][0]
        span = traces[0][1]

        assert span["parent_id"] == root["span_id"]

        span_links = json.loads(span.get("meta", {}).get("_dd.span_links"))
        assert len(span_links) == 1
        link = span_links[0]
        root_tid = root.get("meta", {}).get("_dd.p.tid") or "0000000000000000"
        root_t64 = "{:016x}".format(span["trace_id"])
        assert link.get("trace_id") == f"{root_tid}{root_t64}"
        assert link.get("span_id") == "{:016x}".format(root["span_id"])
        assert link["attributes"].get("foo") == "bar"
        assert link["attributes"].get("array.0") == "a"
        assert link["attributes"].get("array.1") == "b"
        assert link["attributes"].get("array.2") == "c"
        # Some languages do not set tracestate on all spans (ex: java, php)
        # If tracestate is set ensure the value is correct
        if link.get("tracestate"):
            assert link.get("tracestate") == "dd=s:1;t.dm:-0"
        assert link.get("flags") == 1

    def test_span_link_from_distributed_datadog_headers(self, test_agent, test_library):
        """Properly inject datadog distributed tracing information into span links when trace_api is v0.4.
        Testing the conversion of x-datadog-* headers to tracestate for
        representation in span links.
        """
        with test_library:
            with test_library.start_span(
                "root",
                links=[
                    Link(
                        parent_id=0,
                        attributes={"foo": "bar"},
                        http_headers=[
                            ["x-datadog-trace-id", "1234567890"],
                            ["x-datadog-parent-id", "9876543210"],
                            ["x-datadog-sampling-priority", "2"],
                            ["x-datadog-origin", "synthetics"],
                            ["x-datadog-tags", "_dd.p.dm=-4,_dd.p.tid=0000000000000010"],
                        ],
                    )
                ],
            ):
                pass

        traces = test_agent.wait_for_num_traces(1)
        span = traces[0][0]
        assert span_has_no_parent(span) and span.get("trace_id") != 1234567890
        assert span["meta"].get(ORIGIN) is None

        span_links = self._get_span_links(span)
        assert len(span_links) == 1
        link = span_links[0]
        assert link.get("span_id") == 9876543210
        assert link.get("trace_id") == 1234567890
        assert link.get("trace_id_high") == 16

        assert link.get("tracestate") is not None
        tracestateArr = link["tracestate"].split(",")
        assert len(tracestateArr) == 1 and tracestateArr[0].startswith("dd=")
        tracestateDD = tracestateArr[0][3:].split(";")
        assert "o:synthetics" in tracestateDD
        assert "s:2" in tracestateDD
        assert "t.dm:-4" in tracestateDD

        # link has a sampling priority of 2, so it should be sampled
        assert link.get("flags", 1) == 1 | TRACECONTEXT_FLAGS_SET
        assert link["attributes"] == {"foo": "bar"}

    def test_span_link_from_distributed_w3c_headers(self, test_agent, test_library):
        """Properly inject w3c distributed tracing information into span links.
        This mostly tests that the injected tracestate and flags are accurate.
        """
        with test_library:
            with test_library.start_span(
                "root",
                links=[
                    Link(
                        parent_id=0,
                        http_headers=[
                            ["traceparent", "00-12345678901234567890123456789012-1234567890123456-01"],
                            ["tracestate", "foo=1,dd=t.dm:-4;s:2,bar=baz"],
                        ],
                    ),
                ],
            ):
                pass

        traces = test_agent.wait_for_num_traces(1)
        span = traces[0][0]
        assert span_has_no_parent(span) and span.get("trace_id") != 1234567890

        span_links = self._get_span_links(span)
        assert len(span_links) == 1
        link = span_links[0]
        assert link.get("span_id") == 1311768467284833366
        assert link.get("trace_id") == 8687463697196027922
        assert link.get("trace_id_high") == 1311768467284833366

        assert link.get("tracestate") is not None
        tracestateArr = link["tracestate"].split(",")
        dd_num = 0 if tracestateArr[0].startswith("dd=") else 1
        other_num = 0 if dd_num == 1 else 1
        assert tracestateArr[other_num] == "foo=1"
        assert tracestateArr[2] == "bar=baz"
        tracestateDD = tracestateArr[dd_num][3:].split(";")
        assert len(tracestateDD) == 2
        assert "s:2" in tracestateDD
        assert "t.dm:-4" in tracestateDD

        # link has a sampling priority of 2, so it should be sampled
        assert link.get("flags") == 1 | TRACECONTEXT_FLAGS_SET
        assert len(link.get("attributes") or {}) == 0

    def test_span_with_attached_links(self, test_agent, test_library):
        """Test adding a span link from a span to another span.
        """
        with test_library:
            with test_library.start_span("root") as parent:
                with test_library.start_span("first", parent_id=parent.span_id) as first:
                    pass
                with test_library.start_span(
                    "second", parent_id=parent.span_id, links=[Link(parent_id=parent.span_id)]
                ) as second:
                    second.add_link(first.span_id, attributes={"bools": [True, False], "nested": [1, 2]})

        traces = test_agent.wait_for_num_traces(1)
        assert len(traces[0]) == 3

        root = traces[0][0]
        root_tid = root["meta"].get("_dd.p.tid") or "0" if "meta" in root else "0"

        first = traces[0][1]
        span = traces[0][2]

        assert span.get("parent_id") == root.get("span_id")

        span_links = self._get_span_links(span)
        assert len(span_links) == 2

        link = span_links[0]
        assert link.get("span_id") == root.get("span_id")
        assert link.get("trace_id") == root.get("trace_id")
        assert (link.get("trace_id_high") or 0) == int(root_tid, 16)
        assert len(link.get("attributes") or {}) == 0

        link = span_links[1]
        assert link.get("span_id") == first.get("span_id")
        assert link.get("trace_id") == first.get("trace_id")
        assert (link.get("trace_id_high") or 0) == int(root_tid, 16)
        assert len(link.get("attributes")) == 4
        assert link["attributes"].get("bools.0") == "true"
        assert link["attributes"].get("bools.1") == "false"
        assert link["attributes"].get("nested.0") == "1"
        assert link["attributes"].get("nested.1") == "2"

    @missing_feature(library="python", reason="links do not influence the sampling decsion of spans")
    def test_span_link_propagated_sampling_decisions(self, test_agent, test_library):
        """Sampling decisions made by an upstream span should be propagated via span links to
        downstream spans.
        """
        with test_library:
            with test_library.start_span(
                "link_w_manual_keep",
                links=[
                    Link(
                        parent_id=0,
                        http_headers=[
                            ["x-datadog-trace-id", "666"],
                            ["x-datadog-parent-id", "777"],
                            ["x-datadog-sampling-priority", "2"],
                            ["x-datadog-tags", "_dd.p.dm=-0,_dd.p.tid=0000000000000010"],
                        ],
                    )
                ],
            ):
                pass

            with test_library.start_span(
                "link_w_manual_drop",
                links=[
                    Link(
                        parent_id=0,
                        http_headers=[
                            ["traceparent", "00-66645678901234567890123456789012-0000000000000011-01"],
                            ["tracestate", "foo=1,dd=t.dm:-3;s:-1,bar=baz"],
                        ],
                    )
                ],
            ):
                pass

            with test_library.start_span("auto_dropped_span") as ads:
                ads.set_meta(AUTO_DROP_KEY, "")

            with test_library.start_span("linked_to_auto_dropped_span", links=[Link(parent_id=ads.span_id)]):
                pass

        traces = test_agent.wait_for_num_traces(4)
        # Span Link generated from datadog headers containing manual keep
        link_w_manual_keep = traces[0][0]
        # assert that span link is set up correctly
        span_links = self._get_span_links(link_w_manual_keep)
        assert len(span_links) == 1 and span_links[0]["span_id"] == 777
        # assert that sampling decision is propagated by the span link
        assert link_w_manual_keep["meta"].get("_dd.p.dm") == "-0"
        assert link_w_manual_keep["metrics"].get(SAMPLING_PRIORITY_KEY) == 2

        # Span Link generated from tracecontext headers containing manual drop
        link_w_manual_drop = traces[1][0]
        # assert that span link is set up correctly
        span_links = self._get_span_links(link_w_manual_drop)
        assert len(span_links) == 1 and span_links[0]["span_id"] == 17
        # assert that sampling decision is propagated by the span link
        assert link_w_manual_drop["meta"].get("_dd.p.dm") == "-3"
        assert link_w_manual_drop["metrics"].get(SAMPLING_PRIORITY_KEY) == -1

        # Span Link generated between two root spans
        auto_dropped_span = traces[2][0]
        linked_to_auto_dropped_span = traces[3][0]
        # assert that span link is set up correctly
        span_links = self._get_span_links(linked_to_auto_dropped_span)
        assert len(span_links) == 1 and span_links[0]["span_id"] == auto_dropped_span["span_id"]
        # ensure autodropped span has the set sampling decision
        assert auto_dropped_span["metrics"].get(SAMPLING_PRIORITY_KEY) == 0
        # assert that sampling decision is propagated by the span link
        assert linked_to_auto_dropped_span["metrics"].get(SAMPLING_PRIORITY_KEY) == 0
