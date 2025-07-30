"""
Authentication middleware for frontend route protection
"""
import jwt
from flask import request, jsonify, current_app
from functools import wraps

def verify_token(token):
    """Verify JWT token"""
    try:
        if not token:
            return None
        
        # Remove 'Bearer ' prefix if present
        if token.startswith('Bearer '):
            token = token[7:]
        
        # Use the same secret key logic as auth route
        import os
        secret_key = os.environ.get("SECRET_KEY", "supersecretkey")
        
        # Decode the token
        payload = jwt.decode(token, secret_key, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def check_frontend_auth():
    """Check if user is authenticated for frontend access"""
    # Check for token in various places
    token = None
    
    # Check Authorization header
    auth_header = request.headers.get('Authorization')
    if auth_header:
        token = auth_header
    
    # Check cookies
    if not token:
        token = request.cookies.get('auth_token')
    
    # Check query parameter (for initial auth)
    if not token:
        token = request.args.get('token')
    
    # Verify token
    if token:
        payload = verify_token(token)
        if payload:
            return True, payload
    
    return False, None

def require_auth_for_frontend(f):
    """Decorator to require authentication for frontend routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        is_authenticated, user_data = check_frontend_auth()
        if not is_authenticated:
            # Return login page or redirect to login
            return None
        return f(*args, **kwargs)
    return decorated_function

