from django.http import HttpResponseForbidden
from django.contrib.auth.mixins import UserPassesTestMixin,LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from functools import wraps
from django.shortcuts import redirect



def superuser_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('account_login')  # Redirect to login page
        if not request.user.is_superuser:
            raise PermissionDenied("You do not have permission to access this page.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view



def role_required(roles):
    """A decorator to restrict access based on a user's role."""

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('account_login')  # Redirect to login page
            if request.user.role not in roles:
                raise PermissionDenied("You do not have permission to access this page.")
            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator

class StudentRequiredMixin(LoginRequiredMixin,UserPassesTestMixin):
    """A mixin to restrict access based on a user's role."""

    required_roles = ["student"]  # A list of roles, e.g., ['admin', 'tutor']

    def test_func(self):
        # Ensure the user is authenticated and has one of the required roles
        user = self.request.user
        return user.is_authenticated and (user.role in self.required_roles)

    def handle_no_permission(self):
        user = self.request.user
        if not user.is_authenticated:
            return redirect('account_login')  # Redirect to login page
        raise PermissionDenied(f"You do not have permission to access this page.")


class SuperUserRequiredMixin(LoginRequiredMixin,UserPassesTestMixin):
    """A mixin to restrict access to superusers only."""

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_superuser

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            from django.shortcuts import redirect
            return redirect('account_login')  # Redirect to login page
        raise PermissionDenied("You do not have permission to access this page.")





class RoleRequiredMixin(UserPassesTestMixin):
    """
    Mixin to restrict access based on user type (superuser, staff, regular user).
    """
    allow_superuser = False  # Allow superusers by default
    allow_staff = False  # Allow staff members by default
    allow_users = False  # Allow regular users by default

    def test_func(self):
        user = self.request.user
        if not user.is_authenticated:
            return False  # Block unauthenticated users
        if self.allow_superuser and user.is_superuser:
            return True
        if self.allow_staff and user.is_staff:
            return True
        if self.allow_users and not user.is_staff and not user.is_superuser:
            return True
        return False  # Deny access otherwise

    def handle_no_permission(self):
        return HttpResponseForbidden("You are not authorized to view this page.")
