# Unless explicitly stated otherwise all files in this repository are licensed under the the Apache License Version 2.0.
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2021 Datadog, Inc.

from utils import BaseTestCase, interfaces, context, irrelevant
from utils.warmups import default_warmup

context.add_warmup(default_warmup)

# @irrelevant(context.library != "java", reason="Need to build endpoint on weblog")
class Test_Misc(BaseTestCase):
    """ Check that traces are reported for some services """

    def _get_rid_from_span(span):

        # code version
        user_agent = span.get("meta", {}).get("http.request.headers.user-agent", None)

        if not user_agent:  # try something for .NET
            user_agent = span.get("meta", {}).get("http_request_headers_user-agent", None)

        if not user_agent:  # last hope
            user_agent = span.get("meta", {}).get("http.useragent", None)

        if not user_agent or "rid/" not in user_agent:
            return None

        rid = user_agent[-36:]
        return rid  

    def test_main(self):
        r = self.weblog_get("/trace/http")
        interfaces.library.assert_trace_exists(r)
        path_filters = "/v0.4/traces"
        found_trace = False
        for trace in r["request"]["content"]:
            for span in trace:
                if self.rid:
                    if self.rid == self._get_rid_from_span(span):
                        found_trace = True
        assert found_trace == True
