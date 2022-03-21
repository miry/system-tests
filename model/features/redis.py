# Unless explicitly stated otherwise all files in this repository are licensed under the the Apache License Version 2.0.
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2021 Datadog, Inc.

from model import feature
from model.categories import integration

"""
Coverage of redis clients.
"""
class RedisFeature(feature.Feature):
    def __init__(self, name, description):
        self.name = "Redis Client"
        self.description = "Calls to redis are instrumented."
        self.link_test("/tests/test_traces.py")
        self.is_integration()