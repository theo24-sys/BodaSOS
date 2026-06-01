def show_admin_links(request):
    """Expose whether admin/operator links should be shown in templates.

    Only return True for users who are superusers. Templates can use
    `show_admin_links` to conditionally render any sensitive links.
    """
    try:
        is_operator = bool(request.user and getattr(request.user, "is_superuser", False))
    except Exception:
        is_operator = False
    return {"show_admin_links": is_operator}
