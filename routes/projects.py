"""
Project Routes
Project management for companies
"""
from flask import Blueprint, request, jsonify, session
from database.models import (
    create_project, get_projects_by_company, get_project, delete_project,
    get_drawings_by_project
)
from middleware.auth import login_required, company_access_required

projects_bp = Blueprint('projects', __name__, url_prefix='/api/projects')

@projects_bp.route('', methods=['GET', 'POST'])
@login_required
@company_access_required
def manage_projects():
    """Get all projects for current company or create a new one"""
    company_id = session['company_id']
    
    if request.method == 'GET':
        projects = get_projects_by_company(company_id)
        return jsonify([dict(p) for p in projects])
    
    elif request.method == 'POST':
        data = request.json
        project_id = create_project(
            company_id=company_id,
            name=data['name'],
            description=data.get('description')
        )
        return jsonify({'id': project_id, 'name': data['name']}), 201

@projects_bp.route('/<int:project_id>', methods=['GET', 'DELETE'])
@login_required
@company_access_required
def project_detail(project_id):
    """Get or delete a specific project"""
    # Verify project belongs to current company
    project = get_project(project_id)
    
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    if project['company_id'] != session['company_id']:
        return jsonify({'error': 'Access denied'}), 403
    
    if request.method == 'GET':
        drawings = get_drawings_by_project(project_id)
        return jsonify({
            'project': dict(project),
            'drawings': [dict(d) for d in drawings]
        })
    
    elif request.method == 'DELETE':
        delete_project(project_id)
        return '', 204