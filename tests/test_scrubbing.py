# Unless explicitly stated otherwise all files in this repository are licensed under the the Apache License Version 2.0.
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2022 Datadog, Inc.

import pytest
from utils import bug, context, coverage, interfaces, released, rfc, weblog, missing_feature

if context.library == "cpp":
    pytestmark = pytest.mark.skip("not relevant")


def validate_no_leak(needle, whitelist=None):
    def crawler(data):
        if isinstance(data, str):
            if whitelist is not None and data != whitelist:
                assert needle not in data
        elif isinstance(data, (list, tuple)):
            for value in data:
                crawler(value)
        elif isinstance(data, dict):
            for key, value in data.items():
                assert needle not in key
                crawler(value)
        elif isinstance(data, (int, float, bool)) or data is None:
            pass

    return crawler


@released(dotnet="2.13.0", golang="1.40.0", java="0.107.1", nodejs="3.0.0")
@released(php="0.76.0", python="1.6.0rc1.dev", ruby="1.0.0")
@rfc("https://datadoghq.atlassian.net/wiki/spaces/APS/pages/2490990623/QueryString+-+Sensitive+Data+Obfuscation")
@bug(weblog_variant="spring-boot-undertow", reason="APMJAVA-877")
@coverage.good
class Test_UrlQuery:
    """ PII values in query parameter are all removed"""

    def setup_main(self):
        weblog.get("/", params={"pass": "leak-url-main-v1", "key2": "val2", "key3": "val3"})
        weblog.get("/", params={"key1": "val1", "public_key": "leak-url-main-v2", "key3": "val3"})
        weblog.get("/", params={"key1": "val1", "key2": "val2", "token": "leak-url-main-v3"})
        weblog.get("/", params={"json": '{"sign":"leak-url-main-v4"}'})

    def test_main(self):
        interfaces.library.validate(validate_no_leak("leak-url-main"), success_by_default=True)

    def setup_multiple_matching_substring(self):
        weblog.get(
            "/",
            params={
                "token": "leak-url-multiple-v1",
                "key1": "val1",
                "key2": "val2",
                "pass": "leak-url-multiple-v2",
                "public_key": "leak-url-multiple-v3",
                "key3": "val3",
                "json": '{"sign":"leak-url-multiple-v4"}',
            },
        )

    @bug(context.library < "dotnet@2.21.0", reason="APPSEC-5773")
    def test_multiple_matching_substring(self):
        interfaces.library.validate(validate_no_leak("leak-url-multiple"), success_by_default=True)


@released(python="1.7.1")
@missing_feature(library="dotnet", reason="Needs weblog endpoint")
@missing_feature(library="java", reason="Needs weblog endpoint")
@missing_feature(library="ruby", reason="Needs weblog endpoint")
@coverage.basic
class Test_UrlField:
    """ PII in url field are removed on distant calls """

    def _setup(self):
        if not hasattr(self, "r"):
            self.r = weblog.get("/make_distant_call", params={"url": "http://name:leak-password-url@runner:8126"})

    def setup_main(self):
        self._setup()

    def test_main(self):
        """ check that not data is leaked"""
        assert self.r.status_code == 200

        # the initial request contains leak-password-url, and is reported, but it's not the issue
        # we whitelist this value
        whitelist = "http://weblog:7777/make_distant_call?url=http%3A%2F%2Fname%3Aleak-password-url%40runner%3A8126"

        interfaces.library.validate(validate_no_leak("leak-password-url", whitelist), success_by_default=True)

    def setup_distant_call_is_reported(self):
        self._setup()

    @missing_feature(library="golang", reason="Need to wrap the http client")
    @missing_feature(library="php", reason="Not reported")
    def test_distant_call_is_reported(self):
        """ check that the distant call is reported"""

        def validator(trace):
            for span in trace:
                if span.get("type") == "http":
                    assert span["meta"]["http.url"] == "http://runner:8126/"
                    return True

        interfaces.library.validate_traces(self.r, validator)


@coverage.good
class Test_EnvVar:
    """ Environnement variables are not leaked"""

    def test_library(self):
        interfaces.library.validate(validate_no_leak("leaked-env-var"), success_by_default=True)

    def test_agent(self):
        interfaces.agent.validate(validate_no_leak("leaked-env-var"), success_by_default=True)

    def test_logs(self):
        interfaces.library_stdout.assert_absence(".*leaked-env-var.*")
        interfaces.library_dotnet_managed.assert_absence(".*leaked-env-var.*")
        interfaces.agent_stdout.assert_absence(".*leaked-env-var.*")  # TODO
