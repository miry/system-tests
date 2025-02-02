from random import randint
import requests


def make_get_request(app_url):
    generated_uuid = str(randint(0, 10000000))
    requests.get(
        app_url, headers={"x-datadog-trace-id": generated_uuid, "x-datadog-parent-id": generated_uuid}, timeout=10
    )
    return generated_uuid
