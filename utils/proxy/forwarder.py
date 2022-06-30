# Unless explicitly stated otherwise all files in this repository are licensed under the the Apache License Version 2.0.
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2021 Datadog, Inc.

import os
import json
import socket
from datetime import datetime
from http.client import HTTPConnection
import logging
from mitmproxy import http
from mitmproxy.flow import Error as FlowError


SIMPLE_TYPES = (bool, int, float, type(None))

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
handler.setFormatter(logging.Formatter("%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s", "%H:%M:%S"))
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


class Forwarder(object):
    def __init__(self):
        self.forward_ip = os.environ.get("FORWARD_TO_HOST", "runner")
        self.forward_port = os.environ.get("FORWARD_TO_PORT", "8081")
        self.interface_name = os.environ.get("INTERFACE_NAME", "")

        self.dd_api_key = os.environ["DD_API_KEY"]

        # This is the proxy state. Basically, true or false values that tells the proxy to enable, or not
        # specific behavior. You can get/modify it using a direct GET/POST /_system_tests_state request to the proxy
        self.state = json.loads(os.environ.get("INITIAL_PROXY_STATE", "") or "{}")

        # for config backend mock
        self.config_request_count = 0

        logger.info(f"Initial state: {self.state}")
        logger.info(f"Forward flows to {self.forward_ip}:{self.forward_port}")

    def _scrub(self, content):
        if isinstance(content, str):
            return content.replace(self.dd_api_key, "{redacted-by-system-tests-proxy}")
        elif isinstance(content, (list, set, tuple)):
            return [self._scrub(item) for item in content]
        elif isinstance(content, dict):
            return {key: self._scrub(value) for key, value in content.items()}
        elif isinstance(content, SIMPLE_TYPES):
            return content
        else:
            logger.error(f"Can't scrub type {type(content)}")
            return content

    @staticmethod
    def is_direct_command(flow):
        return flow.request.path == "/_system_tests_state"

    @staticmethod
    def is_health_request(flow):
        return flow.request.path == "/_system_tests_health"

    def request(self, flow):
        if self.is_health_request(flow):
            flow.response = http.Response.make(200, "ok\n")

        if self.is_direct_command(flow):
            logger.info(f"Direct command to proxy: {flow.request.pretty_url}")

            try:
                if flow.request.method == "GET":
                    flow.response = http.Response.make(
                        200, json.dumps(self.state), {"Content-Type": "application/json"}
                    )

                elif flow.request.method == "POST":
                    new_state = json.loads(flow.request.content)
                    logger.info(f"New state: {new_state}")
                    self.state.clear()
                    self.state.update(new_state)
                    flow.response = http.Response.make(
                        200, json.dumps(self.state), {"Content-Type": "application/json"}
                    )
                else:
                    flow.response = http.Response.make(405)
            except Exception as e:
                flow.response = http.Response.make(500, repr(e))

    def response(self, flow):
        if self.is_direct_command(flow) or self.is_health_request(flow):
            return

        logger.info(f"Received {flow.request.pretty_url} {flow.response.status_code}")

        self._modify_response(flow)

        request_content = str(flow.request.content)
        response_content = str(flow.response.content)

        if "?" in flow.request.path:
            path, query = flow.request.path.split("?", 1)
        else:
            path, query = flow.request.path, ""

        payload = {
            "path": path,
            "query": query,
            "host": flow.request.host,
            "port": flow.request.port,
            "request": {
                "timestamp_start": datetime.fromtimestamp(flow.request.timestamp_start).isoformat(),
                "content": request_content,
                "headers": [(k, v) for k, v in flow.request.headers.items()],
                "length": len(flow.request.content) if flow.request.content else 0,
            },
            "response": {
                "status_code": flow.response.status_code,
                "content": response_content,
                "headers": [(k, v) for k, v in flow.response.headers.items()],
                "length": len(flow.response.content) if flow.response.content else 0,
            },
        }

        if flow.error and flow.error.msg == FlowError.KILLED_MESSAGE:
            payload["response"] = None

        conn = HTTPConnection(self.forward_ip, self.forward_port)

        try:
            conn.request(
                "POST",
                f"/proxy/{self.interface_name}",
                body=json.dumps(self._scrub(payload)),
                headers={"Content-type": "application/json"},
            )
        except socket.gaierror:
            logger.error(f"Can't resolve to forward {self.forward_ip}:{self.forward_port}")
        except ConnectionRefusedError:
            logger.error("Can't forward, connection refused")
        except BrokenPipeError:
            logger.error("Can't forward, broken pipe")
        except TimeoutError:
            logger.error("Can't forward, time out")
        except Exception as e:
            logger.error(f"Can't forward: {e}")
        finally:
            conn.close()

    def _modify_response(self, flow):
        if self.state.get("mock_remote_config_backend"):

            if flow.request.path == "/v0.7/config" and str(flow.response.status_code) == "404":
                logger.info(f"Overwriting /v0.7/config response #{self.config_request_count + 1}")
                CONFIG_CONTENTS = [
                    b'{"targets":"eyJzaWduZWQiOnsiX3R5cGUiOiJ0YXJnZXRzIiwic3BlY192ZXJzaW9uIjoiMS4wIiwidmVyc2lvbiI6MSwiZXhwaXJlcyI6IjIwMjItMDktMzBUMTg6NTQ6MjRaIiwidGFyZ2V0cyI6e30sImN1c3RvbSI6eyJvcGFxdWVfYmFja2VuZF9zdGF0ZSI6eyJmb28iOiJiYXIifX19LCJzaWduYXR1cmVzIjpbeyJrZXlpZCI6ImVkNzY3MmM5YTI0YWJkYTc4ODcyZWUzMmVlNzFjN2NiMWQ1MjM1ZThkYjRlY2JmMWNhMjhiOWM1MGViNzVkOWUiLCJzaWciOiJjNzRhZDZhMDdkNjA5MjM0ZGU5OTQwNGRlMTRkN2YyOGE5YzJmZTM1YTE1MDkyYmJlOTIyODAyMGY3ZmMwMGRmNDE5YzczZDk5YTgyZWMwMzZkNTM1YWJjNzRkNTRkNmVlMTQ1MjNlZTdhNDk1YTI0M2I0Y2E0ZTg0Zjg4OTIwNCJ9XX0="}',
                    b'{"targets":"eyJzaWduZWQiOnsiX3R5cGUiOiJ0YXJnZXRzIiwic3BlY192ZXJzaW9uIjoiMS4wIiwidmVyc2lvbiI6MiwiZXhwaXJlcyI6IjIwMjItMDktMzBUMTg6NTQ6MjRaIiwidGFyZ2V0cyI6eyJkYXRhZG9nLzIvTElWRV9ERUJVR0dJTkcvbGQxL2NvbmZpZyI6eyJsZW5ndGgiOjgyNiwiaGFzaGVzIjp7InNoYTI1NiI6ImEzODY3NTBjY2QwOGZjODg5MzdhM2NjYTgyMjM5NjRkYWM5MmE3NWU5MzA3MzMzYzVhYTgyMDdjZjEzYmIyYWIifSwiY3VzdG9tIjp7InYiOjF9fX0sImN1c3RvbSI6eyJvcGFxdWVfYmFja2VuZF9zdGF0ZSI6eyJmb28iOiJiYXIifX19LCJzaWduYXR1cmVzIjpbeyJrZXlpZCI6ImVkNzY3MmM5YTI0YWJkYTc4ODcyZWUzMmVlNzFjN2NiMWQ1MjM1ZThkYjRlY2JmMWNhMjhiOWM1MGViNzVkOWUiLCJzaWciOiIxNmY3MjIzZDA4M2EwYzNjZmMwODlmOGU2ZGRjNzVjMjhhNjViZmNhNTc2NWI1ZDk3OWY1YzA3NTM4NWMxZWVmMTNlZGJhYmYxMGNkNDcxMWNkZWM1ZjI4YWZmZTAzMmQzZmExY2QwYmRmMTViNTRkM2JjMjNjOTQxZWUzY2YwNCJ9XX0=","target_files":[{"path":"datadog/2/LIVE_DEBUGGING/ld1/config","raw":"eyJpZCI6InBldGNsaW5pYyIsIm9yZ0lkIjoyLCJzbmFwc2hvdFByb2JlcyI6W3siaWQiOiIyMjk1M2M4OC1lYWRjLTRmOWEtYWEwZi03ZjYyNDNmNGJmOGEiLCJ0eXBlIjoic25hcHNob3QiLCJjcmVhdGVkIjoxNjA1MDkzMDcxLCJsYW5ndWFnZSI6ImphdmEiLCJ0YWdzIjpbXSwiYWN0aXZlIjp0cnVlLCJ3aGVyZSI6eyJ0eXBlTmFtZSI6ImNvbS5kYXRhZG9nLlRhcmdldCIsIm1ldGhvZE5hbWUiOiJteU1ldGhvZCIsInNpZ25hdHVyZSI6ImphdmEubGFuZy5TdHJpbmcgKCkifX1dLCJtZXRyaWNQcm9iZXMiOlt7ImlkIjoiMzNhNjRkOTktZmJlZC01ZWFiLWJiMTAtODA3MzU0MDVjMDliIiwidHlwZSI6Im1ldHJpYyIsImNyZWF0ZWQiOjE2MDUwOTMwNzEsImxhbmd1YWdlIjoiamF2YSIsInRhZ3MiOltdLCJhY3RpdmUiOnRydWUsIndoZXJlIjp7InR5cGVOYW1lIjoiY29tLmRhdGFkb2cuVGFyZ2V0IiwibWV0aG9kTmFtZSI6Im15TWV0aG9kIiwic2lnbmF0dXJlIjoiamF2YS5sYW5nLlN0cmluZyAoKSJ9LCJraW5kIjoiQ09VTlQiLCJtZXRyaWNOYW1lIjoiZGF0YWRvZy5kZWJ1Z2dlci5jYWxscyIsInZhbHVlIjp7ImV4cHIiOiIjbG9jYWxWYXIxLmZpZWxkMS5maWVsZDIifX1dLCJhbGxvd0xpc3QiOnsicGFja2FnZVByZWZpeGVzIjpbImphdmEubGFuZyJdLCJjbGFzc2VzIjpbImphdmEubGFuZy51dGlsLk1hcCJdfSwiZGVueUxpc3QiOnsicGFja2FnZVByZWZpeGVzIjpbImphdmEuc2VjdXJpdHkiXSwiY2xhc3NlcyI6WyJqYXZheC5zZWN1cml0eS5hdXRoLkF1dGhQZXJtaXNzaW9uIl19LCJzYW1wbGluZyI6eyJzbmFwc2hvdHNQZXJTZWNvbmQiOjF9fQ=="}],"client_configs":["datadog/2/LIVE_DEBUGGING/ld1/config"]}',
                    b'{"targets":"eyJzaWduZWQiOnsiX3R5cGUiOiJ0YXJnZXRzIiwic3BlY192ZXJzaW9uIjoiMS4wIiwidmVyc2lvbiI6MywiZXhwaXJlcyI6IjIwMjItMDktMzBUMTg6NTQ6MjRaIiwidGFyZ2V0cyI6eyJkYXRhZG9nLzIvTElWRV9ERUJVR0dJTkcvbGQxL2NvbmZpZyI6eyJsZW5ndGgiOjgyMiwiaGFzaGVzIjp7InNoYTI1NiI6ImVlOTU1MzBhNWUyMjI1ZTQ0MmEzODUwNTQwYWFjZjM1ZTgzOGI3ZDU3OTc1N2ZhZjlmYWJkNzgyZGE3N2VjOGYifSwiY3VzdG9tIjp7InYiOjJ9fX0sImN1c3RvbSI6eyJvcGFxdWVfYmFja2VuZF9zdGF0ZSI6eyJmb28iOiJiYXIifX19LCJzaWduYXR1cmVzIjpbeyJrZXlpZCI6ImVkNzY3MmM5YTI0YWJkYTc4ODcyZWUzMmVlNzFjN2NiMWQ1MjM1ZThkYjRlY2JmMWNhMjhiOWM1MGViNzVkOWUiLCJzaWciOiI1ZWRhMWM4MzQ2Mjk4OWY0M2RkZGFmOGE4MDkyODdiZGI2MzViZWE4ZmFkYTI2ODMwZGI2MDU4MjM3OTVhODYxNDgyNzg0YTMyZTEwYzgyYjA1M2I1NTA0OTU3NzlhYWY4M2E1MDRlNDA1YTBmMzE5MTI4NDY1MmQyOTUyYjYwNSJ9XX0=","target_files":[{"path":"datadog/2/LIVE_DEBUGGING/ld1/config","raw":"eyJpZCI6Im5ld0lEIiwib3JnSWQiOjIsInNuYXBzaG90UHJvYmVzIjpbeyJpZCI6IjIyOTUzYzg4LWVhZGMtNGY5YS1hYTBmLTdmNjI0M2Y0YmY4YSIsInR5cGUiOiJzbmFwc2hvdCIsImNyZWF0ZWQiOjE2MDUwOTMwNzEsImxhbmd1YWdlIjoiamF2YSIsInRhZ3MiOltdLCJhY3RpdmUiOnRydWUsIndoZXJlIjp7InR5cGVOYW1lIjoiY29tLmRhdGFkb2cuVGFyZ2V0IiwibWV0aG9kTmFtZSI6Im15TWV0aG9kIiwic2lnbmF0dXJlIjoiamF2YS5sYW5nLlN0cmluZyAoKSJ9fV0sIm1ldHJpY1Byb2JlcyI6W3siaWQiOiIzM2E2NGQ5OS1mYmVkLTVlYWItYmIxMC04MDczNTQwNWMwOWIiLCJ0eXBlIjoibWV0cmljIiwiY3JlYXRlZCI6MTYwNTA5MzA3MSwibGFuZ3VhZ2UiOiJqYXZhIiwidGFncyI6W10sImFjdGl2ZSI6dHJ1ZSwid2hlcmUiOnsidHlwZU5hbWUiOiJjb20uZGF0YWRvZy5UYXJnZXQiLCJtZXRob2ROYW1lIjoibXlNZXRob2QiLCJzaWduYXR1cmUiOiJqYXZhLmxhbmcuU3RyaW5nICgpIn0sImtpbmQiOiJDT1VOVCIsIm1ldHJpY05hbWUiOiJkYXRhZG9nLmRlYnVnZ2VyLmNhbGxzIiwidmFsdWUiOnsiZXhwciI6IiNsb2NhbFZhcjEuZmllbGQxLmZpZWxkMiJ9fV0sImFsbG93TGlzdCI6eyJwYWNrYWdlUHJlZml4ZXMiOlsiamF2YS5sYW5nIl0sImNsYXNzZXMiOlsiamF2YS5sYW5nLnV0aWwuTWFwIl19LCJkZW55TGlzdCI6eyJwYWNrYWdlUHJlZml4ZXMiOlsiamF2YS5zZWN1cml0eSJdLCJjbGFzc2VzIjpbImphdmF4LnNlY3VyaXR5LmF1dGguQXV0aFBlcm1pc3Npb24iXX0sInNhbXBsaW5nIjp7InNuYXBzaG90c1BlclNlY29uZCI6MX19"}],"client_configs":["datadog/2/LIVE_DEBUGGING/ld1/config"]}',
                    b'{"targets":"eyJzaWduZWQiOnsiX3R5cGUiOiJ0YXJnZXRzIiwic3BlY192ZXJzaW9uIjoiMS4wIiwidmVyc2lvbiI6NCwiZXhwaXJlcyI6IjIwMjItMDktMzBUMTg6NTQ6MjRaIiwidGFyZ2V0cyI6eyJkYXRhZG9nLzIvTElWRV9ERUJVR0dJTkcvbGQxL2NvbmZpZyI6eyJsZW5ndGgiOjgyMiwiaGFzaGVzIjp7InNoYTI1NiI6ImVlOTU1MzBhNWUyMjI1ZTQ0MmEzODUwNTQwYWFjZjM1ZTgzOGI3ZDU3OTc1N2ZhZjlmYWJkNzgyZGE3N2VjOGYifSwiY3VzdG9tIjp7InYiOjJ9fSwiZGF0YWRvZy8yL0xJVkVfREVCVUdHSU5HL2xkMi9jb25maWciOnsibGVuZ3RoIjo4MjYsImhhc2hlcyI6eyJzaGEyNTYiOiJhMzg2NzUwY2NkMDhmYzg4OTM3YTNjY2E4MjIzOTY0ZGFjOTJhNzVlOTMwNzMzM2M1YWE4MjA3Y2YxM2JiMmFiIn0sImN1c3RvbSI6eyJ2IjoxfX19LCJjdXN0b20iOnsib3BhcXVlX2JhY2tlbmRfc3RhdGUiOnsiZm9vIjoiYmFyIn19fSwic2lnbmF0dXJlcyI6W3sia2V5aWQiOiJlZDc2NzJjOWEyNGFiZGE3ODg3MmVlMzJlZTcxYzdjYjFkNTIzNWU4ZGI0ZWNiZjFjYTI4YjljNTBlYjc1ZDllIiwic2lnIjoiZWUxZGU2MTgzZWE0YTFkYWNiOWZhNzU5Njk2MTZiYzI5NmMyMTU5MWNhOGIwMzJhNjlhMjI3MjYzY2Y5MmRkODU5ZjA1NjQ5ZmI0MzA2NTU1NTA0MWM3MWJhMGU2NjIxYTk5NWE5NDNlNTQ2YmE1NWUwODQzZTFlZDQ1ZjQ5MGYifV19","target_files":[{"path":"datadog/2/LIVE_DEBUGGING/ld2/config","raw":"eyJpZCI6InBldGNsaW5pYyIsIm9yZ0lkIjoyLCJzbmFwc2hvdFByb2JlcyI6W3siaWQiOiIyMjk1M2M4OC1lYWRjLTRmOWEtYWEwZi03ZjYyNDNmNGJmOGEiLCJ0eXBlIjoic25hcHNob3QiLCJjcmVhdGVkIjoxNjA1MDkzMDcxLCJsYW5ndWFnZSI6ImphdmEiLCJ0YWdzIjpbXSwiYWN0aXZlIjp0cnVlLCJ3aGVyZSI6eyJ0eXBlTmFtZSI6ImNvbS5kYXRhZG9nLlRhcmdldCIsIm1ldGhvZE5hbWUiOiJteU1ldGhvZCIsInNpZ25hdHVyZSI6ImphdmEubGFuZy5TdHJpbmcgKCkifX1dLCJtZXRyaWNQcm9iZXMiOlt7ImlkIjoiMzNhNjRkOTktZmJlZC01ZWFiLWJiMTAtODA3MzU0MDVjMDliIiwidHlwZSI6Im1ldHJpYyIsImNyZWF0ZWQiOjE2MDUwOTMwNzEsImxhbmd1YWdlIjoiamF2YSIsInRhZ3MiOltdLCJhY3RpdmUiOnRydWUsIndoZXJlIjp7InR5cGVOYW1lIjoiY29tLmRhdGFkb2cuVGFyZ2V0IiwibWV0aG9kTmFtZSI6Im15TWV0aG9kIiwic2lnbmF0dXJlIjoiamF2YS5sYW5nLlN0cmluZyAoKSJ9LCJraW5kIjoiQ09VTlQiLCJtZXRyaWNOYW1lIjoiZGF0YWRvZy5kZWJ1Z2dlci5jYWxscyIsInZhbHVlIjp7ImV4cHIiOiIjbG9jYWxWYXIxLmZpZWxkMS5maWVsZDIifX1dLCJhbGxvd0xpc3QiOnsicGFja2FnZVByZWZpeGVzIjpbImphdmEubGFuZyJdLCJjbGFzc2VzIjpbImphdmEubGFuZy51dGlsLk1hcCJdfSwiZGVueUxpc3QiOnsicGFja2FnZVByZWZpeGVzIjpbImphdmEuc2VjdXJpdHkiXSwiY2xhc3NlcyI6WyJqYXZheC5zZWN1cml0eS5hdXRoLkF1dGhQZXJtaXNzaW9uIl19LCJzYW1wbGluZyI6eyJzbmFwc2hvdHNQZXJTZWNvbmQiOjF9fQ=="}],"client_configs":["datadog/2/LIVE_DEBUGGING/ld1/config","datadog/2/LIVE_DEBUGGING/ld2/config"]}',
                    b'{"targets":"eyJzaWduZWQiOnsiX3R5cGUiOiJ0YXJnZXRzIiwic3BlY192ZXJzaW9uIjoiMS4wIiwidmVyc2lvbiI6NSwiZXhwaXJlcyI6IjIwMjItMDktMzBUMTg6NTQ6MjRaIiwidGFyZ2V0cyI6eyJkYXRhZG9nLzIvTElWRV9ERUJVR0dJTkcvbGQyL2NvbmZpZyI6eyJsZW5ndGgiOjgyNiwiaGFzaGVzIjp7InNoYTI1NiI6ImEzODY3NTBjY2QwOGZjODg5MzdhM2NjYTgyMjM5NjRkYWM5MmE3NWU5MzA3MzMzYzVhYTgyMDdjZjEzYmIyYWIifSwiY3VzdG9tIjp7InYiOjF9fX0sImN1c3RvbSI6eyJvcGFxdWVfYmFja2VuZF9zdGF0ZSI6eyJmb28iOiJiYXIifX19LCJzaWduYXR1cmVzIjpbeyJrZXlpZCI6ImVkNzY3MmM5YTI0YWJkYTc4ODcyZWUzMmVlNzFjN2NiMWQ1MjM1ZThkYjRlY2JmMWNhMjhiOWM1MGViNzVkOWUiLCJzaWciOiIzMTRlOGY5YmI3N2I2ZGE0OTNmZjc2YTNmMzE1NGZhMGY5N2I2YzcyMzg0YWM3MWQzMTFjOTY4NTUwMTViN2QwMjYxMGNmZjIzZjYyODVlYTg5ODViOGI4YjJlZjQ2NzllMTEwYjVhOGFkODUwYzc5YTgzZjQ5Y2I2ZjMzOTkwMyJ9XX0=","client_configs":["datadog/2/LIVE_DEBUGGING/ld2/config"]}',
                    b'{"targets":"eyJzaWduZWQiOnsiX3R5cGUiOiJ0YXJnZXRzIiwic3BlY192ZXJzaW9uIjoiMS4wIiwidmVyc2lvbiI6NiwiZXhwaXJlcyI6IjIwMjItMDktMzBUMTg6NTQ6MjRaIiwidGFyZ2V0cyI6eyJkYXRhZG9nLzIvTElWRV9ERUJVR0dJTkcvbGQyL2NvbmZpZyI6eyJsZW5ndGgiOjgyNiwiaGFzaGVzIjp7InNoYTI1NiI6ImEzODY3NTBjY2QwOGZjODg5MzdhM2NjYTgyMjM5NjRkYWM5MmE3NWU5MzA3MzMzYzVhYTgyMDdjZjEzYmIyYWIifSwiY3VzdG9tIjp7InYiOjF9fSwiZGF0YWRvZy8yL0xJVkVfREVCVUdHSU5HL2xkZXh0cmEvY29uZmlnIjp7Imxlbmd0aCI6ODczLCJoYXNoZXMiOnsic2hhMjU2IjoiNjZkMGRmOGRiN2Q4NWY3N2NjNmMyMDViYTk3YjM1NGQyNTFjYjJmYWI2MzYyZjgyZDBjNDgyYzkwYWE0ZWQ1OCJ9LCJjdXN0b20iOnsidiI6MX19fSwiY3VzdG9tIjp7Im9wYXF1ZV9iYWNrZW5kX3N0YXRlIjp7ImZvbyI6ImJhciJ9fX0sInNpZ25hdHVyZXMiOlt7ImtleWlkIjoiZWQ3NjcyYzlhMjRhYmRhNzg4NzJlZTMyZWU3MWM3Y2IxZDUyMzVlOGRiNGVjYmYxY2EyOGI5YzUwZWI3NWQ5ZSIsInNpZyI6ImU1MWQ5MjJmYjAyMzcxYjcyMDM4Mzk4OWJmODA3M2I0Njc3MjExYzIwODA5MWExYmQ2YWE5OTllMjc2MjJlZTFiMWIxMzQyY2ZkOTRiZGM2YmY4NWU5MWFlN2ExOGU2OTY0NTFjZmZlOTllNjI4OTgzOWY3NDY0YzY3YjAzODAzIn1dfQ==","target_files":[{"path":"datadog/2/LIVE_DEBUGGING/ldextra/config","raw":"eyJvaG5vZXh0cmFmaWVsZCI6ImlzaG91bGRiZWlnbm9yZWR3aXRobm9lcnJvciIsImlkIjoicGV0Y2xpbmljIiwib3JnSWQiOjIsInNuYXBzaG90UHJvYmVzIjpbeyJpZCI6IjIyOTUzYzg4LWVhZGMtNGY5YS1hYTBmLTdmNjI0M2Y0YmY4YSIsInR5cGUiOiJzbmFwc2hvdCIsImNyZWF0ZWQiOjE2MDUwOTMwNzEsImxhbmd1YWdlIjoiamF2YSIsInRhZ3MiOltdLCJhY3RpdmUiOnRydWUsIndoZXJlIjp7InR5cGVOYW1lIjoiY29tLmRhdGFkb2cuVGFyZ2V0IiwibWV0aG9kTmFtZSI6Im15TWV0aG9kIiwic2lnbmF0dXJlIjoiamF2YS5sYW5nLlN0cmluZyAoKSJ9fV0sIm1ldHJpY1Byb2JlcyI6W3siaWQiOiIzM2E2NGQ5OS1mYmVkLTVlYWItYmIxMC04MDczNTQwNWMwOWIiLCJ0eXBlIjoibWV0cmljIiwiY3JlYXRlZCI6MTYwNTA5MzA3MSwibGFuZ3VhZ2UiOiJqYXZhIiwidGFncyI6W10sImFjdGl2ZSI6dHJ1ZSwid2hlcmUiOnsidHlwZU5hbWUiOiJjb20uZGF0YWRvZy5UYXJnZXQiLCJtZXRob2ROYW1lIjoibXlNZXRob2QiLCJzaWduYXR1cmUiOiJqYXZhLmxhbmcuU3RyaW5nICgpIn0sImtpbmQiOiJDT1VOVCIsIm1ldHJpY05hbWUiOiJkYXRhZG9nLmRlYnVnZ2VyLmNhbGxzIiwidmFsdWUiOnsiZXhwciI6IiNsb2NhbFZhcjEuZmllbGQxLmZpZWxkMiJ9fV0sImFsbG93TGlzdCI6eyJwYWNrYWdlUHJlZml4ZXMiOlsiamF2YS5sYW5nIl0sImNsYXNzZXMiOlsiamF2YS5sYW5nLnV0aWwuTWFwIl19LCJkZW55TGlzdCI6eyJwYWNrYWdlUHJlZml4ZXMiOlsiamF2YS5zZWN1cml0eSJdLCJjbGFzc2VzIjpbImphdmF4LnNlY3VyaXR5LmF1dGguQXV0aFBlcm1pc3Npb24iXX0sInNhbXBsaW5nIjp7InNuYXBzaG90c1BlclNlY29uZCI6MX19"}],"client_configs":["datadog/2/LIVE_DEBUGGING/ldextra/config","datadog/2/LIVE_DEBUGGING/ld2/config"]}',
                    b'{"targets":"eyJzaWduZWQiOnsiX3R5cGUiOiJ0YXJnZXRzIiwic3BlY192ZXJzaW9uIjoiMS4wIiwidmVyc2lvbiI6NywiZXhwaXJlcyI6IjIwMjItMDktMzBUMTg6NTQ6MjRaIiwidGFyZ2V0cyI6eyJkYXRhZG9nLzIvTElWRV9ERUJVR0dJTkcvbGQyL2NvbmZpZyI6eyJsZW5ndGgiOjgyNiwiaGFzaGVzIjp7InNoYTI1NiI6ImEzODY3NTBjY2QwOGZjODg5MzdhM2NjYTgyMjM5NjRkYWM5MmE3NWU5MzA3MzMzYzVhYTgyMDdjZjEzYmIyYWIifSwiY3VzdG9tIjp7InYiOjF9fSwiZGF0YWRvZy8yL0xJVkVfREVCVUdHSU5HL2xkZXh0cmEvY29uZmlnIjp7Imxlbmd0aCI6ODczLCJoYXNoZXMiOnsic2hhMjU2IjoiNjZkMGRmOGRiN2Q4NWY3N2NjNmMyMDViYTk3YjM1NGQyNTFjYjJmYWI2MzYyZjgyZDBjNDgyYzkwYWE0ZWQ1OCJ9LCJjdXN0b20iOnsidiI6MX19LCJkYXRhZG9nLzIvTElWRV9ERUJVR0dJTkcvbGRtaXNzaW5nL2NvbmZpZyI6eyJsZW5ndGgiOjgzMywiaGFzaGVzIjp7InNoYTI1NiI6ImQ1ZDE3ZDBkZGQzODNiNzYyYmI3NzBjN2UyNmVjM2E0MTQ5NDAxNTQ3MzQ1YTVjNzRjN2NmNmVlOTc3OGVlZjAifSwiY3VzdG9tIjp7InYiOjF9fX0sImN1c3RvbSI6eyJvcGFxdWVfYmFja2VuZF9zdGF0ZSI6eyJmb28iOiJiYXIifX19LCJzaWduYXR1cmVzIjpbeyJrZXlpZCI6ImVkNzY3MmM5YTI0YWJkYTc4ODcyZWUzMmVlNzFjN2NiMWQ1MjM1ZThkYjRlY2JmMWNhMjhiOWM1MGViNzVkOWUiLCJzaWciOiJhYmQ3NTQ4OTRiZmY1MzE4YzBlODk2N2QxN2NkMGNjMmViNWJmMjYzMWRkM2Q3NzY3ZDYzZWJjN2MwZmU4OTAyMWI5Mjk3MjkwNWY0YmNmNjllYmNiNzlkNWFiNjk3N2NhMjRiZTQwOWIzNzQwMmE5OWFmNWViMjkyNzhkOWUwMSJ9XX0=","client_configs":["datadog/2/LIVE_DEBUGGING/ld2/config","datadog/2/LIVE_DEBUGGING/ldextra/config","datadog/2/LIVE_DEBUGGING/ldmissing/config"]}',
                    b'{"targets":"eyJzaWduZWQiOnsiX3R5cGUiOiJ0YXJnZXRzIiwic3BlY192ZXJzaW9uIjoiMS4wIiwidmVyc2lvbiI6NywiZXhwaXJlcyI6IjIwMjItMDktMzBUMTg6NTQ6MjRaIiwidGFyZ2V0cyI6eyJkYXRhZG9nLzIvTElWRV9ERUJVR0dJTkcvbGQyL2NvbmZpZyI6eyJsZW5ndGgiOjgyNiwiaGFzaGVzIjp7InNoYTI1NiI6ImEzODY3NTBjY2QwOGZjODg5MzdhM2NjYTgyMjM5NjRkYWM5MmE3NWU5MzA3MzMzYzVhYTgyMDdjZjEzYmIyYWIifSwiY3VzdG9tIjp7InYiOjF9fSwiZGF0YWRvZy8yL0xJVkVfREVCVUdHSU5HL2xkZXh0cmEvY29uZmlnIjp7Imxlbmd0aCI6ODczLCJoYXNoZXMiOnsic2hhMjU2IjoiNjZkMGRmOGRiN2Q4NWY3N2NjNmMyMDViYTk3YjM1NGQyNTFjYjJmYWI2MzYyZjgyZDBjNDgyYzkwYWE0ZWQ1OCJ9LCJjdXN0b20iOnsidiI6MX19fSwiY3VzdG9tIjp7Im9wYXF1ZV9iYWNrZW5kX3N0YXRlIjp7ImZvbyI6ImJhciJ9fX0sInNpZ25hdHVyZXMiOlt7ImtleWlkIjoiZWQ3NjcyYzlhMjRhYmRhNzg4NzJlZTMyZWU3MWM3Y2IxZDUyMzVlOGRiNGVjYmYxY2EyOGI5YzUwZWI3NWQ5ZSIsInNpZyI6IjlmZWU0MTA0OThhMmIyZWZkOGUxOGJjMTVhNTFmZjEyYjdkYmFhMDA1Njk5ZDk0YzM4MTZjMzY4NGEwYTIyYTYwODYxN2FhZjc3ZDM0ZjkwNTE2ODQ0MzgyZjI0MDk0NmFhYzYwMzVmYTAyNTIyM2EwZGMxZjE0NjVkYWVkNTA4In1dfQ==","client_configs":["datadog/2/LIVE_DEBUGGING/ldextra/config","datadog/2/LIVE_DEBUGGING/ld2/config"]}',
                    b'{"targets":"eyJzaWduZWQiOnsiX3R5cGUiOiJ0YXJnZXRzIiwic3BlY192ZXJzaW9uIjoiMS4wIiwidmVyc2lvbiI6OCwiZXhwaXJlcyI6IjIwMjItMDktMzBUMTg6NTQ6MjRaIiwidGFyZ2V0cyI6eyJkYXRhZG9nLzIvTElWRV9ERUJVR0dJTkcvbGQyL2NvbmZpZyI6eyJsZW5ndGgiOjgyNiwiaGFzaGVzIjp7InNoYTI1NiI6ImEzODY3NTBjY2QwOGZjODg5MzdhM2NjYTgyMjM5NjRkYWM5MmE3NWU5MzA3MzMzYzVhYTgyMDdjZjEzYmIyYWIifSwiY3VzdG9tIjp7InYiOjF9fSwiZGF0YWRvZy8yL0xJVkVfREVCVUdHSU5HL2xkZXh0cmEvY29uZmlnIjp7Imxlbmd0aCI6ODczLCJoYXNoZXMiOnsic2hhMjU2IjoiNjZkMGRmOGRiN2Q4NWY3N2NjNmMyMDViYTk3YjM1NGQyNTFjYjJmYWI2MzYyZjgyZDBjNDgyYzkwYWE0ZWQ1OCJ9LCJjdXN0b20iOnsidiI6MX19LCJkYXRhZG9nLzIvTElWRV9ERUJVR0dJTkcveWV0YW5vdGhlcmxkZmlsZS9jb25maWciOnsibGVuZ3RoIjo4MzMsImhhc2hlcyI6eyJzaGEyNTYiOiJhMTRlNzljMzhhMjJlYTY4ODYyMjAzZDRkNjI5NGQwMjg2M2YyZGY5MmZjMTRiZTBkNDYwMmZmYTcyNTNlMTcxIn0sImN1c3RvbSI6eyJ2IjoxfX19LCJjdXN0b20iOnsib3BhcXVlX2JhY2tlbmRfc3RhdGUiOnsiZm9vIjoiYmFyIn19fSwic2lnbmF0dXJlcyI6W3sia2V5aWQiOiJlZDc2NzJjOWEyNGFiZGE3ODg3MmVlMzJlZTcxYzdjYjFkNTIzNWU4ZGI0ZWNiZjFjYTI4YjljNTBlYjc1ZDllIiwic2lnIjoiYjU1ZjUzYWRjNjM2NGIzMWUwZmRlNTY1MmFkOWJjMTc5OTJmYmM5MTk0YTJlMmZjYzI4ZWZlOGJmNTFkMzc4YTYxYzc5OTExODdiZjBlZGFmMGU4Y2FkNTUxMDM3YmM0YmM5YTgwNzJmMmEwZWQ0ZTU1N2YxMzc1M2M2YjMyMGEifV19","target_files":[{"path":"datadog/2/LIVE_DEBUGGING/yetanotherldfile/config","raw":"eyJpZCI6InlldGFub3RoZXJsZGZpbGUiLCJvcmdJZCI6Miwic25hcHNob3RQcm9iZXMiOlt7ImlkIjoiMjI5NTNjODgtZWFkYy00ZjlhLWFhMGYtN2Y2MjQzZjRiZjhhIiwidHlwZSI6InNuYXBzaG90IiwiY3JlYXRlZCI6MTYwNTA5MzA3MSwibGFuZ3VhZ2UiOiJqYXZhIiwidGFncyI6W10sImFjdGl2ZSI6dHJ1ZSwid2hlcmUiOnsidHlwZU5hbWUiOiJjb20uZGF0YWRvZy5UYXJnZXQiLCJtZXRob2ROYW1lIjoibXlNZXRob2QiLCJzaWduYXR1cmUiOiJqYXZhLmxhbmcuU3RyaW5nICgpIn19XSwibWV0cmljUHJvYmVzIjpbeyJpZCI6IjMzYTY0ZDk5LWZiZWQtNWVhYi1iYjEwLTgwNzM1NDA1YzA5YiIsInR5cGUiOiJtZXRyaWMiLCJjcmVhdGVkIjoxNjA1MDkzMDcxLCJsYW5ndWFnZSI6ImphdmEiLCJ0YWdzIjpbXSwiYWN0aXZlIjp0cnVlLCJ3aGVyZSI6eyJ0eXBlTmFtZSI6ImNvbS5kYXRhZG9nLlRhcmdldCIsIm1ldGhvZE5hbWUiOiJteU1ldGhvZCIsInNpZ25hdHVyZSI6ImphdmEubGFuZy5TdHJpbmcgKCkifSwia2luZCI6IkNPVU5UIiwibWV0cmljTmFtZSI6ImRhdGFkb2cuZGVidWdnZXIuY2FsbHMiLCJ2YWx1ZSI6eyJleHByIjoiI2xvY2FsVmFyMS5maWVsZDEuZmllbGQyIn19XSwiYWxsb3dMaXN0Ijp7InBhY2thZ2VQcmVmaXhlcyI6WyJqYXZhLmxhbmciXSwiY2xhc3NlcyI6WyJqYXZhLmxhbmcudXRpbC5NYXAiXX0sImRlbnlMaXN0Ijp7InBhY2thZ2VQcmVmaXhlcyI6WyJqYXZhLnNlY3VyaXR5Il0sImNsYXNzZXMiOlsiamF2YXguc2VjdXJpdHkuYXV0aC5BdXRoUGVybWlzc2lvbiJdfSwic2FtcGxpbmciOnsic25hcHNob3RzUGVyU2Vjb25kIjoxfX0="},{"path":"thisshouldbeignored","raw":"ImFXZHViM0psYldVPSI="}],"client_configs":["datadog/2/LIVE_DEBUGGING/ldextra/config","datadog/2/LIVE_DEBUGGING/ld2/config","datadog/2/LIVE_DEBUGGING/yetanotherldfile/config"]}',
                    b'{"targets":"eyJzaWduZWQiOnsiX3R5cGUiOiJ0YXJnZXRzIiwic3BlY192ZXJzaW9uIjoiMS4wIiwidmVyc2lvbiI6OSwiZXhwaXJlcyI6IjIwMjItMDktMzBUMTg6NTQ6MjRaIiwidGFyZ2V0cyI6eyJkYXRhZG9nLzIvTElWRV9ERUJVR0dJTkcvbGQyL2NvbmZpZyI6eyJsZW5ndGgiOjgyNiwiaGFzaGVzIjp7InNoYTI1NiI6ImEzODY3NTBjY2QwOGZjODg5MzdhM2NjYTgyMjM5NjRkYWM5MmE3NWU5MzA3MzMzYzVhYTgyMDdjZjEzYmIyYWIifSwiY3VzdG9tIjp7InYiOjF9fSwiZGF0YWRvZy8yL0xJVkVfREVCVUdHSU5HL2xkZXh0cmEvY29uZmlnIjp7Imxlbmd0aCI6ODczLCJoYXNoZXMiOnsic2hhMjU2IjoiNjZkMGRmOGRiN2Q4NWY3N2NjNmMyMDViYTk3YjM1NGQyNTFjYjJmYWI2MzYyZjgyZDBjNDgyYzkwYWE0ZWQ1OCJ9LCJjdXN0b20iOnsidiI6MX19LCJkYXRhZG9nLzIvTElWRV9ERUJVR0dJTkcvdGhpc3Nob3VsZGFsc29iZWlnbm9yZWQvY29uZmlnIjp7Imxlbmd0aCI6MTk5NCwiaGFzaGVzIjp7InNoYTI1NiI6ImM4NTI3MGIwMDY5OWUwOTQ1ZGI3OWMwMmM5YjY1NjdjYjk5MWUwN2JhNmMwNmY0NDk5ZDg5MGU1OGYwMjQzMWMifSwiY3VzdG9tIjp7InYiOjF9fSwiZGF0YWRvZy8yL0xJVkVfREVCVUdHSU5HL3lldGFub3RoZXJsZGZpbGUvY29uZmlnIjp7Imxlbmd0aCI6ODMzLCJoYXNoZXMiOnsic2hhMjU2IjoiYTE0ZTc5YzM4YTIyZWE2ODg2MjIwM2Q0ZDYyOTRkMDI4NjNmMmRmOTJmYzE0YmUwZDQ2MDJmZmE3MjUzZTE3MSJ9LCJjdXN0b20iOnsidiI6MX19fSwiY3VzdG9tIjp7Im9wYXF1ZV9iYWNrZW5kX3N0YXRlIjp7ImZvbyI6ImJhciJ9fX0sInNpZ25hdHVyZXMiOlt7ImtleWlkIjoiZWQ3NjcyYzlhMjRhYmRhNzg4NzJlZTMyZWU3MWM3Y2IxZDUyMzVlOGRiNGVjYmYxY2EyOGI5YzUwZWI3NWQ5ZSIsInNpZyI6ImZjMTg0ODI2ODE0YTkxZDM5ZTM3YjM4ZjVkMmNmODI0YTUzMDEwM2FhNWRjNjdmZjQ3Y2M4ZDgzZTgxZTJlZjdjZDQxMWJkODMzM2IwNjM4ZWI0MDM5ZmRkZDE2Yzc1MmVlZTk1YzliN2UyNTIxNTAzZDZhOGVlMmIyN2QzMzBjIn1dfQ==","client_configs":["datadog/2/LIVE_DEBUGGING/ldextra/config","datadog/2/LIVE_DEBUGGING/ld2/config","datadog/2/LIVE_DEBUGGING/yetanotherldfile/config"]}',
                    b'{"targets":"eyJzaWduZWQiOnsiX3R5cGUiOiJ0YXJnZXRzIiwic3BlY192ZXJzaW9uIjoiMS4wIiwidmVyc2lvbiI6MTAsImV4cGlyZXMiOiIyMDIyLTA5LTMwVDE4OjU0OjI0WiIsInRhcmdldHMiOnsiZGF0YWRvZy8yL0xJVkVfREVCVUdHSU5HL2xkMi9jb25maWciOnsibGVuZ3RoIjo4MjYsImhhc2hlcyI6eyJzaGEyNTYiOiJhMzg2NzUwY2NkMDhmYzg4OTM3YTNjY2E4MjIzOTY0ZGFjOTJhNzVlOTMwNzMzM2M1YWE4MjA3Y2YxM2JiMmFiIn0sImN1c3RvbSI6eyJ2IjoxfX0sImRhdGFkb2cvMi9MSVZFX0RFQlVHR0lORy9sZGV4dHJhL2NvbmZpZyI6eyJsZW5ndGgiOjg3MywiaGFzaGVzIjp7InNoYTI1NiI6IjY2ZDBkZjhkYjdkODVmNzdjYzZjMjA1YmE5N2IzNTRkMjUxY2IyZmFiNjM2MmY4MmQwYzQ4MmM5MGFhNGVkNTgifSwiY3VzdG9tIjp7InYiOjF9fSwiZGF0YWRvZy8yL0xJVkVfREVCVUdHSU5HL3RoaXNzaG91bGRhbHNvYmVpZ25vcmVkL2NvbmZpZyI6eyJsZW5ndGgiOjE5OTQsImhhc2hlcyI6eyJzaGEyNTYiOiJjODUyNzBiMDA2OTllMDk0NWRiNzljMDJjOWI2NTY3Y2I5OTFlMDdiYTZjMDZmNDQ5OWQ4OTBlNThmMDI0MzFjIn0sImN1c3RvbSI6eyJ2IjoxfX0sImRhdGFkb2cvMi9MSVZFX0RFQlVHR0lORy95ZXRhbm90aGVybGRmaWxlL2NvbmZpZyI6eyJsZW5ndGgiOjgzMywiaGFzaGVzIjp7InNoYTI1NiI6ImExNGU3OWMzOGEyMmVhNjg4NjIyMDNkNGQ2Mjk0ZDAyODYzZjJkZjkyZmMxNGJlMGQ0NjAyZmZhNzI1M2UxNzEifSwiY3VzdG9tIjp7InYiOjF9fX0sImN1c3RvbSI6eyJvcGFxdWVfYmFja2VuZF9zdGF0ZSI6eyJmb28iOiJiYXIifX19LCJzaWduYXR1cmVzIjpbeyJrZXlpZCI6ImVkNzY3MmM5YTI0YWJkYTc4ODcyZWUzMmVlNzFjN2NiMWQ1MjM1ZThkYjRlY2JmMWNhMjhiOWM1MGViNzVkOWUiLCJzaWciOiIyYTEzMTE4MThhYzgxZDRiYmUyOWI5YTU0NzIwYzY5ZTE3ZjhmODc0NTIxNzA4OWUyOGYxODA3YmI0ZDQzNGU4ZWZmYjQwYmUyN2M2ODM0NDE2ODRmMzE1NjZkYWFhNTlkOGJhZTVmNWQyMzViZTExZDMzNjM0ZjQ5M2IzY2IwNCJ9XX0=","target_files":[{"path":"datadog/2/LIVE_DEBUGGING/thisshouldalsobeignored/config","raw":"ImV3b2dJQ0FnSW1sa0lqb2dJbkJsZEdOc2FXNXBZeUlzQ2lBZ0lDQWliM0puU1dRaU9pQXlMQW9nSUNBZ0luTnVZWEJ6YUc5MFVISnZZbVZ6SWpvZ1d3b2dJQ0FnSUNBZ0lIc0tJQ0FnSUNBZ0lDQWdJQ0FnSW1sa0lqb2dJakl5T1RVell6ZzRMV1ZoWkdNdE5HWTVZUzFoWVRCbUxUZG1OakkwTTJZMFltWTRZU0lzQ2lBZ0lDQWdJQ0FnSUNBZ0lDSjBlWEJsSWpvZ0luTnVZWEJ6YUc5MElpd0tJQ0FnSUNBZ0lDQWdJQ0FnSW1OeVpXRjBaV1FpT2lBeE5qQTFNRGt6TURjeExqQXdNREF3TURBd01Dd0tJQ0FnSUNBZ0lDQWdJQ0FnSW14aGJtZDFZV2RsSWpvZ0ltcGhkbUVpTEFvZ0lDQWdJQ0FnSUNBZ0lDQWlkR0ZuY3lJNklGdGRMQW9nSUNBZ0lDQWdJQ0FnSUNBaVlXTjBhWFpsSWpvZ2RISjFaU3dLSUNBZ0lDQWdJQ0FnSUNBZ0luZG9aWEpsSWpvZ2V3b2dJQ0FnSUNBZ0lDQWdJQ0FnSUNBZ0luUjVjR1ZPWVcxbElqb2dJbU52YlM1a1lYUmhaRzluTGxSaGNtZGxkQ0lzQ2lBZ0lDQWdJQ0FnSUNBZ0lDQWdJQ0FpYldWMGFHOWtUbUZ0WlNJNklDSnRlVTFsZEdodlpDSXNDaUFnSUNBZ0lDQWdJQ0FnSUNBZ0lDQWljMmxuYm1GMGRYSmxJam9nSW1waGRtRXViR0Z1Wnk1VGRISnBibWNnS0NraUNpQWdJQ0FnSUNBZ0lDQWdJSDBLSUNBZ0lDQWdJQ0I5Q2lBZ0lDQmRMQW9nSUNBZ0ltMWxkSEpwWTFCeWIySmxjeUk2SUZzS0lDQWdJQ0FnSUNCN0NpQWdJQ0FnSUNBZ0lDQWdJQ0pwWkNJNklDSXpNMkUyTkdRNU9TMW1ZbVZrTFRWbFlXSXRZbUl4TUMwNE1EY3pOVFF3TldNd09XSWlMQW9nSUNBZ0lDQWdJQ0FnSUNBaWRIbHdaU0k2SUNKdFpYUnlhV01pTEFvZ0lDQWdJQ0FnSUNBZ0lDQWlZM0psWVhSbFpDSTZJREUyTURVd09UTXdOekV1TURBd01EQXdNREF3TEFvZ0lDQWdJQ0FnSUNBZ0lDQWliR0Z1WjNWaFoyVWlPaUFpYW1GMllTSXNDaUFnSUNBZ0lDQWdJQ0FnSUNKMFlXZHpJam9nVzEwc0NpQWdJQ0FnSUNBZ0lDQWdJQ0poWTNScGRtVWlPaUIwY25WbExBb2dJQ0FnSUNBZ0lDQWdJQ0FpZDJobGNtVWlPaUI3Q2lBZ0lDQWdJQ0FnSUNBZ0lDQWdJQ0FpZEhsd1pVNWhiV1VpT2lBaVkyOXRMbVJoZEdGa2IyY3VWR0Z5WjJWMElpd0tJQ0FnSUNBZ0lDQWdJQ0FnSUNBZ0lDSnRaWFJvYjJST1lXMWxJam9nSW0xNVRXVjBhRzlrSWl3S0lDQWdJQ0FnSUNBZ0lDQWdJQ0FnSUNKemFXZHVZWFIxY21VaU9pQWlhbUYyWVM1c1lXNW5MbE4wY21sdVp5QW9LU0lLSUNBZ0lDQWdJQ0FnSUNBZ2ZTd0tJQ0FnSUNBZ0lDQWdJQ0FnSW10cGJtUWlPaUFpUTA5VlRsUWlMQW9nSUNBZ0lDQWdJQ0FnSUNBaWJXVjBjbWxqVG1GdFpTSTZJQ0prWVhSaFpHOW5MbVJsWW5WbloyVnlMbU5oYkd4eklpd0tJQ0FnSUNBZ0lDQWdJQ0FnSW5aaGJIVmxJam9nZXdvZ0lDQWdJQ0FnSUNBZ0lDQWdJQ0FnSW1WNGNISWlPaUFpSTJ4dlkyRnNWbUZ5TVM1bWFXVnNaREV1Wm1sbGJHUXlJZ29nSUNBZ0lDQWdJQ0FnSUNCOUNpQWdJQ0FnSUNBZ2ZRb2dJQ0FnWFN3S0lDQWdJQ0poYkd4dmQweHBjM1FpT2lCN0NpQWdJQ0FnSUNBZ0luQmhZMnRoWjJWUWNtVm1hWGhsY3lJNklGc0tJQ0FnSUNBZ0lDQWdJQ0FnSW1waGRtRXViR0Z1WnlJS0lDQWdJQ0FnSUNCZExBb2dJQ0FnSUNBZ0lDSmpiR0Z6YzJWeklqb2dXd29nSUNBZ0lDQWdJQ0FnSUNBaWFtRjJZUzVzWVc1bkxuVjBhV3d1VFdGd0lnb2dJQ0FnSUNBZ0lGMEtJQ0FnSUgwc0NpQWdJQ0FpWkdWdWVVeHBjM1FpT2lCN0NpQWdJQ0FnSUNBZ0luQmhZMnRoWjJWUWNtVm1hWGhsY3lJNklGc0tJQ0FnSUNBZ0lDQWdJQ0FnSW1waGRtRXVjMlZqZFhKcGRIa2lDaUFnSUNBZ0lDQWdYU3dLSUNBZ0lDQWdJQ0FpWTJ4aGMzTmxjeUk2SUZzS0lDQWdJQ0FnSUNBZ0lDQWdJbXBoZG1GNExuTmxZM1Z5YVhSNUxtRjFkR2d1UVhWMGFGQmxjbTFwYzNOcGIyNGlDaUFnSUNBZ0lDQWdYUW9nSUNBZ2ZTd0tJQ0FnSUNKellXMXdiR2x1WnlJNklIc0tJQ0FnSUNBZ0lDQWljMjVoY0hOb2IzUnpVR1Z5VTJWamIyNWtJam9nTVM0d0NpQWdJQ0I5Q24wPSI="}],"client_configs":["datadog/2/LIVE_DEBUGGING/ldextra/config","datadog/2/LIVE_DEBUGGING/ld2/config","datadog/2/LIVE_DEBUGGING/yetanotherldfile/config"]}',
                ]

                if self.config_request_count + 1 > len(CONFIG_CONTENTS):
                    content = b"{}"  # default content when there isn't an RC update
                else:
                    content = CONFIG_CONTENTS[self.config_request_count]

                flow.response.status_code = 200
                flow.response.content = content

                self.config_request_count += 1


addons = [Forwarder()]
