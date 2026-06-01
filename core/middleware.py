import logging

logger = logging.getLogger("django")

class RequestIDMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response


class SaccoIsolationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user is not None and getattr(user, "is_authenticated", False) and getattr(user, "role", None) == "sacco_admin":
            request.sacco_id = getattr(user, "sacco_id", None)
        return self.get_response(request)


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        user_id = getattr(user, "id", None) if getattr(user, "is_authenticated", False) else None
        response = self.get_response(request)
        logger.info("request method=%s path=%s user_id=%s status_code=%s", request.method, request.path, user_id, getattr(response, "status_code", None))
        return response
