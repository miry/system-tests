# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: protos/apm_test_client.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x1cprotos/apm_test_client.proto\"\x8a\x02\n\rStartSpanArgs\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x14\n\x07service\x18\x02 \x01(\tH\x00\x88\x01\x01\x12\x16\n\tparent_id\x18\x03 \x01(\x04H\x01\x88\x01\x01\x12\x15\n\x08resource\x18\x04 \x01(\tH\x02\x88\x01\x01\x12\x11\n\x04type\x18\x05 \x01(\tH\x03\x88\x01\x01\x12\x13\n\x06origin\x18\x06 \x01(\tH\x04\x88\x01\x01\x12\x32\n\x0chttp_headers\x18\x07 \x01(\x0b\x32\x17.DistributedHTTPHeadersH\x05\x88\x01\x01\x42\n\n\x08_serviceB\x0c\n\n_parent_idB\x0b\n\t_resourceB\x07\n\x05_typeB\t\n\x07_originB\x0f\n\r_http_headers\"\x8c\x01\n\x16\x44istributedHTTPHeaders\x12>\n\x0chttp_headers\x18\t \x03(\x0b\x32(.DistributedHTTPHeaders.HttpHeadersEntry\x1a\x32\n\x10HttpHeadersEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x02\x38\x01\"4\n\x0fStartSpanReturn\x12\x0f\n\x07span_id\x18\x01 \x01(\x04\x12\x10\n\x08trace_id\x18\x02 \x01(\x04\"$\n\x11InjectHeadersArgs\x12\x0f\n\x07span_id\x18\x01 \x01(\x04\"Z\n\x13InjectHeadersReturn\x12\x32\n\x0chttp_headers\x18\x01 \x01(\x0b\x32\x17.DistributedHTTPHeadersH\x00\x88\x01\x01\x42\x0f\n\r_http_headers\"\x1c\n\x0e\x46inishSpanArgs\x12\n\n\x02id\x18\x01 \x01(\x04\"\x12\n\x10\x46inishSpanReturn\">\n\x0fSpanSetMetaArgs\x12\x0f\n\x07span_id\x18\x01 \x01(\x04\x12\x0b\n\x03key\x18\x02 \x01(\t\x12\r\n\x05value\x18\x03 \x01(\t\"\x13\n\x11SpanSetMetaReturn\"@\n\x11SpanSetMetricArgs\x12\x0f\n\x07span_id\x18\x01 \x01(\x04\x12\x0b\n\x03key\x18\x02 \x01(\t\x12\r\n\x05value\x18\x03 \x01(\x02\"\x15\n\x13SpanSetMetricReturn\"\x7f\n\x10SpanSetErrorArgs\x12\x0f\n\x07span_id\x18\x01 \x01(\x04\x12\x11\n\x04type\x18\x02 \x01(\tH\x00\x88\x01\x01\x12\x14\n\x07message\x18\x03 \x01(\tH\x01\x88\x01\x01\x12\x12\n\x05stack\x18\x04 \x01(\tH\x02\x88\x01\x01\x42\x07\n\x05_typeB\n\n\x08_messageB\x08\n\x06_stack\"\x14\n\x12SpanSetErrorReturn\"\x10\n\x0e\x46lushSpansArgs\"\x12\n\x10\x46lushSpansReturn\"\x15\n\x13\x46lushTraceStatsArgs\"\x17\n\x15\x46lushTraceStatsReturn\"\x10\n\x0eStopTracerArgs\"\x12\n\x10StopTracerReturn2\x86\x04\n\tAPMClient\x12/\n\tStartSpan\x12\x0e.StartSpanArgs\x1a\x10.StartSpanReturn\"\x00\x12\x32\n\nFinishSpan\x12\x0f.FinishSpanArgs\x1a\x11.FinishSpanReturn\"\x00\x12\x35\n\x0bSpanSetMeta\x12\x10.SpanSetMetaArgs\x1a\x12.SpanSetMetaReturn\"\x00\x12;\n\rSpanSetMetric\x12\x12.SpanSetMetricArgs\x1a\x14.SpanSetMetricReturn\"\x00\x12\x38\n\x0cSpanSetError\x12\x11.SpanSetErrorArgs\x1a\x13.SpanSetErrorReturn\"\x00\x12;\n\rInjectHeaders\x12\x12.InjectHeadersArgs\x1a\x14.InjectHeadersReturn\"\x00\x12\x32\n\nFlushSpans\x12\x0f.FlushSpansArgs\x1a\x11.FlushSpansReturn\"\x00\x12\x41\n\x0f\x46lushTraceStats\x12\x14.FlushTraceStatsArgs\x1a\x16.FlushTraceStatsReturn\"\x00\x12\x32\n\nStopTracer\x12\x0f.StopTracerArgs\x1a\x11.StopTracerReturn\"\x00\x62\x06proto3')



