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




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x1cprotos/apm_test_client.proto\"}\n\rStartSpanArgs\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x0f\n\x02id\x18\x02 \x01(\x04H\x00\x88\x01\x01\x12\x14\n\x07service\x18\x03 \x01(\tH\x01\x88\x01\x01\x12\x16\n\tparent_id\x18\x04 \x01(\x04H\x02\x88\x01\x01\x42\x05\n\x03_idB\n\n\x08_serviceB\x0c\n\n_parent_id\"\x1d\n\x0fStartSpanReturn\x12\n\n\x02id\x18\x01 \x01(\x04\"\x1c\n\x0e\x46inishSpanArgs\x12\n\n\x02id\x18\x01 \x01(\x04\"\x12\n\x10\x46inishSpanReturn\"\x10\n\x0e\x46lushSpansArgs\"\x12\n\x10\x46lushSpansReturn2\xa4\x01\n\tAPMClient\x12/\n\tStartSpan\x12\x0e.StartSpanArgs\x1a\x10.StartSpanReturn\"\x00\x12\x32\n\nFinishSpan\x12\x0f.FinishSpanArgs\x1a\x11.FinishSpanReturn\"\x00\x12\x32\n\nFlushSpans\x12\x0f.FlushSpansArgs\x1a\x11.FlushSpansReturn\"\x00\x62\x06proto3')



_STARTSPANARGS = DESCRIPTOR.message_types_by_name['StartSpanArgs']
_STARTSPANRETURN = DESCRIPTOR.message_types_by_name['StartSpanReturn']
_FINISHSPANARGS = DESCRIPTOR.message_types_by_name['FinishSpanArgs']
_FINISHSPANRETURN = DESCRIPTOR.message_types_by_name['FinishSpanReturn']
_FLUSHSPANSARGS = DESCRIPTOR.message_types_by_name['FlushSpansArgs']
_FLUSHSPANSRETURN = DESCRIPTOR.message_types_by_name['FlushSpansReturn']
StartSpanArgs = _reflection.GeneratedProtocolMessageType('StartSpanArgs', (_message.Message,), {
  'DESCRIPTOR' : _STARTSPANARGS,
  '__module__' : 'protos.apm_test_client_pb2'
  # @@protoc_insertion_point(class_scope:StartSpanArgs)
  })
_sym_db.RegisterMessage(StartSpanArgs)

StartSpanReturn = _reflection.GeneratedProtocolMessageType('StartSpanReturn', (_message.Message,), {
  'DESCRIPTOR' : _STARTSPANRETURN,
  '__module__' : 'protos.apm_test_client_pb2'
  # @@protoc_insertion_point(class_scope:StartSpanReturn)
  })
_sym_db.RegisterMessage(StartSpanReturn)

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

_APMCLIENT = DESCRIPTOR.services_by_name['APMClient']
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _STARTSPANARGS._serialized_start=32
  _STARTSPANARGS._serialized_end=157
  _STARTSPANRETURN._serialized_start=159
  _STARTSPANRETURN._serialized_end=188
  _FINISHSPANARGS._serialized_start=190
  _FINISHSPANARGS._serialized_end=218
  _FINISHSPANRETURN._serialized_start=220
  _FINISHSPANRETURN._serialized_end=238
  _FLUSHSPANSARGS._serialized_start=240
  _FLUSHSPANSARGS._serialized_end=256
  _FLUSHSPANSRETURN._serialized_start=258
  _FLUSHSPANSRETURN._serialized_end=276
  _APMCLIENT._serialized_start=279
  _APMCLIENT._serialized_end=443
# @@protoc_insertion_point(module_scope)
