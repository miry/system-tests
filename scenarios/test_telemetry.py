# Unless explicitly stated otherwise all files in this repository are licensed under the the Apache License Version 2.0.
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2022 Datadog, Inc.

"""Telemetry tests for app-closing event"""
from utils import BaseTestCase, interfaces, bug
import time


@bug(library="cpp", reason="Need to understand how to activate profiling")
@bug(library="golang", reason="Need to understand how to activate profiling")
@bug(library="dotnet", reason="Need to understand how to activate profiling")
@bug(library="php", reason="Need to understand how to activate profiling")
@bug(library="ruby", reason="Need to understand how to activate profiling")
class Test_App_Closing(BaseTestCase):
    """Basic testing of app closing"""

    def test_app_closing(self):
        """Assert app-closing is sent when weblog app is closed"""
        time.sleep(5)
        self.weblog_post("/shutdown", data=None)
        # time.sleep(5)
        interfaces.library.assert_app_closing_validation()
