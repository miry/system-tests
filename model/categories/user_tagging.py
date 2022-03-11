# Unless explicitly stated otherwise all files in this repository are licensed under the the Apache License Version 2.0.
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2021 Datadog, Inc.

from model import feature
from model.category import FeatureCategory

"""
A grouping of features related to tagging.
"""
class UserTaggingCategory(FeatureCategory):
    name = "User Tagging"
    description = "Features which relate to applying user configured tags to traces and spans."