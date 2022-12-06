# Unless explicitly stated otherwise all files in this repository are licensed under the the Apache License Version 2.0.
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2022 Datadog, Inc.

"""Telemetry tests for app-closing event"""
from utils import interfaces, bug, weblog
import time
import requests_unixsocket


@bug(library="cpp", reason="Not yet implemented")
@bug(library="golang", reason="Not yet implemented")
@bug(library="php", reason="Not yet implemented")
@bug(library="ruby", reason="Not yet implemented")
class Test_App_Closing:
    """Basic testing of app closing"""

    def test_app_closing(self):
        """Assert app-closing is sent when weblog app is closed"""

        def close_container():
            session = requests_unixsocket.Session()
            r = session.get("http+unix://%2Fvar%2Frun%2Fdocker.sock/containers/system-tests_weblog_1/kill")

        def close_weblog():
            weblog.post("/shutdown", data=None)

        close_weblog()
        close_container()
        time.sleep(5)
        interfaces.library.assert_app_closing_validation()
