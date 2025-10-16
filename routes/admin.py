# routes/admin.py - UPDATED VERSION
"""
Admin Routes - Company and User Management
NOW WITH AUTOMATIC MATERIALS DATABASE LOADING
"""
from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash
from database.models import (
    create_company, get_companies, delete_company,
    create_user, get_users, delete_user, get_user_by_email,
    add_user_to_company, get_user_companies
)
from database.db import load_default_materials_for_company
from middleware.auth import login_required, admin_required

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

# ============ Company Management ============

@admin_bp.route('/companies', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_companies():
    """Get all companies or create a new one"""
    if request.method == 'GET':
        companies = get_companies()
        return jsonify([dict(c) for c in companies])
    
    elif request.method == 'POST':
        data = request.json
        
        # Create the company
        company_id = create_company(
            name=data['name'],
            address=data.get('address'),
            phone=data.get('phone')
        )
        
        # IMPORTANT: Load default materials database for new company
        try:
            load_default_materials_for_company(company_id)
            print(f"✓ Default materials loaded for company: {data['name']}")
        except Exception as e:
            print(f"⚠️  Error loading default materials: {e}")
        
        return jsonify({'id': company_id, 'name': data['name']}), 201

@admin_bp.route('/companies/<int:company_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_company_route(company_id):
    """Delete a company"""
    delete_company(company_id)
    return '', 204

# ============ User Management ============

@admin_bp.route('/users', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_users():
    """Get all users or create a new one"""
    if request.method == 'GET':
        users = get_users()
        # Don't send password hashes
        return jsonify([{
            'id': u['id'],
            'email': u['email'],
            'first_name': u['first_name'],
            'last_name': u['last_name'],
            'is_admin': u['is_admin'],
            'created_at': u['created_at']
        } for u in users])
    
    elif request.method == 'POST':
        data = request.json
        
        # Check if user already exists
        existing = get_user_by_email(data['email'])
        if existing:
            return jsonify({'error': 'User with this email already exists'}), 400
        
        # Create the user
        user_id = create_user(
            email=data['email'],
            password=data['password'],
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            is_admin=data.get('is_admin', False)
        )
        
        # Add user to companies if specified
        if 'company_ids' in data:
            for company_id in data['company_ids']:
                add_user_to_company(user_id, company_id)
        
        return jsonify({'id': user_id, 'email': data['email']}), 201

@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_user_route(user_id):
    """Delete a user"""
    # Prevent deleting yourself
    if user_id == session.get('user_id'):
        return jsonify({'error': 'Cannot delete your own account'}), 400
    
    delete_user(user_id)
    return '', 204

# ============ User-Company Assignment ============

@admin_bp.route('/users/<int:user_id>/companies', methods=['GET', 'POST'])
@login_required
@admin_required
def user_companies(user_id):
    """Get or assign companies for a user"""
    if request.method == 'GET':
        companies = get_user_companies(user_id)
        return jsonify([dict(c) for c in companies])
    
    elif request.method == 'POST':
        data = request.json
        add_user_to_company(user_id, data['company_id'])
        return jsonify({'success': True}), 201

# ============ System Status ============

@admin_bp.route('/status', methods=['GET'])
@login_required
@admin_required
def system_status():
    """Get system status and statistics"""
    from database.db import get_db
    
    db = get_db()
    
    # Get counts
    company_count = db.execute('SELECT COUNT(*) FROM companies').fetchone()[0]
    user_count = db.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    project_count = db.execute('SELECT COUNT(*) FROM projects').fetchone()[0]
    drawing_count = db.execute('SELECT COUNT(*) FROM drawings').fetchone()[0]
    material_count = db.execute('SELECT COUNT(*) FROM company_materials WHERE is_active = 1').fetchone()[0]
    takeoff_count = db.execute('SELECT COUNT(*) FROM takeoff_items').fetchone()[0]
    rfq_count = db.execute('SELECT COUNT(*) FROM rfqs').fetchone()[0]
    
    return jsonify({
        'companies': company_count,
        'users': user_count,
        'projects': project_count,
        'drawings': drawing_count,
        'active_materials': material_count,
        'takeoff_items': takeoff_count,
        'rfqs': rfq_count
    })

# ============ Materials Database Reset ============

@admin_bp.route('/companies/<int:company_id>/reset-materials', methods=['POST'])
@login_required
@admin_required
def reset_company_materials(company_id):
    """Reset company materials to default database (admin only)"""
    from database.db import get_db
    
    # Delete existing materials
    db = get_db()
    db.execute('DELETE FROM company_materials WHERE company_id = ?', (company_id,))
    db.commit()
    
    # Reload defaults
    load_default_materials_for_company(company_id)
    
    return jsonify({'success': True, 'message': 'Materials database reset to defaults'})