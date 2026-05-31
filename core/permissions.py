from rest_framework.permissions import BasePermission


class _RolePermission(BasePermission):
    required_role = None

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and getattr(request.user, "role", None) == self.required_role)


class IsSaccoAdmin(_RolePermission):
    required_role = "sacco_admin"


class IsRider(_RolePermission):
    required_role = "rider"


class IsSystemAdmin(_RolePermission):
    required_role = "system_admin"


class IsSaccoMember(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        sacco_id = view.kwargs.get("sacco_id") if hasattr(view, "kwargs") else None
        if sacco_id is None and hasattr(request, "data"):
            sacco_id = request.data.get("sacco_id")
        return sacco_id is not None and str(getattr(user, "sacco_id", "")) == str(sacco_id)


class IsPatient(BasePermission):
    def has_permission(self, request, view):
        if request.method == "POST" and request.path.endswith("/api/v1/sos/"):
            return True
        return bool(request.user and request.user.is_authenticated and getattr(request.user, "role", None) == "patient")
