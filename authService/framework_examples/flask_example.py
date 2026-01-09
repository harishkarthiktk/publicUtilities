"""
Flask Framework Example - AuthTemplate Integration

This example shows how to integrate AuthTemplate into a Flask application
using HTTP Basic Authentication.

Dependencies:
    pip install flask authtemplate pyyaml

To run this example:
    python flask_example.py
"""

from flask import Flask, jsonify, request, g
from functools import wraps
from pathlib import Path

# Import from authtemplate
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from core import AuthManager
from config import AuthConfig
from logger import setup_logger, AuthLogger


# Initialize Flask app
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Set up authentication
auth_config = AuthConfig(
    yaml_file='example_users.yaml',
    use_env_vars=True
)

logger = setup_logger('FlaskAuth', log_file='logs/flask_auth.log')
auth_logger = AuthLogger(logger)
auth_manager = AuthManager(auth_config, logger=auth_logger)


def get_client_ip():
    """Extract client IP from request."""
    return request.remote_addr or 'unknown'


def require_auth(f):
    """
    Decorator to require authentication on a route.

    Usage:
        @app.route('/protected')
        @require_auth
        def protected_route():
            return jsonify({'message': 'You are authenticated'})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')

        if not auth_header:
            return jsonify({'error': 'Missing Authorization header'}), 401

        # Verify credentials from Basic Auth header
        result = auth_manager.verify_basic_auth_header(
            auth_header,
            ip_address=get_client_ip()
        )

        if not result.success:
            return jsonify({'error': result.message}), 401

        # Store authenticated user in Flask's g object for use in route
        g.user = result.user

        return f(*args, **kwargs)

    return decorated_function


# ============================================================================
# Routes
# ============================================================================

@app.route('/health', methods=['GET'])
def health_check():
    """Public health check endpoint (no authentication required)."""
    return jsonify({'status': 'OK', 'service': 'FlaskAuth Example'}), 200


@app.route('/protected', methods=['GET'])
@require_auth
def protected_route():
    """Protected endpoint that requires authentication."""
    return jsonify({
        'message': 'You are authenticated',
        'username': g.user.username,
        'roles': g.user.roles
    }), 200


@app.route('/user/info', methods=['GET'])
@require_auth
def user_info():
    """Get information about the authenticated user."""
    user_info = auth_manager.get_user_info(g.user.username)
    return jsonify({
        'user': g.user.to_dict(),
        'request_ip': get_client_ip()
    }), 200


@app.route('/admin/users', methods=['GET'])
@require_auth
def list_users():
    """List all users (admin endpoint)."""
    # You can add role-based access control here
    users = auth_manager.list_users()
    return jsonify({
        'users': users,
        'count': len(users)
    }), 200


@app.errorhandler(401)
def unauthorized(error):
    """Handle 401 Unauthorized errors."""
    return jsonify({'error': 'Unauthorized'}), 401


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 Internal Server errors."""
    return jsonify({'error': 'Internal server error'}), 500


# ============================================================================
# Example: Using AuthManager Directly
# ============================================================================

@app.route('/auth/test', methods=['POST'])
def auth_test():
    """
    Test authentication with provided credentials.

    POST body:
        {
            "username": "admin",
            "password": "password"
        }
    """
    data = request.get_json()
    username = data.get('username', '')
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'error': 'Missing username or password'}), 400

    result = auth_manager.verify_credentials(
        username,
        password,
        ip_address=get_client_ip()
    )

    if result.success:
        return jsonify({
            'success': True,
            'user': result.user.to_dict()
        }), 200
    else:
        return jsonify({
            'success': False,
            'error': result.message
        }), 401


# ============================================================================
# Startup and Shutdown
# ============================================================================

@app.before_request
def before_request():
    """Log incoming requests."""
    logger.debug(f"Incoming request: {request.method} {request.path}")


@app.after_request
def after_request(response):
    """Log responses."""
    logger.debug(f"Response: {response.status_code}")
    return response


if __name__ == '__main__':
    print(f"Starting Flask Auth Example")
    print(f"Configured users: {auth_manager.list_users()}")
    print(f"\nTest endpoints:")
    print(f"  GET  http://localhost:5000/health              (no auth)")
    print(f"  GET  http://localhost:5000/protected            (requires auth)")
    print(f"  POST http://localhost:5000/auth/test            (test auth)")
    print(f"  GET  http://localhost:5000/user/info            (requires auth)")
    print(f"  GET  http://localhost:5000/admin/users          (requires auth)")
    print(f"\nExample credentials: admin / password")
    print(f"")

    app.run(host='0.0.0.0', port=5000, debug=True)
