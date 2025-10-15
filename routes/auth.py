"""
Authentication Routes
Handles login, logout, and user session management
"""
from flask import Blueprint, request, jsonify, session
from werkzeug.security import check_password_hash
from database.models import get_user_by_email, get_user_by_id, get_user_companies, check_user_company_access, get_company
from middleware.auth import login_required

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/login', methods=['POST'])
def login():
    """User login endpoint"""
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400
    
    user = get_user_by_email(email)
    
    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify({'error': 'Invalid email or password'}), 401
    
    # Set session
    session['user_id'] = user['id']
    session['user_email'] = user['email']
    session['is_admin'] = user['is_admin']
    
    return jsonify({
        'success': True,
        'user': {
            'id': user['id'],
            'email': user['email'],
            'first_name': user['first_name'],
            'last_name': user['last_name'],
            'is_admin': user['is_admin']
        }
    })

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """User logout endpoint"""
    session.clear()
    return jsonify({'success': True})

@auth_bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    """Get current logged-in user info"""
    user = get_user_by_id(session['user_id'])
    
    return jsonify({
        'id': user['id'],
        'email': user['email'],
        'first_name': user['first_name'],
        'last_name': user['last_name'],
        'is_admin': user['is_admin']
    })

@auth_bp.route('/companies', methods=['GET'])
@login_required
def get_user_companies_route():
    """Get companies for current user"""
    companies = get_user_companies(session['user_id'])
    return jsonify([dict(c) for c in companies])

@auth_bp.route('/select-company/<int:company_id>', methods=['POST'])
@login_required
def select_company(company_id):
    """Select a company to work with"""
    # Verify user has access to this company
    if not check_user_company_access(session['user_id'], company_id):
        return jsonify({'error': 'Access denied'}), 403
    
    company = get_company(company_id)
    if not company:
        return jsonify({'error': 'Company not found'}), 404
    
    session['company_id'] = company_id
    session['company_name'] = company['name']
    
    return jsonify({'success': True, 'company': dict(company)})

@auth_bp.route('/current-company', methods=['GET'])
@login_required
def get_current_company():
    """Get currently selected company"""
    if 'company_id' not in session:
        return jsonify({'company': None})
    
    company = get_company(session['company_id'])
    return jsonify({'company': dict(company) if company else None})