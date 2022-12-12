# Unless explicitly stated otherwise all files in this repository are licensed under the the Apache License Version 2.0.
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2021 Datadog, Inc.

import pytest
from tests.constants import PYTHON_RELEASE_GA_1_1, PYTHON_RELEASE_PUBLIC_BETA
from utils import bug, context, coverage, interfaces, irrelevant, released, rfc, weblog
from utils.tools import logger


# *ATTENTION*: Copy this file to the tests folder, modify, and rename with a prefix of `test_` to enable your new tests

# There are ways to mark a test to be skipped in pytest, which may or may not be relevant for your tests.
# Use any of the following examples and add them as decorators on your test class.
#  - Require a specific version condition:
#       @bug(context.library < "golang@1.36.0")
#  - Skip for an entire library:
#       @irrelevant(context.library != "java", reason="*ATTENTION*: The reason the language is skipped")
#  - Skip for every library except one
#       @irrelevant(context.library = "dotnet", reason="only for .NET")

# To run an individual test: ./run.sh tests/test_traces.py::Test_Misc::test_main
@released(dotnet="2.13.0", golang="1.40.0", java="0.107.1", nodejs="3.0.0")
class Test_Misc:
    """TODO: what does this test do"""

    def setup_main(self):
        self.r = weblog.get("/")

    def test_main(self):
        interfaces.library.assert_receive_request_root_trace()
        b_data = interfaces.backend.get_backend_data(self.r)
        logger.info('GOT SOME B_DATA: ')
        logger.info(b_data)

