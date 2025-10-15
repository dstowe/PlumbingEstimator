"""
Admin Routes
Company and user management for administrators
"""
from flask import Blueprint, request, jsonify, session
import sqlite3
from database.models import (
    create_company, get_companies, delete_company,
    create_user, get_users, delete_user, add_user_to_company
)
from middleware.auth import admin_required

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

# Company Management
@admin_bp.route('/companies', methods=['GET', 'POST'])
@admin_required
def manage_companies():
    """Get all companies or create a new one"""
    if request.method == 'GET':
        companies = get_companies()
        return jsonify([dict(c) for c in companies])
    
    elif request.method == 'POST':
        data = request.json
        try:
            company_id = create_company(
                name=data['name'],
                address=data.get('address'),
                phone=data.get('phone')
            )
            return jsonify({'id': company_id, 'name': data['name']}), 201
        except sqlite3.IntegrityError:
            return jsonify({'error': 'Company name already exists'}), 400

@admin_bp.route('/companies/<int:company_id>', methods=['DELETE'])
@admin_required
def remove_company(company_id):
    """Delete a company"""
    delete_company(company_id)
    return '', 204

# User Management
@admin_bp.route('/users', methods=['GET', 'POST'])
@admin_required
def manage_users():
    """Get all users or create a new one"""
    if request.method == 'GET':
        users = get_users()
        return jsonify([dict(u) for u in users])
    
    elif request.method == 'POST':
        data = request.json
        try:
            user_id = create_user(
                email=data['email'],
                password=data['password'],
                first_name=data.get('first_name'),
                last_name=data.get('last_name'),
                is_admin=data.get('is_admin', False)
            )
            
            # Add user to companies
            if 'company_ids' in data:
                for company_id in data['company_ids']:
                    add_user_to_company(user_id, company_id)
            
            return jsonify({'id': user_id, 'email': data['email']}), 201
        except sqlite3.IntegrityError:
            return jsonify({'error': 'Email already exists'}), 400

@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def remove_user(user_id):
    """Delete a user"""
    # Prevent deleting yourself
    if user_id == session['user_id']:
        return jsonify({'error': 'Cannot delete your own account'}), 400
    
    delete_user(user_id)
    return '', 204