_STARTSPANARGS = DESCRIPTOR.message_types_by_name['StartSpanArgs']
_DISTRIBUTEDHTTPHEADERS = DESCRIPTOR.message_types_by_name['DistributedHTTPHeaders']
_DISTRIBUTEDHTTPHEADERS_HTTPHEADERSENTRY = _DISTRIBUTEDHTTPHEADERS.nested_types_by_name['HttpHeadersEntry']
_STARTSPANRETURN = DESCRIPTOR.message_types_by_name['StartSpanReturn']
_INJECTHEADERSARGS = DESCRIPTOR.message_types_by_name['InjectHeadersArgs']
_INJECTHEADERSRETURN = DESCRIPTOR.message_types_by_name['InjectHeadersReturn']
_FINISHSPANARGS = DESCRIPTOR.message_types_by_name['FinishSpanArgs']
_FINISHSPANRETURN = DESCRIPTOR.message_types_by_name['FinishSpanReturn']
_SPANSETMETAARGS = DESCRIPTOR.message_types_by_name['SpanSetMetaArgs']
_SPANSETMETARETURN = DESCRIPTOR.message_types_by_name['SpanSetMetaReturn']
_SPANSETMETRICARGS = DESCRIPTOR.message_types_by_name['SpanSetMetricArgs']
_SPANSETMETRICRETURN = DESCRIPTOR.message_types_by_name['SpanSetMetricReturn']
_SPANSETERRORARGS = DESCRIPTOR.message_types_by_name['SpanSetErrorArgs']
_SPANSETERRORRETURN = DESCRIPTOR.message_types_by_name['SpanSetErrorReturn']
_FLUSHSPANSARGS = DESCRIPTOR.message_types_by_name['FlushSpansArgs']
_FLUSHSPANSRETURN = DESCRIPTOR.message_types_by_name['FlushSpansReturn']
_FLUSHTRACESTATSARGS = DESCRIPTOR.message_types_by_name['FlushTraceStatsArgs']
_FLUSHTRACESTATSRETURN = DESCRIPTOR.message_types_by_name['FlushTraceStatsReturn']
_STOPTRACERARGS = DESCRIPTOR.message_types_by_name['StopTracerArgs']
_STOPTRACERRETURN = DESCRIPTOR.message_types_by_name['StopTracerReturn']
StartSpanArgs = _reflection.GeneratedProtocolMessageType('StartSpanArgs', (_message.Message,), {
  'DESCRIPTOR' : _STARTSPANARGS,
  '__module__' : 'protos.apm_test_client_pb2'
  # @@protoc_insertion_point(class_scope:StartSpanArgs)
  })
_sym_db.RegisterMessage(StartSpanArgs)

DistributedHTTPHeaders = _reflection.GeneratedProtocolMessageType('DistributedHTTPHeaders', (_message.Message,), {

  'HttpHeadersEntry' : _reflection.GeneratedProtocolMessageType('HttpHeadersEntry', (_message.Message,), {
    'DESCRIPTOR' : _DISTRIBUTEDHTTPHEADERS_HTTPHEADERSENTRY,
    '__module__' : 'protos.apm_test_client_pb2'
    # @@protoc_insertion_point(class_scope:DistributedHTTPHeaders.HttpHeadersEntry)
    })
  ,
  'DESCRIPTOR' : _DISTRIBUTEDHTTPHEADERS,
  '__module__' : 'protos.apm_test_client_pb2'
  # @@protoc_insertion_point(class_scope:DistributedHTTPHeaders)
  })
_sym_db.RegisterMessage(DistributedHTTPHeaders)
_sym_db.RegisterMessage(DistributedHTTPHeaders.HttpHeadersEntry)

StartSpanReturn = _reflection.GeneratedProtocolMessageType('StartSpanReturn', (_message.Message,), {
  'DESCRIPTOR' : _STARTSPANRETURN,
  '__module__' : 'protos.apm_test_client_pb2'
  # @@protoc_insertion_point(class_scope:StartSpanReturn)
  })
_sym_db.RegisterMessage(StartSpanReturn)

InjectHeadersArgs = _reflection.GeneratedProtocolMessageType('InjectHeadersArgs', (_message.Message,), {
  'DESCRIPTOR' : _INJECTHEADERSARGS,
  '__module__' : 'protos.apm_test_client_pb2'
  # @@protoc_insertion_point(class_scope:InjectHeadersArgs)
  })
