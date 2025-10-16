# routes/materials.py
"""
Materials Management Routes
Company materials database and takeoff management
"""
from flask import Blueprint, request, jsonify, session
from database.materials_db import (
    get_company_materials, get_material, create_material, update_material, delete_material,
    create_takeoff_item, get_takeoff_items, get_project_takeoff_summary,
    update_takeoff_item, delete_takeoff_item,
    create_rfq, add_rfq_item, get_project_rfqs, get_rfq_with_items, update_rfq_status
)
from database.models import get_project, get_drawing, get_wbs_categories
from middleware.auth import login_required, company_access_required, admin_required

materials_bp = Blueprint('materials', __name__, url_prefix='/api')

# ============ Materials Database Management (Admin Only) ============

@materials_bp.route('/materials', methods=['GET'])
@login_required
@company_access_required
def get_materials():
    """Get all materials for current company"""
    company_id = session['company_id']
    category = request.args.get('category')
    active_only = request.args.get('active_only', 'true').lower() == 'true'
    
    materials = get_company_materials(company_id, category, active_only)
    return jsonify([dict(m) for m in materials])

@materials_bp.route('/materials/categories', methods=['GET'])
@login_required
@company_access_required
def get_material_categories():
    """Get unique material categories for current company"""
    company_id = session['company_id']
    materials = get_company_materials(company_id, active_only=False)
    
    categories = set()
    for material in materials:
        categories.add(material['category'])
    
    return jsonify(sorted(list(categories)))

@materials_bp.route('/materials', methods=['POST'])
@login_required
@company_access_required
@admin_required
def create_material_route():
    """Create a new material (admin only)"""
    company_id = session['company_id']
    data = request.json
    
    material_id = create_material(
        company_id=company_id,
        part_number=data['part_number'],
        category=data['category'],
        description=data['description'],
        size=data.get('size'),
        unit=data['unit'],
        list_price=float(data['list_price']),
        labor_units=float(data['labor_units'])
    )
    
    return jsonify({'id': material_id}), 201

