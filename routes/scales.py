"""
Scale Management Routes
Handles drawing scales, custom scales, and scale zones
"""
from flask import Blueprint, request, jsonify, session
from database.models import (
    get_drawing, get_project_from_drawing,
    create_custom_scale, get_custom_scales_for_project, delete_custom_scale,
    set_page_scale, get_page_scale,
    create_scale_zone, get_scale_zones_for_page, update_scale_zone, delete_scale_zone
)
from middleware.auth import login_required, company_access_required

scales_bp = Blueprint('scales', __name__, url_prefix='/api')

# Common architectural and engineering scales
COMMON_SCALES = [
    # Architectural scales (imperial)
    {'id': 'arch_3_32', 'name': '3/32" = 1\'-0"', 'ratio': 128, 'type': 'architectural'},
    {'id': 'arch_1_8', 'name': '1/8" = 1\'-0"', 'ratio': 96, 'type': 'architectural'},
    {'id': 'arch_3_16', 'name': '3/16" = 1\'-0"', 'ratio': 64, 'type': 'architectural'},
    {'id': 'arch_1_4', 'name': '1/4" = 1\'-0"', 'ratio': 48, 'type': 'architectural'},
    {'id': 'arch_3_8', 'name': '3/8" = 1\'-0"', 'ratio': 32, 'type': 'architectural'},
    {'id': 'arch_1_2', 'name': '1/2" = 1\'-0"', 'ratio': 24, 'type': 'architectural'},
    {'id': 'arch_3_4', 'name': '3/4" = 1\'-0"', 'ratio': 16, 'type': 'architectural'},
    {'id': 'arch_1', 'name': '1" = 1\'-0"', 'ratio': 12, 'type': 'architectural'},
    {'id': 'arch_1_5', 'name': '1-1/2" = 1\'-0"', 'ratio': 8, 'type': 'architectural'},
    {'id': 'arch_3', 'name': '3" = 1\'-0"', 'ratio': 4, 'type': 'architectural'},
    
    # Engineering scales (imperial)
    {'id': 'eng_10', 'name': '1" = 10\'', 'ratio': 120, 'type': 'engineering'},
    {'id': 'eng_20', 'name': '1" = 20\'', 'ratio': 240, 'type': 'engineering'},
    {'id': 'eng_30', 'name': '1" = 30\'', 'ratio': 360, 'type': 'engineering'},
    {'id': 'eng_40', 'name': '1" = 40\'', 'ratio': 480, 'type': 'engineering'},
    {'id': 'eng_50', 'name': '1" = 50\'', 'ratio': 600, 'type': 'engineering'},
    {'id': 'eng_60', 'name': '1" = 60\'', 'ratio': 720, 'type': 'engineering'},
    {'id': 'eng_100', 'name': '1" = 100\'', 'ratio': 1200, 'type': 'engineering'},
    
    # Metric scales
    {'id': 'metric_1_100', 'name': '1:100', 'ratio': 100, 'type': 'metric'},
    {'id': 'metric_1_50', 'name': '1:50', 'ratio': 50, 'type': 'metric'},
    {'id': 'metric_1_20', 'name': '1:20', 'ratio': 20, 'type': 'metric'},
    {'id': 'metric_1_10', 'name': '1:10', 'ratio': 10, 'type': 'metric'},
    {'id': 'metric_1_5', 'name': '1:5', 'ratio': 5, 'type': 'metric'},
]

@scales_bp.route('/scales/common', methods=['GET'])
@login_required
def get_common_scales_list():
    """Get list of common architectural and engineering scales"""
    return jsonify(COMMON_SCALES)

@scales_bp.route('/projects/<int:project_id>/scales/custom', methods=['GET', 'POST'])
@login_required
@company_access_required
def manage_custom_scales(project_id):
    """Get or create custom scales for a project"""
    if request.method == 'GET':
        scales = get_custom_scales_for_project(project_id)
        return jsonify([dict(s) for s in scales])
    
    elif request.method == 'POST':
        data = request.json
        scale_id = create_custom_scale(
            project_id=project_id,
            name=data['name'],
            pixels_per_unit=data['pixels_per_unit'],
            unit=data.get('unit', 'feet')
        )
        return jsonify({'id': scale_id, 'name': data['name']}), 201