_sym_db.RegisterMessage(InjectHeadersArgs)

InjectHeadersReturn = _reflection.GeneratedProtocolMessageType('InjectHeadersReturn', (_message.Message,), {
  'DESCRIPTOR' : _INJECTHEADERSRETURN,
  '__module__' : 'protos.apm_test_client_pb2'
  # @@protoc_insertion_point(class_scope:InjectHeadersReturn)
  })
_sym_db.RegisterMessage(InjectHeadersReturn)

FinishSpanArgs = _reflection.GeneratedProtocolMessageType('FinishSpanArgs', (_message.Message,), {
  'DESCRIPTOR' : _FINISHSPANARGS,
  '__module__' : 'protos.apm_test_client_pb2'
  # @@protoc_insertion_point(class_scope:FinishSpanArgs)
  })
_sym_db.RegisterMessage(FinishSpanArgs)

FinishSpanReturn = _reflection.GeneratedProtocolMessageType('FinishSpanReturn', (_message.Message,), {
  'DESCRIPTOR' : _FINISHSPANRETURN,
  '__module__' : 'protos.apm_test_client_pb2'
  # @@protoc_insertion_point(class_scope:FinishSpanReturn)
  })
_sym_db.RegisterMessage(FinishSpanReturn)

SpanSetMetaArgs = _reflection.GeneratedProtocolMessageType('SpanSetMetaArgs', (_message.Message,), {
  'DESCRIPTOR' : _SPANSETMETAARGS,
  '__module__' : 'protos.apm_test_client_pb2'
  # @@protoc_insertion_point(class_scope:SpanSetMetaArgs)
  })
_sym_db.RegisterMessage(SpanSetMetaArgs)

SpanSetMetaReturn = _reflection.GeneratedProtocolMessageType('SpanSetMetaReturn', (_message.Message,), {
  'DESCRIPTOR' : _SPANSETMETARETURN,
  '__module__' : 'protos.apm_test_client_pb2'
  # @@protoc_insertion_point(class_scope:SpanSetMetaReturn)
  })
_sym_db.RegisterMessage(SpanSetMetaReturn)

SpanSetMetricArgs = _reflection.GeneratedProtocolMessageType('SpanSetMetricArgs', (_message.Message,), {
  'DESCRIPTOR' : _SPANSETMETRICARGS,
  '__module__' : 'protos.apm_test_client_pb2'
  # @@protoc_insertion_point(class_scope:SpanSetMetricArgs)
  })
_sym_db.RegisterMessage(SpanSetMetricArgs)

SpanSetMetricReturn = _reflection.GeneratedProtocolMessageType('SpanSetMetricReturn', (_message.Message,), {
  'DESCRIPTOR' : _SPANSETMETRICRETURN,
  '__module__' : 'protos.apm_test_client_pb2'
  # @@protoc_insertion_point(class_scope:SpanSetMetricReturn)
  })
_sym_db.RegisterMessage(SpanSetMetricReturn)

SpanSetErrorArgs = _reflection.GeneratedProtocolMessageType('SpanSetErrorArgs', (_message.Message,), {
  'DESCRIPTOR' : _SPANSETERRORARGS,
  '__module__' : 'protos.apm_test_client_pb2'
  # @@protoc_insertion_point(class_scope:SpanSetErrorArgs)
  })
_sym_db.RegisterMessage(SpanSetErrorArgs)

SpanSetErrorReturn = _reflection.GeneratedProtocolMessageType('SpanSetErrorReturn', (_message.Message,), {
  'DESCRIPTOR' : _SPANSETERRORRETURN,
  '__module__' : 'protos.apm_test_client_pb2'
  # @@protoc_insertion_point(class_scope:SpanSetErrorReturn)
  })
_sym_db.RegisterMessage(SpanSetErrorReturn)

FlushSpansArgs = _reflection.GeneratedProtocolMessageType('FlushSpansArgs', (_message.Message,), {
  'DESCRIPTOR' : _FLUSHSPANSARGS,
  '__module__' : 'protos.apm_test_client_pb2'
  # @@protoc_insertion_point(class_scope:FlushSpansArgs)
  })
_sym_db.RegisterMessage(FlushSpansArgs)

FlushSpansReturn = _reflection.GeneratedProtocolMessageType('FlushSpansReturn', (_message.Message,), {
  'DESCRIPTOR' : _FLUSHSPANSRETURN,
  '__module__' : 'protos.apm_test_client_pb2'
  # @@protoc_insertion_point(class_scope:FlushSpansReturn)
  })
