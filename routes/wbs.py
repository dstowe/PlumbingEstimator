"""
WBS (Work Breakdown Structure) Routes
Manage WBS categories for projects with hierarchical support
"""
from flask import Blueprint, request, jsonify, session
from database.models import (
    get_project, get_wbs_categories, get_wbs_category, get_wbs_categories_tree,
    create_wbs_category, update_wbs_category, delete_wbs_category,
    get_takeoff_by_wbs, bulk_update_items_wbs, get_wbs_path,
    check_wbs_category_has_items, check_wbs_category_has_children
)
from middleware.auth import login_required, company_access_required

wbs_bp = Blueprint('wbs', __name__, url_prefix='/api')

@wbs_bp.route('/projects/<int:project_id>/wbs', methods=['GET', 'POST'])
@login_required
@company_access_required
def manage_wbs_categories(project_id):
    """Get all WBS categories for a project or create a new one"""
    # Verify project belongs to current company
    project = get_project(project_id)
    if not project or project['company_id'] != session['company_id']:
        return jsonify({'error': 'Project not found'}), 404
    
    if request.method == 'GET':
        categories = get_wbs_categories(project_id)
        return jsonify([dict(c) for c in categories])
    
    elif request.method == 'POST':
        data = request.json
        category_id = create_wbs_category(
            project_id=project_id,
            name=data['name'],
            parent_id=data.get('parent_id'),
            sort_order=data.get('sort_order')
        )
        return jsonify({'id': category_id, 'name': data['name']}), 201

@wbs_bp.route('/projects/<int:project_id>/wbs/tree', methods=['GET'])
@login_required
@company_access_required
def get_wbs_tree(project_id):
    """Get WBS categories as a hierarchical tree"""
    project = get_project(project_id)
    if not project or project['company_id'] != session['company_id']:
        return jsonify({'error': 'Project not found'}), 404
    
    tree = get_wbs_categories_tree(project_id)
    return jsonify(tree)

@wbs_bp.route('/wbs/<int:category_id>', methods=['PUT', 'DELETE'])
@login_required
@company_access_required
def wbs_category_detail(category_id):
    """Update or delete a WBS category"""
    category = get_wbs_category(category_id)
    if not category:
        return jsonify({'error': 'WBS category not found'}), 404
    
    # Verify category's project belongs to current company
    project = get_project(category['project_id'])
    if not project or project['company_id'] != session['company_id']:
        return jsonify({'error': 'Access denied'}), 403
    
    if request.method == 'PUT':
        data = request.json
        update_wbs_category(
            category_id=category_id,
            name=data.get('name'),
            sort_order=data.get('sort_order')
        )
        return jsonify({'success': True})
    
    elif request.method == 'DELETE':
        # Check if category has items assigned
        if check_wbs_category_has_items(category_id):
            return jsonify({'error': 'Cannot delete WBS category that has items assigned to it'}), 400
        
        # Check if category has children
        if check_wbs_category_has_children(category_id):
            return jsonify({'error': 'Cannot delete WBS category that has sub-categories. Delete sub-categories first.'}), 400
        
        try:
            delete_wbs_category(category_id)
            return '', 204
        except ValueError as e:
            return jsonify({'error': str(e)}), 400

@wbs_bp.route('/wbs/<int:category_id>/path', methods=['GET'])
@login_required
def get_category_path(category_id):
    """Get the full path of a category"""
    path = get_wbs_path(category_id)
    return jsonify({'path': path})

@wbs_bp.route('/projects/<int:project_id>/takeoff-by-wbs', methods=['GET'])
@login_required
@company_access_required
def project_takeoff_by_wbs(project_id):
    """Get takeoff summary grouped by WBS category for entire project"""
    # Verify project belongs to current company
    project = get_project(project_id)
    if not project or project['company_id'] != session['company_id']:
        return jsonify({'error': 'Project not found'}), 404
    
    takeoff = get_takeoff_by_wbs(project_id)
    
    # Build hierarchical structure
    result = {}
    for row in takeoff:
        wbs_id = row['wbs_category_id']
        wbs_name = row['wbs_category'] or 'Uncategorized'
        
        if wbs_id:
            # Get full path for hierarchical categories
            full_path = get_wbs_path(wbs_id)
            wbs_name = full_path
        
        if wbs_name not in result:
            result[wbs_name] = {
                'wbs_category_id': wbs_id,
                'wbs_category': wbs_name,
                'items': []
            }
        result[wbs_name]['items'].append({
            'item_type': row['item_type'],
            'count': row['count']
        })
    
    return jsonify(list(result.values()))

@wbs_bp.route('/items/bulk-update-wbs', methods=['POST'])
@login_required
def bulk_update_wbs():
    """Bulk update WBS category for multiple items"""
    data = request.json
    item_ids = data.get('item_ids', [])
    wbs_category_id = data.get('wbs_category_id')
    
    if not item_ids:
        return jsonify({'error': 'No items provided'}), 400
    
    bulk_update_items_wbs(item_ids, wbs_category_id)
    return jsonify({'success': True, 'updated': len(item_ids)})