# Unless explicitly stated otherwise all files in this repository are licensed under the the Apache License Version 2.0.
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2021 Datadog, Inc.

from model import feature

"""
A grouping of features related to sampling.
"""
class SamplingCategory:

    features = []

    def __instancecheck__(cls, instance):
        return cls.__subclasscheck__(type(instance))

    def register_feature(self, feature: feature.Feature):
        """Register this feature in this category"""
        self.features.append(feature)
        feature.
