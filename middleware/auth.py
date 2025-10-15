"""
Authentication and authorization decorators
"""
from functools import wraps
from flask import session, jsonify
from database.models import get_user_by_id

def login_required(f):
    """Require user to be logged in"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Require user to be an admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        
        user = get_user_by_id(session['user_id'])
        
        if not user or not user['is_admin']:
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

def company_access_required(f):
    """Require user to have selected a company"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'company_id' not in session:
            return jsonify({'error': 'Please select a company first'}), 400
        return f(*args, **kwargs)
    return decorated_function