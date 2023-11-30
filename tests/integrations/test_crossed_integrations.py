import json

from utils import interfaces, scenarios, coverage, weblog, missing_feature
from utils._weblog import _Weblog
from utils.tools import logger


# TODO: move this class in utils
class _PythonBuddy(_Weblog):
    def __init__(self):
        from collections import defaultdict

        self.port = 9001
        self.domain = "localhost"

        self.responses = defaultdict(list)
        self.current_nodeid = "not used"
        self.replay = False


@scenarios.crossed_tracing_libraries
@coverage.basic
class Test_PythonKafka:
    """ Test kafka compatibility with datadog python tracer """

    WEBLOG_TO_BUDDY_TOPIC = "Test_PythonKafka_weblog_to_buddy"
    BUDDY_TO_WEBLOG_TOPIC = "Test_PythonKafka_buddy_to_weblog"

    @staticmethod
    def get_span(interface, span_kind, topic):

        logger.debug(f"Trying to find traces with span kind: {span_kind} and topic: {topic} in {interface}")

        for data, trace in interface.get_traces():
            for span in trace:
                if span_kind != span["meta"].get("span.kind"):
                    continue

                is_java_tracer = "java" in span["meta"]["component"]

                # dd-trace-java does not add kafka.topic to its kafka.produce spans
                if not is_java_tracer and topic != span["meta"].get("kafka.topic"):
                    continue

                # instead, we rely on resource
                if is_java_tracer and not span["resource"].endswith(topic):
                    continue
                if ("java" not in span["meta"]["component"] and topic != span["meta"].get("kafka.topic")) or (
                    "java" in span["meta"]["component"] and not span["resource"].endswith(topic)
                ):
                    continue

                logger.debug(f"span found in {data['log_filename']}:\n{json.dumps(span, indent=2)}")

                return span

        logger.debug("No span found")
        return None

    def setup_produce(self):
        """
            send request A to weblog : this request will produce a kafka message
            send request B to python buddy, this request will consume kafka message
        """

        python_buddy = _PythonBuddy()

        self.production_response = weblog.get("/kafka/produce", params={"topic": self.WEBLOG_TO_BUDDY_TOPIC})
        self.consume_response = python_buddy.get("/kafka/consume", params={"topic": self.WEBLOG_TO_BUDDY_TOPIC})

    def test_produce(self):
        """ Check that a message produced to kafka is correctly ingested by a Datadog python tracer"""

        assert self.production_response.status_code == 200
        # assert self.consume_response.status_code == 200

        # The weblog is the producer, the buddy is the consumer
        self.validate_kafka_spans(
            producer_interface=interfaces.library,
            consumer_interface=interfaces.python_buddy,
            topic=self.WEBLOG_TO_BUDDY_TOPIC,
        )

    @missing_feature(library="python")
    @missing_feature(library="java")
    def test_produce_trace_equality(self):
        """This test relies on the setup for produce, it currently cannot be run on its own"""
        producer_span = self.get_span(interfaces.library, span_kind="producer", topic=self.WEBLOG_TO_BUDDY_TOPIC)
        consumer_span = self.get_span(interfaces.python_buddy, span_kind="consumer", topic=self.WEBLOG_TO_BUDDY_TOPIC)

        # Both producer and consumer spans should be part of the same trace
        # Different tracers can handle the exact propagation differently, so for now, this test avoids
        # asserting on direct parent/child relationships
        assert producer_span["trace_id"] == consumer_span["trace_id"]

    def setup_consume(self):
        """
            send request A to python buddy : this request will produce a kafka message
            send request B to weblog, this request will consume kafka message

            request A: GET /python_buddy/produce_kafka_message
            request B: GET /weblog/consume_kafka_message 
        """
        python_buddy = _PythonBuddy()

        self.production_response = python_buddy.get("/kafka/produce", params={"topic": self.BUDDY_TO_WEBLOG_TOPIC})
        self.consume_response = weblog.get("/kafka/consume", params={"topic": self.BUDDY_TO_WEBLOG_TOPIC})

    def test_consume(self):
        """ Check that a message by an app instrumented by a Datadog python tracer is correctly ingested """

        assert self.production_response.status_code == 200
        assert self.consume_response.status_code == 200

        # The buddy is the producer, the weblog is the consumer
        self.validate_kafka_spans(
            producer_interface=interfaces.python_buddy,
            consumer_interface=interfaces.library,
            topic=self.BUDDY_TO_WEBLOG_TOPIC,
        )

    @missing_feature(library="python")
    @missing_feature(library="java")
    def test_consume_trace_equality(self):
        """This test relies on the setup for consume, it currently cannot be run on its own"""
        producer_span = self.get_span(interfaces.python_buddy, span_kind="producer", topic=self.BUDDY_TO_WEBLOG_TOPIC)
        consumer_span = self.get_span(interfaces.library, span_kind="consumer", topic=self.BUDDY_TO_WEBLOG_TOPIC)

        # Both producer and consumer spans should be part of the same trace
        # Different tracers can handle the exact propagation differently, so for now, this test avoids
        # asserting on direct parent/child relationships
        assert producer_span["trace_id"] == consumer_span["trace_id"]

    def validate_kafka_spans(self, producer_interface, consumer_interface, topic):
        """
            Validates production/consumption of kafka message.
            It works the same for both test_produce and test_consume
        """

        # Check that the producer did not created any consumer span
        assert self.get_span(producer_interface, span_kind="consumer", topic=topic) is None

        # Check that the consumer did not created any producer span
        assert self.get_span(consumer_interface, span_kind="producer", topic=topic) is None

        producer_span = self.get_span(producer_interface, span_kind="producer", topic=topic)
        consumer_span = self.get_span(consumer_interface, span_kind="consumer", topic=topic)
        # check that both consumer and producer spans exists
        assert producer_span is not None
        assert consumer_span is not None

        # java doesn't give us much to assert on
        if "java" not in consumer_span["meta"]["component"]:
            assert consumer_span["meta"]["kafka.received_message"] == "True"

        # Assert that the consumer span is not the root
        assert "parent_id" in consumer_span, "parent_id is missing in consumer span"

        # returns both span for any custom check
        return producer_span, consumer_span
