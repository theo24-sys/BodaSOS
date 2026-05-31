from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler


def custom_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    if response is None:
        return Response(
            {
                "success": False,
                "error": {
                    "code": "SERVER_ERROR",
                    "message": "An unexpected error occurred.",
                    "details": None,
                },
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    code_map = {
        status.HTTP_404_NOT_FOUND: "NOT_FOUND",
        status.HTTP_403_FORBIDDEN: "PERMISSION_DENIED",
        status.HTTP_400_BAD_REQUEST: "VALIDATION_ERROR",
    }
    details = response.data
    message = response.data.get("detail") if isinstance(response.data, dict) else "Request failed."
    if isinstance(response.data, dict):
        details = {key: value for key, value in response.data.items() if key != "detail"}
    response.data = {
        "success": False,
        "error": {
            "code": code_map.get(response.status_code, "SERVER_ERROR"),
            "message": message or "Request failed.",
            "details": details,
        },
    }
    return response
