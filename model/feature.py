# Unless explicitly stated otherwise all files in this repository are licensed under the the Apache License Version 2.0.
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2021 Datadog, Inc.

import tag
import category

"""
A feature to be tested.
"""
class Feature:

    name = "TODO"
    description = "TODO"
    categories = []
    tags = []

    def __instancecheck__(cls, instance):
        return cls.__subclasscheck__(type(instance))

    def get_description(self) -> str:
        return "TODO"

    def tag(self, tag = tag.Tag) -> str:
        self.tags.append(tag)

    def categorize(self, category = category.FeatureCategory) -> str:
        self.categories.append(category)