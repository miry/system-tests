# Unless explicitly stated otherwise all files in this repository are licensed under the the Apache License Version 2.0.
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2021 Datadog, Inc.

import tag
import category
from model.categories import integration

class Test:
    """
    A test to be run.
    """

    """A concise name for this test."""
    name = "TODO"

    """A longer description of what this test does."""
    description = "TODO"

    """The result of the test, zero is good."""
    result = -1

    """A summary of the test results that humans can make sense of."""
    result_summary = "TODO"

    """An identifier used to correlate the requests made to the assertions"""
    correlation_id = 0

    """A timeout for the assertions"""
    timeout = 10000

    def __init__(self, name, description):
        self.name = name
        self.description = description
        self.correlation_id = id(self)

    """The request(s) to execute this test"""
    def execute_request(self):
        raise Exception("The execute function must be overriden")

    """The assertions to make after the requests finish, or a timeout is reached"""
    def wait_until(self):
        raise Exception("An condition to wait for must be specified")

    """The assertions to make after the requests finish, or a timeout is reached"""
    def make_assertion(self):
        raise Exception("An assertion must be made")
