# Unless explicitly stated otherwise all files in this repository are licensed under the the Apache License Version 2.0.
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2021 Datadog, Inc.

import tag
import category
from model.categories import integration

"""
A feature to be tested.
"""
class Feature:

    name = "TODO"
    description = "TODO"
    
    categories = []
    tags = []
    tests = []

    def __init__(self, name, description):
        self.name = name
        self.description = description

    def __instancecheck__(cls, instance):
        return cls.__subclasscheck__(type(instance))

    def tag(self, tag = tag.Tag):
        self.tags.append(tag)

    def categorize(self, category = category.FeatureCategory):
        self.categories.append(category)

    def link_test(self, path = str):
        self.tests.append(path)

    def is_integration(self):
        self.categorize(integration.IntegrationCategory)