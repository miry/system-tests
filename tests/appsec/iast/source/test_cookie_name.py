# Unless explicitly stated otherwise all files in this repository are licensed under the the Apache License Version 2.0.
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2021 Datadog, Inc.

from utils import coverage, bug
from .._test_iast_fixtures import BaseSourceTest


@coverage.basic
class TestCookieName(BaseSourceTest):
    """Verify that request cookies are tainted"""

    endpoint = "/iast/source/cookiename/test"
    requests_kwargs = [{"method": "GET", "cookies": {"user": "unused"}}]
    source_type = "http.request.cookie.name"
    source_name = "user"
    source_value = "user"

    @bug(library="java", reason="Not working as expected")
    def test_telemetry_metric_instrumented_source(self):
        super().test_telemetry_metric_instrumented_source()

    @bug(library="java", reason="Not working as expected")
    def test_telemetry_metric_executed_source(self):
        super().test_telemetry_metric_executed_source()
