# Unless explicitly stated otherwise all files in this repository are licensed under the the Apache License Version 2.0.
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2022 Datadog, Inc.
from collections import defaultdict

from utils import weblog, interfaces, context, scenarios


REQUEST_PREFIX = 'http.request.body.contents'
RESPONSE_PREFIX = 'http.response.body.contents'

@scenarios.integrations_payload_tagging
class Test_Payload_tagging:

    present_tags = {
        'foo.bar.baz': '1',
        'foo.bar.quux': '2',
        'foo.null item': 'null',
        'deep.trace.a.b.c.d.e.f.g.h': 'truncated',
        'array.isindexed.0': 'index0',
        'array.isindexed.1': 'index1',
        'array.isindexed.2': 'index2',
        'keys with `\\.`': 'are escaped',
        'token': 'redacted',
    }
    absent_tags = [
        'config filtered',
        'config filtered.should'
    ]

    traced_packages = {
        'nodejs': ['fetch'] # ,'http', 'http2']
    }

    def check_boolean(self, span, tag):
        if self.language == 'nodejs':
            return span.get('metrics', {}).get(tag), 1.0
        return span.get('meta', {}).get(tag), True

    @staticmethod
    def prefix_dict(obj, prefix):
        return {f'{prefix}.{k}': v for k, v in obj.items()}

    @staticmethod
    def prefix_list(obj, prefix):
        return [f'{prefix}.{k}' for k in obj]

    def init_with_payload(self, payload):
        self.requests = {}
        self.language = context.library.library

        integrations = self.traced_packages[self.language]
        self.requests[self.language] = defaultdict(list)
        for integration in integrations:
            self.requests[self.language][integration].append(
                weblog.post(
                    path=f'/payload_tagging/{integration}',
                    json=payload
                )
            )

    def filter_spans(self):
        spans = defaultdict(list)
        for integration, reqs in self.requests[self.language].items():
            for req in reqs:
                for _, trace in interfaces.library.get_traces(request=req):
                    for span in trace:
                        meta = span.get('meta', {})
                        if meta.get('component') != integration:
                            continue
                        if any(k.startswith(REQUEST_PREFIX) for k in meta.keys()):
                            spans[integration].append(span)
        return spans

    def check_tags(self, present_tags, absent_tags):
        payload_spans = self.filter_spans()
        assert len(payload_spans) > 0, 'no spans with payload information found'
        for integration, int_spans in payload_spans.items():
            for span in int_spans:
                meta = span.get('meta', {})
                for tag, value in present_tags.items():
                    tag_value = meta.get(tag)
                    assert tag_value is not None, f'{integration} - tag missing: {tag}'
                    assert tag_value == value, f'{integration} - {tag} value: expected {value}, got {tag_value}'
                for tag in absent_tags:
                    assert meta.get(tag) is None, f'{integration} - found unexpected tag {tag}'

        return payload_spans

    ### GENERIC PAYLOAD ###
    def setup_trace_client_payload(self):
        payload = {
            'token': 'shouldberemoved',
            'foo': {
                'bar': {
                    'baz': 1,
                    'quux': 2
                },
                'null item': None
            },
            'deep': {'trace': {'a': {'b': {'c': {'d': {'e': {'f': {'g': {'h': {'i': {'j': {}}}}}}}}}}}},
            'array': {
                'isindexed': ['index0', 'index1', 'index2']
            },
            'keys with `.`': 'are escaped',
            'config filtered': {'should': 'not be here'}
        }
        return self.init_with_payload(payload)

    def test_trace_client_payload(self):
        present_tags = {
            'foo.bar.baz': '1',
            'foo.bar.quux': '2',
            'foo.null item': 'null',
            'deep.trace.a.b.c.d.e.f.g.h': 'truncated',
            'array.isindexed.0': 'index0',
            'array.isindexed.1': 'index1',
            'array.isindexed.2': 'index2',
            'keys with `\\.`': 'are escaped',
            'token': 'redacted',
        }
        absent_tags = [
            'config filtered',
            'config filtered.should'
        ]
        return self.check_tags(
            self.prefix_dict(present_tags, REQUEST_PREFIX),
            self.prefix_list(absent_tags, REQUEST_PREFIX)
        )

    ### TRIMMED TAGS ###
    def setup_trace_client_max_tags(self):
        payload = {
            f'key{i+1}': f'value{i+1}' for i in range(760)
        }
        return self.init_with_payload(payload)

    def test_trace_client_max_tags(self):
        spans = self.filter_spans()

        for integration, int_spans in spans.items():
            for span in int_spans:
                tags = [*filter(lambda tag: tag.startswith(REQUEST_PREFIX), span.get('meta'))]
                assert len(tags) == 757, f'{integration} - got {len(tags)} tags, expected 757'
                tag_value, expected_value = self.check_boolean(span, '_dd.payload_tags_trimmed')
                assert tag_value is not None, 'No _dd.payload_tags_trimmed marker'
                assert tag_value == expected_value