@materials_bp.route('/materials/<int:material_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
@company_access_required
def material_detail(material_id):
    """Get, update, or delete a material"""
    material = get_material(material_id)
    
    if not material:
        return jsonify({'error': 'Material not found'}), 404
    
    # Verify material belongs to current company
    if material['company_id'] != session['company_id']:
        return jsonify({'error': 'Access denied'}), 403
    
    if request.method == 'GET':
        return jsonify(dict(material))
    
    elif request.method == 'PUT':
        # Require admin for updates
        from database.models import get_user_by_id
        user = get_user_by_id(session['user_id'])
        if not user or not user['is_admin']:
            return jsonify({'error': 'Admin access required'}), 403
        
        data = request.json
        update_material(
            material_id,
            part_number=data.get('part_number'),
            category=data.get('category'),
            description=data.get('description'),
            size=data.get('size'),
            unit=data.get('unit'),
            list_price=float(data['list_price']) if 'list_price' in data else None,
            labor_units=float(data['labor_units']) if 'labor_units' in data else None,
            is_active=data.get('is_active')
        )
        return jsonify({'success': True})
    
    elif request.method == 'DELETE':
        # Require admin for deletion
        from database.models import get_user_by_id
        user = get_user_by_id(session['user_id'])
        if not user or not user['is_admin']:
            return jsonify({'error': 'Admin access required'}), 403
        
        delete_material(material_id)
        return '', 204

# ============ Takeoff Management ============

@materials_bp.route('/drawings/<int:drawing_id>/takeoff', methods=['GET', 'POST'])
@login_required
@company_access_required
def drawing_takeoff(drawing_id):
    """Get or add takeoff items for a drawing"""
    # Verify drawing belongs to current company's project
    drawing = get_drawing(drawing_id)
    if not drawing:
        return jsonify({'error': 'Drawing not found'}), 404
    
    project = get_project(drawing['project_id'])
    if not project or project['company_id'] != session['company_id']:
        return jsonify({'error': 'Access denied'}), 403
    
    if request.method == 'GET':
        page_number = request.args.get('page_number', type=int)
        wbs_category_id = request.args.get('wbs_category_id', type=int)
        
        items = get_takeoff_items(drawing_id, page_number, wbs_category_id)
        return jsonify([dict(item) for item in items])
    
    elif request.method == 'POST':
        data = request.json
        
        item_id = create_takeoff_item(
            drawing_id=drawing_id,
            page_number=data['page_number'],
            material_id=data['material_id'],
            wbs_category_id=data.get('wbs_category_id'),
            quantity=float(data['quantity']),
            multiplier=float(data.get('multiplier', 1.0)),
            measurement_type=data.get('measurement_type'),
            notes=data.get('notes')
        )
        
        return jsonify({'id': item_id}), 201

@materials_bp.route('/takeoff/<int:item_id>', methods=['PUT', 'DELETE'])
@login_required
@company_access_required
def takeoff_item_detail(item_id):
    """Update or delete a takeoff item"""
    if request.method == 'PUT':
        data = request.json
        
        update_takeoff_item(
            item_id,
            quantity=float(data['quantity']) if 'quantity' in data else None,
            multiplier=float(data['multiplier']) if 'multiplier' in data else None,
            wbs_category_id=data.get('wbs_category_id'),
            notes=data.get('notes')
        )
        
        return jsonify({'success': True})
    
    elif request.method == 'DELETE':
        delete_takeoff_item(item_id)
        return '', 204

@materials_bp.route('/projects/<int:project_id>/takeoff/summary', methods=['GET'])
@login_required
@company_access_required
def project_takeoff_summary_route(project_id):
    """Get takeoff summary for entire project"""
    # Verify project belongs to current company
    project = get_project(project_id)
    if not project or project['company_id'] != session['company_id']:
        return jsonify({'error': 'Access denied'}), 403
    
    summary = get_project_takeoff_summary(project_id)
    return jsonify([dict(item) for item in summary])

# ============ RFQ Management ============

@materials_bp.route('/projects/<int:project_id>/rfqs', methods=['GET', 'POST'])
@login_required
@company_access_required
def project_rfqs(project_id):
    """Get or create RFQs for a project"""
    # Verify project belongs to current company
    project = get_project(project_id)
    if not project or project['company_id'] != session['company_id']:
        return jsonify({'error': 'Access denied'}), 403
    
    if request.method == 'GET':
        rfqs = get_project_rfqs(project_id)
        return jsonify([dict(rfq) for rfq in rfqs])
    
    elif request.method == 'POST':
        data = request.json
        
        rfq_id = create_rfq(
            project_id=project_id,
            rfq_number=data['rfq_number'],
            supplier_name=data.get('supplier_name'),
            supplier_email=data.get('supplier_email'),
            supplier_phone=data.get('supplier_phone'),
            notes=data.get('notes')
        )
        
        # Add items to RFQ
        for item in data.get('items', []):
            add_rfq_item(
                rfq_id=rfq_id,
                material_id=item['material_id'],
                quantity=float(item['quantity']),
                unit=item['unit'],
                notes=item.get('notes')
            )
        
        return jsonify({'id': rfq_id, 'rfq_number': data['rfq_number']}), 201

@materials_bp.route('/rfqs/<int:rfq_id>', methods=['GET'])
@login_required
@company_access_required
def rfq_detail(rfq_id):
    """Get RFQ with all items"""
    rfq_data = get_rfq_with_items(rfq_id)
    
    if not rfq_data['rfq']:
        return jsonify({'error': 'RFQ not found'}), 404
    
    # Verify RFQ belongs to current company's project
    project = get_project(rfq_data['rfq']['project_id'])
    if not project or project['company_id'] != session['company_id']:
        return jsonify({'error': 'Access denied'}), 403
    
    return jsonify(rfq_data)

@materials_bp.route('/rfqs/<int:rfq_id>/status', methods=['PUT'])
@login_required
@company_access_required
def update_rfq_status_route(rfq_id):
    """Update RFQ status"""
    data = request.json
    update_rfq_status(rfq_id, data['status'])
    return jsonify({'success': True})

@materials_bp.route('/rfqs/<int:rfq_id>/generate', methods=['POST'])
@login_required
@company_access_required
def generate_rfq_document(rfq_id):
    """Generate RFQ document (PDF/Excel)"""
    rfq_data = get_rfq_with_items(rfq_id)
    
    if not rfq_data['rfq']:
        return jsonify({'error': 'RFQ not found'}), 404
    
    # Verify access
    project = get_project(rfq_data['rfq']['project_id'])
    if not project or project['company_id'] != session['company_id']:
        return jsonify({'error': 'Access denied'}), 403
    
    # In production, generate actual PDF/Excel document here
    # For now, return data structure
    
    return jsonify({
        'message': 'RFQ generated successfully',
        'rfq': rfq_data
    })