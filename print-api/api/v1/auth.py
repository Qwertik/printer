import functools
from flask import request, jsonify, current_app


def require_auth(f):
    """Decorator: checks Authorization: Bearer <token> against config.API_TOKEN."""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        token = current_app.config.get('API_TOKEN', '')
        if not token:
            # No token configured — auth disabled (development mode)
            return f(*args, **kwargs)
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401
        if auth_header[7:] != token:
            return jsonify({"error": "Invalid token"}), 403
        return f(*args, **kwargs)
    return decorated


def require_admin(f):
    """Decorator: checks for admin token. Used for /print/raw."""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        token = current_app.config.get('ADMIN_TOKEN', '')
        if not token:
            return jsonify({"error": "Admin endpoint not configured"}), 403
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401
        if auth_header[7:] != token:
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)
    return decorated