_sym_db.RegisterMessage(FlushSpansReturn)

FlushTraceStatsArgs = _reflection.GeneratedProtocolMessageType('FlushTraceStatsArgs', (_message.Message,), {
  'DESCRIPTOR' : _FLUSHTRACESTATSARGS,
  '__module__' : 'protos.apm_test_client_pb2'
  # @@protoc_insertion_point(class_scope:FlushTraceStatsArgs)
  })
_sym_db.RegisterMessage(FlushTraceStatsArgs)

FlushTraceStatsReturn = _reflection.GeneratedProtocolMessageType('FlushTraceStatsReturn', (_message.Message,), {
  'DESCRIPTOR' : _FLUSHTRACESTATSRETURN,
  '__module__' : 'protos.apm_test_client_pb2'
  # @@protoc_insertion_point(class_scope:FlushTraceStatsReturn)
  })
_sym_db.RegisterMessage(FlushTraceStatsReturn)

StopTracerArgs = _reflection.GeneratedProtocolMessageType('StopTracerArgs', (_message.Message,), {
  'DESCRIPTOR' : _STOPTRACERARGS,
  '__module__' : 'protos.apm_test_client_pb2'
  # @@protoc_insertion_point(class_scope:StopTracerArgs)
  })
_sym_db.RegisterMessage(StopTracerArgs)

StopTracerReturn = _reflection.GeneratedProtocolMessageType('StopTracerReturn', (_message.Message,), {
  'DESCRIPTOR' : _STOPTRACERRETURN,
  '__module__' : 'protos.apm_test_client_pb2'
  # @@protoc_insertion_point(class_scope:StopTracerReturn)
  })
_sym_db.RegisterMessage(StopTracerReturn)

_APMCLIENT = DESCRIPTOR.services_by_name['APMClient']
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _DISTRIBUTEDHTTPHEADERS_HTTPHEADERSENTRY._options = None
  _DISTRIBUTEDHTTPHEADERS_HTTPHEADERSENTRY._serialized_options = b'8\001'
  _STARTSPANARGS._serialized_start=33
  _STARTSPANARGS._serialized_end=299
  _DISTRIBUTEDHTTPHEADERS._serialized_start=302
  _DISTRIBUTEDHTTPHEADERS._serialized_end=442
  _DISTRIBUTEDHTTPHEADERS_HTTPHEADERSENTRY._serialized_start=392
  _DISTRIBUTEDHTTPHEADERS_HTTPHEADERSENTRY._serialized_end=442
  _STARTSPANRETURN._serialized_start=444
  _STARTSPANRETURN._serialized_end=496
  _INJECTHEADERSARGS._serialized_start=498
  _INJECTHEADERSARGS._serialized_end=534
  _INJECTHEADERSRETURN._serialized_start=536
  _INJECTHEADERSRETURN._serialized_end=626
  _FINISHSPANARGS._serialized_start=628
  _FINISHSPANARGS._serialized_end=656
  _FINISHSPANRETURN._serialized_start=658
  _FINISHSPANRETURN._serialized_end=676
  _SPANSETMETAARGS._serialized_start=678
  _SPANSETMETAARGS._serialized_end=740
  _SPANSETMETARETURN._serialized_start=742
  _SPANSETMETARETURN._serialized_end=761
  _SPANSETMETRICARGS._serialized_start=763
  _SPANSETMETRICARGS._serialized_end=827
  _SPANSETMETRICRETURN._serialized_start=829
  _SPANSETMETRICRETURN._serialized_end=850
  _SPANSETERRORARGS._serialized_start=852
  _SPANSETERRORARGS._serialized_end=979
  _SPANSETERRORRETURN._serialized_start=981
  _SPANSETERRORRETURN._serialized_end=1001
  _FLUSHSPANSARGS._serialized_start=1003
  _FLUSHSPANSARGS._serialized_end=1019
  _FLUSHSPANSRETURN._serialized_start=1021
  _FLUSHSPANSRETURN._serialized_end=1039
  _FLUSHTRACESTATSARGS._serialized_start=1041
  _FLUSHTRACESTATSARGS._serialized_end=1062
  _FLUSHTRACESTATSRETURN._serialized_start=1064
  _FLUSHTRACESTATSRETURN._serialized_end=1087
  _STOPTRACERARGS._serialized_start=1089
  _STOPTRACERARGS._serialized_end=1105
  _STOPTRACERRETURN._serialized_start=1107
  _STOPTRACERRETURN._serialized_end=1125
  _APMCLIENT._serialized_start=1128
  _APMCLIENT._serialized_end=1646
# @@protoc_insertion_point(module_scope)
