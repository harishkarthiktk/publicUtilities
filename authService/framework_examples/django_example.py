"""
Django Framework Example - AuthTemplate Integration

This example shows how to implement HTTP Basic Authentication
in a Django application using AuthTemplate pattern.

This assumes you have a Django project set up.

Installation:
    pip install django djangorestframework authtemplate pyyaml

Setup:
    1. Add this to your Django app's urls.py
    2. Create auth/core.py with AuthManager class
    3. Add required middleware

To use in your Django views:
    from .auth import require_basic_auth

    @require_basic_auth
    def protected_view(request):
        return JsonResponse({'user': request.user.username})
"""

from django.http import JsonResponse
from django.views import View
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from functools import wraps
import base64
import json

# Import AuthTemplate components
# from authtemplate.core import AuthManager
# from authtemplate.config import AuthConfig
# from authtemplate.logger import setup_logger, AuthLogger


# ============================================================================
# Django-Specific Auth Utilities (Adapter for AuthTemplate)
# ============================================================================

class DjangoAuthAdapter:
    """
    Adapter to integrate AuthTemplate with Django's authentication system.
    """

    def __init__(self, auth_manager):
        """
        Initialize the adapter.

        Args:
            auth_manager: AuthManager instance from AuthTemplate
        """
        self.auth_manager = auth_manager

    def get_client_ip(self, request):
        """Extract client IP from Django request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR', 'unknown')

    def verify_basic_auth(self, request):
        """
        Verify HTTP Basic Authentication from Django request.

        Returns:
            (success, user, message)
        """
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        ip_address = self.get_client_ip(request)

        if not auth_header.startswith('Basic '):
            return False, None, 'Missing authorization header'

        try:
            encoded = auth_header[6:]
            decoded = base64.b64decode(encoded).decode('utf-8')
            username, password = decoded.split(':', 1)
        except (ValueError, UnicodeDecodeError):
            return False, None, 'Invalid authorization header'

        result = self.auth_manager.verify_credentials(username, password, ip_address)
        return result.success, result.user, result.message


# ============================================================================
# Django Authentication Decorators
# ============================================================================

def require_basic_auth(view_func):
    """
    Decorator to require HTTP Basic Authentication on a Django view.

    Usage:
        @require_basic_auth
        def protected_view(request):
            return JsonResponse({'message': 'Authenticated'})
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # This assumes auth_adapter is available in your Django view context
        # You should set this up in your view initialization

        auth_header = request.META.get('HTTP_AUTHORIZATION', '')

        if not auth_header:
            return JsonResponse({'error': 'Missing Authorization header'}, status=401)

        if not auth_header.startswith('Basic '):
            return JsonResponse({'error': 'Invalid authorization header'}, status=401)

        try:
            encoded = auth_header[6:]
            decoded = base64.b64decode(encoded).decode('utf-8')
            username, password = decoded.split(':', 1)
        except (ValueError, UnicodeDecodeError):
            return JsonResponse({'error': 'Invalid authorization header'}, status=401)

        # TODO: Call auth_manager.verify_credentials here
        # For now, this is a template

        # Store authenticated user in request for access in view
        # request.auth_user = user

        return view_func(request, *args, **kwargs)

    return wrapper


# ============================================================================
# Django Views
# ============================================================================

class HealthCheckView(View):
    """Health check endpoint (no authentication required)."""

    def get(self, request):
        return JsonResponse({
            'status': 'OK',
            'service': 'DjangoAuth Example'
        })


class ProtectedView(View):
    """Protected endpoint that requires authentication."""

    @method_decorator(require_basic_auth)
    def get(self, request):
        return JsonResponse({
            'message': 'You are authenticated',
            'username': 'authenticated_user'  # Would come from request.auth_user
        })


class UserInfoView(View):
    """Get information about the authenticated user."""

    @method_decorator(require_basic_auth)
    def get(self, request):
        return JsonResponse({
            'user': {
                'username': 'authenticated_user',
                'email': 'user@example.com',
                'roles': ['user']
            }
        })


class ListUsersView(View):
    """List all configured users."""

    @method_decorator(require_basic_auth)
    def get(self, request):
        # In a real implementation, fetch from auth_manager
        return JsonResponse({
            'users': ['admin', 'user1', 'user2'],
            'count': 3
        })


class AuthTestView(View):
    """Test authentication with provided credentials."""

    @require_http_methods(["POST"])
    def post(self, request):
        try:
            data = json.loads(request.body)
            username = data.get('username', '')
            password = data.get('password', '')

            if not username or not password:
                return JsonResponse(
                    {'error': 'Missing username or password'},
                    status=400
                )

            # TODO: Call auth_manager.verify_credentials here

            return JsonResponse({
                'success': True,
                'user': {'username': username}
            })

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)


# ============================================================================
# Django Middleware (Optional)
# ============================================================================

class BasicAuthMiddleware:
    """
    Optional middleware to add authentication info to all requests.
    """

    def __init__(self, get_response, auth_adapter):
        self.get_response = get_response
        self.auth_adapter = auth_adapter

    def __call__(self, request):
        # Try to authenticate from basic auth header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')

        if auth_header.startswith('Basic '):
            try:
                encoded = auth_header[6:]
                decoded = base64.b64decode(encoded).decode('utf-8')
                username, password = decoded.split(':', 1)

                # Store credentials in request
                request.basic_auth = {
                    'username': username,
                    'password': password
                }
            except (ValueError, UnicodeDecodeError):
                pass

        response = self.get_response(request)
        return response


# ============================================================================
# Django URL Configuration (urls.py)
# ============================================================================

"""
Example Django URL configuration to use these views:

from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.HealthCheckView.as_view(), name='health'),
    path('protected/', views.ProtectedView.as_view(), name='protected'),
    path('user/info/', views.UserInfoView.as_view(), name='user_info'),
    path('admin/users/', views.ListUsersView.as_view(), name='list_users'),
    path('auth/test/', views.AuthTestView.as_view(), name='auth_test'),
]
"""

# ============================================================================
# Django Settings Configuration (settings.py)
# ============================================================================

"""
Add to your Django settings.py:

INSTALLED_APPS = [
    # ... other apps
    'your_app_name',
]

MIDDLEWARE = [
    # ... other middleware
    'your_app_name.middleware.BasicAuthMiddleware',
]

# Authentication settings
AUTH_TYPE = 'basic'
BASIC_AUTH_USERS_FILE = os.path.join(BASE_DIR, 'config/users.yaml')
"""
