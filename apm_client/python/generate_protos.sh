#!/bin/bash

arch -x86_64 python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. apm_test_client/pb/apm_test_client.proto
