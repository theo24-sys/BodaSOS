from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse


def health_check(request):
    checks = {}
    overall_ok = True

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        checks["postgresql"] = "ok"
    except Exception as exc:  # pragma: no cover - runtime health path
        overall_ok = False
        checks["postgresql"] = f"error: {exc}"

    try:
        if hasattr(cache, "ping"):
            cache_ok = cache.ping()
        else:
            cache.set("health-check", "ok", 5)
            cache_ok = cache.get("health-check") == "ok"
        checks["redis"] = "ok" if cache_ok else "error"
        overall_ok = overall_ok and cache_ok
    except Exception as exc:  # pragma: no cover - runtime health path
        overall_ok = False
        checks["redis"] = f"error: {exc}"

    return JsonResponse({"status": "ok" if overall_ok else "degraded", "checks": checks}, status=200 if overall_ok else 503)
