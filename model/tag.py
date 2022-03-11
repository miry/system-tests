# Unless explicitly stated otherwise all files in this repository are licensed under the the Apache License Version 2.0.
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2021 Datadog, Inc.

"""
A tag to make features searchable and discoverable.
"""
class Tag:

    name = "TODO"
    description = "TODO"
    features = []

    def __instancecheck__(cls, instance):
        return cls.__subclasscheck__(type(instance))

    def get_name(self) -> str:
        return "TODO"

    def get_description(self) -> str:
        return "TODO"