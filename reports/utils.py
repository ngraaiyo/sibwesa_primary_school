# reports/utils.py
from functools import wraps
from django.http import HttpResponseForbidden

def has_role(user, roles):
    """Check if user has any role in `roles`."""
    if not user.is_authenticated:
        return False
    # If CustomUser has a 'role' attribute
    if hasattr(user, 'role') and user.role in roles:
        return True
    # If using groups
    if user.groups.filter(name__in=roles).exists():
        return True
    # Superuser always allowed
    return user.is_superuser

def role_required(roles):
    """Decorator to restrict view access by role."""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if has_role(request.user, roles):
                return view_func(request, *args, **kwargs)
            return HttpResponseForbidden("You do not have permission to view this page.")
        return _wrapped
    return decorator
