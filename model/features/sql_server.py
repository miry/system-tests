# Unless explicitly stated otherwise all files in this repository are licensed under the the Apache License Version 2.0.
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2021 Datadog, Inc.

from model import feature

"""
Coverage of sql server clients.
"""
class SqlServerFeature(feature.Feature):
    def __init__(self, name, description):
        self.name = "SQL Server Client"
        self.description = "Calls to SQL server are instrumented."
        self.link_test("/tests/test_traces.py")
        self.categorize(integration.IntegrationCategory)