@scales_bp.route('/scales/custom/<int:scale_id>', methods=['DELETE'])
@login_required
def delete_custom_scale_route(scale_id):
    """Delete a custom scale"""
    delete_custom_scale(scale_id)
    return '', 204

@scales_bp.route('/drawings/<int:drawing_id>/page/<int:page_num>/scale', methods=['GET', 'PUT'])
@login_required
def manage_page_scale(drawing_id, page_num):
    """Get or set the scale for a specific page"""
    if request.method == 'GET':
        scale = get_page_scale(drawing_id, page_num)
        # Convert Row to dict explicitly
        return jsonify(dict(scale) if scale else {})
    
    elif request.method == 'PUT':
        data = request.json
        set_page_scale(
            drawing_id=drawing_id,
            page_number=page_num,
            scale_id=data.get('scale_id'),
            scale_name=data.get('scale_name'),
            pixels_per_unit=data.get('pixels_per_unit')
        )
        return jsonify({'success': True})

@scales_bp.route('/drawings/<int:drawing_id>/page/<int:page_num>/scale-zones', methods=['GET', 'POST'])
@login_required
def manage_scale_zones(drawing_id, page_num):
    """Get or create scale zones (bounding boxes with different scales)"""
    if request.method == 'GET':
        zones = get_scale_zones_for_page(drawing_id, page_num)
        return jsonify([dict(z) for z in zones])
    
    elif request.method == 'POST':
        data = request.json
        zone_id = create_scale_zone(
            drawing_id=drawing_id,
            page_number=page_num,
            name=data['name'],
            x=data['x'],
            y=data['y'],
            width=data['width'],
            height=data['height'],
            scale_id=data.get('scale_id'),
            scale_name=data.get('scale_name'),
            pixels_per_unit=data.get('pixels_per_unit')
        )
        return jsonify({'id': zone_id}), 201

@scales_bp.route('/scale-zones/<int:zone_id>', methods=['PUT', 'DELETE'])
@login_required
def scale_zone_detail(zone_id):
    """Update or delete a scale zone"""
    if request.method == 'PUT':
        data = request.json
        update_scale_zone(
            zone_id=zone_id,
            name=data.get('name'),
            x=data.get('x'),
            y=data.get('y'),
            width=data.get('width'),
            height=data.get('height'),
            scale_id=data.get('scale_id'),
            scale_name=data.get('scale_name'),
            pixels_per_unit=data.get('pixels_per_unit')
        )
        return jsonify({'success': True})
    
    elif request.method == 'DELETE':
        delete_scale_zone(zone_id)
        return '', 204

@scales_bp.route('/drawings/<int:drawing_id>/calibrate', methods=['POST'])
@login_required
def calibrate_scale(drawing_id):
    """
    Calibrate a custom scale based on known distance
    
    Request body:
    {
        "page_number": 0,
        "pixel_distance": 150.5,
        "real_distance": 10,
        "unit": "feet",
        "name": "Custom Scale 1"
    }
    """
    data = request.json
    
    pixel_distance = data.get('pixel_distance')
    real_distance = data.get('real_distance')
    unit = data.get('unit', 'feet')
    
    if not pixel_distance or not real_distance:
        return jsonify({'error': 'pixel_distance and real_distance required'}), 400
    
    pixels_per_unit = pixel_distance / real_distance
    scale_ratio = real_distance / pixel_distance
    
    result = {
        'pixels_per_unit': pixels_per_unit,
        'scale_ratio': scale_ratio,
        'unit': unit
    }
    
    if data.get('name'):
        drawing = get_drawing(drawing_id)
        if not drawing:
            return jsonify({'error': 'Drawing not found'}), 404
        
        project = get_project_from_drawing(drawing_id)
        if project:
            scale_id = create_custom_scale(
                project_id=project['id'],
                name=data['name'],
                pixels_per_unit=pixels_per_unit,
                unit=unit
            )
            result['scale_id'] = scale_id
    
    return jsonify(result)