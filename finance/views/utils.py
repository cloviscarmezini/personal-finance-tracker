import json
from django.http import JsonResponse


def is_json_request(request):
    content_type = (request.content_type or "").lower()
    return (
        content_type.startswith("application/json")
        or request.headers.get("X-Requested-With") == "XMLHttpRequest"
    )


def parse_request_payload(request):
    if is_json_request(request):
        try:
            body = request.body.decode("utf-8") if isinstance(request.body, bytes) else request.body
            return json.loads(body) if body else {}
        except json.JSONDecodeError:
            return {}
    return request.POST


def json_success(data, status=200):
    return JsonResponse({"status": "success", "data": data}, status=status)


def json_error(message, errors=None, status=400):
    payload = {"status": "error", "message": message}
    if errors:
        payload["errors"] = errors
    return JsonResponse(payload, status=status)
