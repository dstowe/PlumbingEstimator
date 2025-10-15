"""
Drawing Routes
Drawing upload, processing, and detection management
"""
import os
import io
from datetime import datetime
from flask import Blueprint, request, jsonify, session, send_file
from werkzeug.utils import secure_filename
import cv2

from config import Config
from database.models import (
    get_project, create_drawing, get_drawing, update_drawing_scale,
    create_detected_item, get_detected_items, update_detected_item,
    delete_detected_item, get_takeoff_summary
)
from services.pdf_processor import extract_pdf_page_as_image, get_pdf_page_count, detect_scale_notation
from services.detector import detect_plumbing_symbols
from middleware.auth import login_required, company_access_required

drawings_bp = Blueprint('drawings', __name__, url_prefix='/api')

# Drawing Upload
@drawings_bp.route('/projects/<int:project_id>/drawings', methods=['POST'])
@login_required
@company_access_required
def upload_drawing(project_id):
    """Upload a new drawing to a project"""
    # Verify project belongs to current company
    project = get_project(project_id)
    if not project or project['company_id'] != session['company_id']:
        return jsonify({'error': 'Project not found'}), 404
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Validate file type
    if not file.filename.lower().endswith(('.pdf', '.tif', '.tiff')):
        return jsonify({'error': 'Only PDF and TIFF files allowed'}), 400
    
    # Save file
    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{timestamp}_{filename}"
    filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
    file.save(filepath)
    
    # Get page count
    page_count = get_pdf_page_count(filepath)
    
    # Save to database
    drawing_id = create_drawing(
        project_id=project_id,
        name=file.filename,
        file_path=filepath,
        page_count=page_count
    )
    
    return jsonify({
        'id': drawing_id,
        'name': file.filename,
        'page_count': page_count
    }), 201

# Drawing Processing
@drawings_bp.route('/drawings/<int:drawing_id>/process', methods=['POST'])
@login_required
@company_access_required
def process_drawing(drawing_id):
    """Process a drawing to detect fixtures"""
    data = request.json
    page_number = data.get('page_number', 0)
    
    drawing = get_drawing(drawing_id)
    if not drawing:
        return jsonify({'error': 'Drawing not found'}), 404
    
    # Extract image and detect
    img = extract_pdf_page_as_image(drawing['file_path'], page_number)
    scale = detect_scale_notation(img)
    detected_items = detect_plumbing_symbols(img)
    
    # Update scale
    update_drawing_scale(drawing_id, scale)
    
    # Save detected items
    for item in detected_items:
        create_detected_item(
            drawing_id=drawing_id,
            page_number=page_number,
            item_type=item['type'],
            x=item['x'],
            y=item['y'],
            width=item['width'],
            height=item['height'],
            confidence=item['confidence']
        )
    
    return jsonify({
        'scale': scale,
        'detected_items': detected_items,
        'count': len(detected_items)
    })

# Drawing Image Retrieval
@drawings_bp.route('/drawings/<int:drawing_id>/page/<int:page_num>/image')
@login_required
def get_drawing_page_image(drawing_id, page_num):
    """Get drawing page as image"""
    drawing = get_drawing(drawing_id)
    if not drawing:
        return jsonify({'error': 'Drawing not found'}), 404
    
    img = extract_pdf_page_as_image(drawing['file_path'], page_num, dpi=100)
    
    # Convert to PNG
    _, buffer = cv2.imencode('.png', img)
    io_buf = io.BytesIO(buffer)
    
    return send_file(io_buf, mimetype='image/png')

# Detected Items Management
@drawings_bp.route('/drawings/<int:drawing_id>/items', methods=['GET', 'POST'])
@login_required
def manage_drawing_items(drawing_id):
    """Get or add detected items"""
    if request.method == 'GET':
        page_num = request.args.get('page', type=int)
        items = get_detected_items(drawing_id, page_num)
        return jsonify([dict(item) for item in items])
    
    elif request.method == 'POST':
        data = request.json
        item_id = create_detected_item(
            drawing_id=drawing_id,
            page_number=data['page_number'],
            item_type=data['item_type'],
            x=data['x'],
            y=data['y'],
            width=data['width'],
            height=data['height'],
            confidence=data.get('confidence', 1.0),
            verified=True
        )
        return jsonify({'id': item_id}), 201

@drawings_bp.route('/items/<int:item_id>', methods=['PUT', 'DELETE'])
@login_required
def item_detail(item_id):
    """Update or delete a detected item"""
    if request.method == 'PUT':
        data = request.json
        update_detected_item(
            item_id=item_id,
            item_type=data.get('item_type'),
            verified=data.get('verified', True),
            notes=data.get('notes')
        )
        return jsonify({'success': True})
    
    elif request.method == 'DELETE':
        delete_detected_item(item_id)
        return '', 204

# Takeoff Summary
@drawings_bp.route('/drawings/<int:drawing_id>/takeoff')
@login_required
def get_drawing_takeoff(drawing_id):
    """Get quantity takeoff summary"""
    items = get_takeoff_summary(drawing_id)
    
    return jsonify([{
        'type': item['item_type'],
        'count': item['count']
    } for item in items])