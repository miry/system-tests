# Unless explicitly stated otherwise all files in this repository are licensed under the the Apache License Version 2.0.
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2021 Datadog, Inc.

from model import tag

"""
A grouping of features related to sampling.
"""
class SamplingCategory(tag.Tag):
    name = "Sampling"
    description = "Features which relate to sampling decisions and priority."