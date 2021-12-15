FROM system_tests/weblog

# Datadog conf for all weblogs
ENV DD_TRACE_HEADER_TAGS='user-agent:http.request.headers.user-agent'

ARG SYSTEM_TESTS_LIBRARY
ENV SYSTEM_TESTS_LIBRARY=$SYSTEM_TESTS_LIBRARY

ARG SYSTEM_TESTS_WEBLOG_VARIANT
ENV SYSTEM_TESTS_WEBLOG_VARIANT=$SYSTEM_TESTS_WEBLOG_VARIANT

ARG SYSTEM_TESTS_LIBRARY_VERSION
ENV SYSTEM_TESTS_LIBRARY_VERSION=$SYSTEM_TESTS_LIBRARY_VERSION

ARG SYSTEM_TESTS_LIBDDWAF_VERSION
ENV SYSTEM_TESTS_LIBDDWAF_VERSION=$SYSTEM_TESTS_LIBDDWAF_VERSION

# files for exotic scenarios
RUN echo "corrupted::data" > /appsec_corrupted_rules.yml