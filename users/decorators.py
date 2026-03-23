from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required


def manager_required(view_func):
    """
    Decorator for views restricted to managers/staff only.
    Must be used together with @login_required (or will redirect unauthenticated users to login).
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.is_manager or request.user.is_staff:
            return view_func(request, *args, **kwargs)
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    return wrapper


def student_required(view_func):
    """
    Decorator for views restricted to students only.
    Redirects unauthenticated users to login; redirects managers to admin dashboard.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.is_manager or request.user.is_staff:
            return redirect('admin_dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper
