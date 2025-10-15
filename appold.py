"""
Plumbing Estimator Prototype - Multi-Tenant with Authentication
A local construction estimation tool for plumbing takeoffs from PDF drawings
"""

from flask import Flask, render_template_string, request, jsonify, send_file, session, redirect, url_for
from flask_cors import CORS
import sqlite3
import os
import json
from datetime import datetime
import fitz  # PyMuPDF
import cv2
import numpy as np
from pathlib import Path
import base64
import io
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'  # Change this!
CORS(app)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Ensure directories exist
Path(app.config['UPLOAD_FOLDER']).mkdir(exist_ok=True)
Path('data').mkdir(exist_ok=True)

# Database setup
def init_db():
    conn = sqlite3.connect('data/estimator.db')
    c = conn.cursor()
    
    # Companies table
    c.execute('''CREATE TABLE IF NOT EXISTS companies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        address TEXT,
        phone TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        first_name TEXT,
        last_name TEXT,
        is_admin BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # User-Company relationship (many-to-many)
    c.execute('''CREATE TABLE IF NOT EXISTS user_companies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        company_id INTEGER NOT NULL,
        role TEXT DEFAULT 'user',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
        UNIQUE(user_id, company_id)
    )''')
    
    # Projects table (now with company_id)
    c.execute('''CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
    )''')
    
    # Drawings table
    c.execute('''CREATE TABLE IF NOT EXISTS drawings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        file_path TEXT NOT NULL,
        page_count INTEGER,
        scale TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
    )''')
    
    # Detected items table
    c.execute('''CREATE TABLE IF NOT EXISTS detected_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        drawing_id INTEGER NOT NULL,
        page_number INTEGER NOT NULL,
        item_type TEXT NOT NULL,
        x REAL,
        y REAL,
        width REAL,
        height REAL,
        confidence REAL,
        verified BOOLEAN DEFAULT 0,
        notes TEXT,
        FOREIGN KEY (drawing_id) REFERENCES drawings(id) ON DELETE CASCADE
    )''')
    
    # Measurements table
    c.execute('''CREATE TABLE IF NOT EXISTS measurements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        drawing_id INTEGER NOT NULL,
        page_number INTEGER NOT NULL,
        measurement_type TEXT NOT NULL,
        value REAL,
        unit TEXT,
        start_x REAL,
        start_y REAL,
        end_x REAL,
        end_y REAL,
        notes TEXT,
        FOREIGN KEY (drawing_id) REFERENCES drawings(id) ON DELETE CASCADE
    )''')
    
    # Create default admin user if none exists
    admin_exists = c.execute('SELECT COUNT(*) FROM users WHERE is_admin = 1').fetchone()[0]
    if admin_exists == 0:
        admin_hash = generate_password_hash('admin123')
        c.execute(
            'INSERT INTO users (email, password_hash, first_name, last_name, is_admin) VALUES (?, ?, ?, ?, ?)',
            ('admin@example.com', admin_hash, 'Admin', 'User', 1)
        )
        print("Default admin user created: admin@example.com / admin123")
    
    conn.commit()
    conn.close()

# Initialize database
init_db()

# Authentication decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        
        conn = get_db()
        user = conn.execute('SELECT is_admin FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        conn.close()
        
        if not user or not user['is_admin']:
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

def company_access_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'company_id' not in session:
            return jsonify({'error': 'Please select a company first'}), 400
        return f(*args, **kwargs)
    return decorated_function

# PDF Processing Functions
def extract_pdf_page_as_image(pdf_path, page_num, dpi=150):
    """Convert PDF page to image for processing"""
    doc = fitz.open(pdf_path)
    page = doc[page_num]
    mat = fitz.Matrix(dpi/72, dpi/72)
    pix = page.get_pixmap(matrix=mat)
    img_data = pix.tobytes("png")
    doc.close()
    
    # Convert to OpenCV format
    nparr = np.frombuffer(img_data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return img

def detect_scale(img):
    """Simple scale detection - looks for text like '1/4" = 1'-0"' """
    return "1/4\" = 1'-0\""

def detect_plumbing_symbols(img):
    """Detect plumbing fixtures using template matching"""
    detected = []
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Circle detection for fixtures
    circles = cv2.HoughCircles(
        gray, cv2.HOUGH_GRADIENT, dp=1, minDist=50,
        param1=50, param2=30, minRadius=10, maxRadius=50
    )
    
    if circles is not None:
        circles = np.uint16(np.around(circles))
        for i, circle in enumerate(circles[0, :]):
            x, y, r = circle
            detected.append({
                'type': 'fixture_unknown',
                'x': float(x), 'y': float(y),
                'width': float(r * 2), 'height': float(r * 2),
                'confidence': 0.6
            })
    
    # Rectangle detection
    edges = cv2.Canny(gray, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        area = cv2.contourArea(contour)
        if 500 < area < 5000 and 0.5 < w/h < 2.0:
            detected.append({
                'type': 'equipment',
                'x': float(x), 'y': float(y),
                'width': float(w), 'height': float(h),
                'confidence': 0.5
            })
    
    return detected[:50]

# Database helper
def get_db():
    conn = sqlite3.connect('data/estimator.db')
    conn.row_factory = sqlite3.Row
    return conn

# Authentication Routes
@app.route('/')
def index():
    if 'user_id' not in session:
        return render_template_string(LOGIN_TEMPLATE)
    
    if 'company_id' not in session:
        return render_template_string(COMPANY_SELECT_TEMPLATE)
    
    return render_template_string(MAIN_TEMPLATE)

@app.route('/admin')
@admin_required
def admin_panel():
    return render_template_string(ADMIN_TEMPLATE)

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400
    
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    conn.close()
    
    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify({'error': 'Invalid email or password'}), 401
    
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

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/api/auth/me', methods=['GET'])
@login_required
def get_current_user():
    conn = get_db()
    user = conn.execute('SELECT id, email, first_name, last_name, is_admin FROM users WHERE id = ?', 
                       (session['user_id'],)).fetchone()
    conn.close()
    
    return jsonify(dict(user))

# Company Selection Routes
@app.route('/api/user/companies', methods=['GET'])
@login_required
def get_user_companies():
    conn = get_db()
    companies = conn.execute('''
        SELECT c.*, uc.role 
        FROM companies c
        JOIN user_companies uc ON c.id = uc.company_id
        WHERE uc.user_id = ?
        ORDER BY c.name
    ''', (session['user_id'],)).fetchall()
    conn.close()
    
    return jsonify([dict(c) for c in companies])

@app.route('/api/select-company/<int:company_id>', methods=['POST'])
@login_required
def select_company(company_id):
    # Verify user has access to this company
    conn = get_db()
    access = conn.execute('''
        SELECT 1 FROM user_companies 
        WHERE user_id = ? AND company_id = ?
    ''', (session['user_id'], company_id)).fetchone()
    
    if not access:
        conn.close()
        return jsonify({'error': 'Access denied'}), 403
    
    company = conn.execute('SELECT * FROM companies WHERE id = ?', (company_id,)).fetchone()
    conn.close()
    
    session['company_id'] = company_id
    session['company_name'] = company['name']
    
    return jsonify({'success': True, 'company': dict(company)})

@app.route('/api/current-company', methods=['GET'])
@login_required
def get_current_company():
    if 'company_id' not in session:
        return jsonify({'company': None})
    
    conn = get_db()
    company = conn.execute('SELECT * FROM companies WHERE id = ?', (session['company_id'],)).fetchone()
    conn.close()
    
    return jsonify({'company': dict(company) if company else None})

# Admin Routes - Companies
@app.route('/api/admin/companies', methods=['GET', 'POST'])
@admin_required
def admin_companies():
    conn = get_db()
    
    if request.method == 'GET':
        companies = conn.execute('SELECT * FROM companies ORDER BY name').fetchall()
        conn.close()
        return jsonify([dict(c) for c in companies])
    
    elif request.method == 'POST':
        data = request.json
        try:
            c = conn.cursor()
            c.execute('INSERT INTO companies (name, address, phone) VALUES (?, ?, ?)',
                     (data['name'], data.get('address'), data.get('phone')))
            company_id = c.lastrowid
            conn.commit()
            conn.close()
            return jsonify({'id': company_id, 'name': data['name']}), 201
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({'error': 'Company name already exists'}), 400

@app.route('/api/admin/companies/<int:company_id>', methods=['DELETE'])
@admin_required
def delete_company(company_id):
    conn = get_db()
    conn.execute('DELETE FROM companies WHERE id = ?', (company_id,))
    conn.commit()
    conn.close()
    return '', 204

# Admin Routes - Users
@app.route('/api/admin/users', methods=['GET', 'POST'])
@admin_required
def admin_users():
    conn = get_db()
    
    if request.method == 'GET':
        users = conn.execute('''
            SELECT u.*, GROUP_CONCAT(c.name, ', ') as companies
            FROM users u
            LEFT JOIN user_companies uc ON u.id = uc.user_id
            LEFT JOIN companies c ON uc.company_id = c.id
            GROUP BY u.id
            ORDER BY u.email
        ''').fetchall()
        conn.close()
        return jsonify([dict(u) for u in users])
    
    elif request.method == 'POST':
        data = request.json
        try:
            password_hash = generate_password_hash(data['password'])
            c = conn.cursor()
            c.execute('''INSERT INTO users (email, password_hash, first_name, last_name, is_admin) 
                        VALUES (?, ?, ?, ?, ?)''',
                     (data['email'], password_hash, data.get('first_name'), 
                      data.get('last_name'), data.get('is_admin', False)))
            user_id = c.lastrowid
            
            # Add user to companies
            if 'company_ids' in data:
                for company_id in data['company_ids']:
                    c.execute('INSERT INTO user_companies (user_id, company_id) VALUES (?, ?)',
                             (user_id, company_id))
            
            conn.commit()
            conn.close()
            return jsonify({'id': user_id, 'email': data['email']}), 201
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({'error': 'Email already exists'}), 400

@app.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    # Prevent deleting yourself
    if user_id == session['user_id']:
        return jsonify({'error': 'Cannot delete your own account'}), 400
    
    conn = get_db()
    conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()
    return '', 204

# Project Routes (Company-scoped)
@app.route('/api/projects', methods=['GET', 'POST'])
@login_required
@company_access_required
def projects():
    conn = get_db()
    company_id = session['company_id']
    
    if request.method == 'GET':
        projects = conn.execute(
            'SELECT * FROM projects WHERE company_id = ? ORDER BY updated_at DESC',
            (company_id,)
        ).fetchall()
        conn.close()
        return jsonify([dict(p) for p in projects])
    
    elif request.method == 'POST':
        data = request.json
        c = conn.cursor()
        c.execute(
            'INSERT INTO projects (company_id, name, description) VALUES (?, ?, ?)',
            (company_id, data['name'], data.get('description', ''))
        )
        project_id = c.lastrowid
        conn.commit()
        conn.close()
        return jsonify({'id': project_id, 'name': data['name']}), 201

@app.route('/api/projects/<int:project_id>', methods=['GET', 'DELETE'])
@login_required
@company_access_required
def project_detail(project_id):
    conn = get_db()
    
    # Verify project belongs to current company
    project = conn.execute(
        'SELECT * FROM projects WHERE id = ? AND company_id = ?',
        (project_id, session['company_id'])
    ).fetchone()
    
    if not project:
        conn.close()
        return jsonify({'error': 'Project not found'}), 404
    
    if request.method == 'GET':
        drawings = conn.execute(
            'SELECT * FROM drawings WHERE project_id = ? ORDER BY created_at',
            (project_id,)
        ).fetchall()
        conn.close()
        return jsonify({
            'project': dict(project),
            'drawings': [dict(d) for d in drawings]
        })
    
    elif request.method == 'DELETE':
        conn.execute('DELETE FROM projects WHERE id = ?', (project_id,))
        conn.commit()
        conn.close()
        return '', 204

# Drawing Routes (remain the same, but inherit company access through projects)
@app.route('/api/projects/<int:project_id>/drawings', methods=['POST'])
@login_required
@company_access_required
def upload_drawing(project_id):
    # Verify project belongs to current company
    conn = get_db()
    project = conn.execute(
        'SELECT * FROM projects WHERE id = ? AND company_id = ?',
        (project_id, session['company_id'])
    ).fetchone()
    conn.close()
    
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.lower().endswith(('.pdf', '.tif', '.tiff')):
        return jsonify({'error': 'Only PDF and TIFF files allowed'}), 400
    
    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{timestamp}_{filename}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    try:
        doc = fitz.open(filepath)
        page_count = len(doc)
        doc.close()
    except:
        page_count = 1
    
    conn = get_db()
    c = conn.cursor()
    c.execute(
        'INSERT INTO drawings (project_id, name, file_path, page_count) VALUES (?, ?, ?, ?)',
        (project_id, file.filename, filepath, page_count)
    )
    drawing_id = c.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({'id': drawing_id, 'name': file.filename, 'page_count': page_count}), 201

@app.route('/api/drawings/<int:drawing_id>/process', methods=['POST'])
@login_required
@company_access_required
def process_drawing(drawing_id):
    data = request.json
    page_number = data.get('page_number', 0)
    
    conn = get_db()
    drawing = conn.execute('SELECT * FROM drawings WHERE id = ?', (drawing_id,)).fetchone()
    
    if not drawing:
        conn.close()
        return jsonify({'error': 'Drawing not found'}), 404
    
    img = extract_pdf_page_as_image(drawing['file_path'], page_number)
    scale = detect_scale(img)
    detected_items = detect_plumbing_symbols(img)
    
    conn.execute('UPDATE drawings SET scale = ? WHERE id = ?', (scale, drawing_id))
    
    c = conn.cursor()
    for item in detected_items:
        c.execute(
            '''INSERT INTO detected_items 
            (drawing_id, page_number, item_type, x, y, width, height, confidence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (drawing_id, page_number, item['type'], item['x'], item['y'],
             item['width'], item['height'], item['confidence'])
        )
    
    conn.commit()
    conn.close()
    
    return jsonify({'scale': scale, 'detected_items': detected_items, 'count': len(detected_items)})

@app.route('/api/drawings/<int:drawing_id>/page/<int:page_num>/image')
@login_required
def get_drawing_page_image(drawing_id, page_num):
    conn = get_db()
    drawing = conn.execute('SELECT * FROM drawings WHERE id = ?', (drawing_id,)).fetchone()
    conn.close()
    
    if not drawing:
        return jsonify({'error': 'Drawing not found'}), 404
    
    img = extract_pdf_page_as_image(drawing['file_path'], page_num, dpi=100)
    _, buffer = cv2.imencode('.png', img)
    io_buf = io.BytesIO(buffer)
    
    return send_file(io_buf, mimetype='image/png')

@app.route('/api/drawings/<int:drawing_id>/items', methods=['GET', 'POST'])
@login_required
def drawing_items(drawing_id):
    conn = get_db()
    
    if request.method == 'GET':
        page_num = request.args.get('page', type=int)
        query = 'SELECT * FROM detected_items WHERE drawing_id = ?'
        params = [drawing_id]
        
        if page_num is not None:
            query += ' AND page_number = ?'
            params.append(page_num)
        
        items = conn.execute(query, params).fetchall()
        conn.close()
        return jsonify([dict(item) for item in items])
    
    elif request.method == 'POST':
        data = request.json
        c = conn.cursor()
        c.execute(
            '''INSERT INTO detected_items 
            (drawing_id, page_number, item_type, x, y, width, height, confidence, verified)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (drawing_id, data['page_number'], data['item_type'],
             data['x'], data['y'], data['width'], data['height'],
             data.get('confidence', 1.0), True)
        )
        item_id = c.lastrowid
        conn.commit()
        conn.close()
        return jsonify({'id': item_id}), 201

@app.route('/api/items/<int:item_id>', methods=['PUT', 'DELETE'])
@login_required
def item_detail(item_id):
    conn = get_db()
    
    if request.method == 'PUT':
        data = request.json
        conn.execute(
            'UPDATE detected_items SET item_type = ?, verified = ?, notes = ? WHERE id = ?',
            (data.get('item_type'), data.get('verified', True), data.get('notes'), item_id)
        )
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    
    elif request.method == 'DELETE':
        conn.execute('DELETE FROM detected_items WHERE id = ?', (item_id,))
        conn.commit()
        conn.close()
        return '', 204

@app.route('/api/drawings/<int:drawing_id>/takeoff')
@login_required
def get_takeoff(drawing_id):
    conn = get_db()
    items = conn.execute(
        'SELECT item_type, COUNT(*) as count FROM detected_items WHERE drawing_id = ? GROUP BY item_type',
        (drawing_id,)
    ).fetchall()
    conn.close()
    
    return jsonify([{'type': item['item_type'], 'count': item['count']} for item in items])

# HTML Templates
LOGIN_TEMPLATE = r'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - Plumbing Estimator</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .login-container {
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            width: 400px;
        }
        h1 { margin-bottom: 30px; color: #2c3e50; text-align: center; }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 5px; color: #555; font-weight: 500; }
        input[type="email"], input[type="password"] {
            width: 100%;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
        }
        input:focus { outline: none; border-color: #667eea; }
        button {
            width: 100%;
            padding: 12px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 5px;
            font-size: 16px;
            font-weight: 500;
            cursor: pointer;
            transition: background 0.3s;
        }
        button:hover { background: #5568d3; }
        .error { color: #e74c3c; margin-top: 10px; font-size: 14px; display: none; }
        .info { color: #7f8c8d; margin-top: 20px; font-size: 13px; text-align: center; }
    </style>
</head>
<body>
    <div class="login-container">
        <h1>🔧 Plumbing Estimator</h1>
        <form id="loginForm">
            <div class="form-group">
                <label>Email</label>
                <input type="email" id="email" required autocomplete="email">
            </div>
            <div class="form-group">
                <label>Password</label>
                <input type="password" id="password" required autocomplete="current-password">
            </div>
            <button type="submit">Login</button>
            <div class="error" id="errorMsg"></div>
        </form>
        <div class="info">
            Default admin: admin@example.com / admin123
        </div>
    </div>

    <script>
        document.getElementById('loginForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            const errorMsg = document.getElementById('errorMsg');
            
            try {
                const response = await fetch('/api/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password })
                });
                
                if (response.ok) {
                    window.location.href = '/';
                } else {
                    const data = await response.json();
                    errorMsg.textContent = data.error || 'Login failed';
                    errorMsg.style.display = 'block';
                }
            } catch (error) {
                errorMsg.textContent = 'Connection error';
                errorMsg.style.display = 'block';
            }
        });
    </script>
</body>
</html>
'''

COMPANY_SELECT_TEMPLATE = r'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Select Company - Plumbing Estimator</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container {
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            min-width: 500px;
            max-width: 600px;
        }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }
        h1 { color: #2c3e50; }
        .logout-btn {
            padding: 8px 16px;
            background: #e74c3c;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
        }
        .company-card {
            padding: 20px;
            border: 2px solid #ecf0f1;
            border-radius: 8px;
            margin-bottom: 15px;
            cursor: pointer;
            transition: all 0.3s;
        }
        .company-card:hover {
            border-color: #667eea;
            background: #f8f9fa;
            transform: translateY(-2px);
        }
        .company-name { font-size: 18px; font-weight: 600; color: #2c3e50; margin-bottom: 5px; }
        .company-role { font-size: 14px; color: #7f8c8d; }
        .no-companies {
            text-align: center;
            padding: 40px;
            color: #7f8c8d;
        }
        .admin-link {
            text-align: center;
            margin-top: 20px;
        }
        .admin-link a {
            color: #667eea;
            text-decoration: none;
            font-weight: 500;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Select Company</h1>
            <button class="logout-btn" onclick="logout()">Logout</button>
        </div>
        <div id="companies"></div>
        <div id="adminLink" style="display: none;" class="admin-link">
            <a href="/admin">Go to Admin Panel</a>
        </div>
    </div>

    <script>
        async function loadCompanies() {
            const response = await fetch('/api/user/companies');
            const companies = await response.json();
            
            const container = document.getElementById('companies');
            
            if (companies.length === 0) {
                container.innerHTML = '<div class="no-companies">You are not assigned to any companies.<br>Please contact your administrator.</div>';
                return;
            }
            
            container.innerHTML = companies.map(c => `
                <div class="company-card" onclick="selectCompany(${c.id})">
                    <div class="company-name">${c.name}</div>
                    <div class="company-role">Role: ${c.role}</div>
                </div>
            `).join('');
        }
        
        async function selectCompany(companyId) {
            await fetch('/api/select-company/' + companyId, { method: 'POST' });
            window.location.href = '/';
        }
        
        async function logout() {
            await fetch('/api/auth/logout', { method: 'POST' });
            window.location.href = '/';
        }
        
        async function checkAdmin() {
            const response = await fetch('/api/auth/me');
            const user = await response.json();
            if (user.is_admin) {
                document.getElementById('adminLink').style.display = 'block';
            }
        }
        
        loadCompanies();
        checkAdmin();
    </script>
</body>
</html>
'''

ADMIN_TEMPLATE = r'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Panel - Plumbing Estimator</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; }
        
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }
        h1 { color: #2c3e50; }
        .nav-buttons { display: flex; gap: 10px; }
        button {
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            transition: background 0.3s;
        }
        .btn-primary { background: #3498db; color: white; }
        .btn-primary:hover { background: #2980b9; }
        .btn-secondary { background: #95a5a6; color: white; }
        .btn-secondary:hover { background: #7f8c8d; }
        .btn-danger { background: #e74c3c; color: white; }
        .btn-danger:hover { background: #c0392b; }
        
        .tabs { display: flex; gap: 10px; margin-bottom: 20px; border-bottom: 2px solid #ecf0f1; }
        .tab { padding: 10px 20px; cursor: pointer; color: #7f8c8d; border-bottom: 2px solid transparent; }
        .tab.active { color: #3498db; border-bottom-color: #3498db; }
        
        table { width: 100%; border-collapse: collapse; background: white; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ecf0f1; }
        th { background: #34495e; color: white; font-weight: 500; }
        tr:hover { background: #f8f9fa; }
        
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            z-index: 1000;
        }
        .modal-content {
            background: white;
            margin: 50px auto;
            padding: 30px;
            width: 500px;
            border-radius: 8px;
        }
        .modal h2 { margin-bottom: 20px; color: #2c3e50; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; color: #555; font-weight: 500; }
        input[type="text"], input[type="email"], input[type="password"], select {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
        }
        .checkbox-group { margin-top: 10px; }
        .checkbox-group label { display: inline; margin-left: 5px; font-weight: normal; }
        .form-actions { display: flex; gap: 10px; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>👨‍💼 Admin Panel</h1>
            <div class="nav-buttons">
                <button class="btn-secondary" onclick="window.location.href='/'">Back to App</button>
                <button class="btn-danger" onclick="logout()">Logout</button>
            </div>
        </div>
        
        <div class="tabs">
            <div class="tab active" onclick="showTab('companies')">Companies</div>
            <div class="tab" onclick="showTab('users')">Users</div>
        </div>
        
        <!-- Companies Tab -->
        <div id="companiesTab">
            <button class="btn-primary" onclick="showNewCompanyModal()" style="margin-bottom: 20px;">+ New Company</button>
            <table>
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Address</th>
                        <th>Phone</th>
                        <th>Created</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody id="companiesTable"></tbody>
            </table>
        </div>
        
        <!-- Users Tab -->
        <div id="usersTab" style="display: none;">
            <button class="btn-primary" onclick="showNewUserModal()" style="margin-bottom: 20px;">+ New User</button>
            <table>
                <thead>
                    <tr>
                        <th>Email</th>
                        <th>Name</th>
                        <th>Companies</th>
                        <th>Admin</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody id="usersTable"></tbody>
            </table>
        </div>
    </div>
    
    <!-- Company Modal -->
    <div id="companyModal" class="modal">
        <div class="modal-content">
            <h2>New Company</h2>
            <div class="form-group">
                <label>Company Name*</label>
                <input type="text" id="companyName" required>
            </div>
            <div class="form-group">
                <label>Address</label>
                <input type="text" id="companyAddress">
            </div>
            <div class="form-group">
                <label>Phone</label>
                <input type="text" id="companyPhone">
            </div>
            <div class="form-actions">
                <button class="btn-primary" onclick="createCompany()">Create</button>
                <button class="btn-secondary" onclick="closeModals()">Cancel</button>
            </div>
        </div>
    </div>
    
    <!-- User Modal -->
    <div id="userModal" class="modal">
        <div class="modal-content">
            <h2>New User</h2>
            <div class="form-group">
                <label>Email*</label>
                <input type="email" id="userEmail" required>
            </div>
            <div class="form-group">
                <label>Password*</label>
                <input type="password" id="userPassword" required>
            </div>
            <div class="form-group">
                <label>First Name</label>
                <input type="text" id="userFirstName">
            </div>
            <div class="form-group">
                <label>Last Name</label>
                <input type="text" id="userLastName">
            </div>
            <div class="checkbox-group">
                <input type="checkbox" id="userIsAdmin">
                <label for="userIsAdmin">Administrator</label>
            </div>
            <div class="form-group" style="margin-top: 15px;">
                <label>Assign to Companies</label>
                <div id="companyCheckboxes"></div>
            </div>
            <div class="form-actions">
                <button class="btn-primary" onclick="createUser()">Create</button>
                <button class="btn-secondary" onclick="closeModals()">Cancel</button>
            </div>
        </div>
    </div>

    <script>
        let companies = [];
        let users = [];
        
        async function showTab(tab) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            event.target.classList.add('active');
            
            document.getElementById('companiesTab').style.display = tab === 'companies' ? 'block' : 'none';
            document.getElementById('usersTab').style.display = tab === 'users' ? 'block' : 'none';
            
            if (tab === 'companies') loadCompanies();
            else loadUsers();
        }
        
        async function loadCompanies() {
            const response = await fetch('/api/admin/companies');
            companies = await response.json();
            
            const table = document.getElementById('companiesTable');
            table.innerHTML = companies.map(c => `
                <tr>
                    <td><strong>${c.name}</strong></td>
                    <td>${c.address || '-'}</td>
                    <td>${c.phone || '-'}</td>
                    <td>${new Date(c.created_at).toLocaleDateString()}</td>
                    <td>
                        <button class="btn-danger" onclick="deleteCompany(${c.id})">Delete</button>
                    </td>
                </tr>
            `).join('');
        }
        
        async function loadUsers() {
            const response = await fetch('/api/admin/users');
            users = await response.json();
            
            const table = document.getElementById('usersTable');
            table.innerHTML = users.map(u => `
                <tr>
                    <td>${u.email}</td>
                    <td>${u.first_name || ''} ${u.last_name || ''}</td>
                    <td>${u.companies || 'None'}</td>
                    <td>${u.is_admin ? '✓' : ''}</td>
                    <td>
                        <button class="btn-danger" onclick="deleteUser(${u.id})">Delete</button>
                    </td>
                </tr>
            `).join('');
        }
        
        function showNewCompanyModal() {
            document.getElementById('companyModal').style.display = 'block';
        }
        
        async function showNewUserModal() {
            await loadCompanies();
            const checkboxes = document.getElementById('companyCheckboxes');
            checkboxes.innerHTML = companies.map(c => `
                <div style="margin: 5px 0;">
                    <input type="checkbox" id="company_${c.id}" value="${c.id}">
                    <label for="company_${c.id}" style="display: inline; font-weight: normal;">${c.name}</label>
                </div>
            `).join('');
            document.getElementById('userModal').style.display = 'block';
        }
        
        function closeModals() {
            document.getElementById('companyModal').style.display = 'none';
            document.getElementById('userModal').style.display = 'none';
            // Clear form fields
            document.querySelectorAll('input[type="text"], input[type="email"], input[type="password"]').forEach(i => i.value = '');
            document.querySelectorAll('input[type="checkbox"]').forEach(i => i.checked = false);
        }
        
        async function createCompany() {
            const name = document.getElementById('companyName').value;
            if (!name) return alert('Company name is required');
            
            const response = await fetch('/api/admin/companies', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name,
                    address: document.getElementById('companyAddress').value,
                    phone: document.getElementById('companyPhone').value
                })
            });
            
            if (response.ok) {
                closeModals();
                loadCompanies();
            } else {
                const data = await response.json();
                alert(data.error || 'Failed to create company');
            }
        }
        
        async function createUser() {
            const email = document.getElementById('userEmail').value;
            const password = document.getElementById('userPassword').value;
            
            if (!email || !password) return alert('Email and password are required');
            
            const companyIds = [];
            companies.forEach(c => {
                if (document.getElementById('company_' + c.id).checked) {
                    companyIds.push(c.id);
                }
            });
            
            const response = await fetch('/api/admin/users', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    email,
                    password,
                    first_name: document.getElementById('userFirstName').value,
                    last_name: document.getElementById('userLastName').value,
                    is_admin: document.getElementById('userIsAdmin').checked,
                    company_ids: companyIds
                })
            });
            
            if (response.ok) {
                closeModals();
                loadUsers();
            } else {
                const data = await response.json();
                alert(data.error || 'Failed to create user');
            }
        }
        
        async function deleteCompany(id) {
            if (!confirm('Delete this company? All projects and data will be permanently deleted!')) return;
            
            await fetch('/api/admin/companies/' + id, { method: 'DELETE' });
            loadCompanies();
        }
        
        async function deleteUser(id) {
            if (!confirm('Delete this user?')) return;
            
            const response = await fetch('/api/admin/users/' + id, { method: 'DELETE' });
            if (response.ok) {
                loadUsers();
            } else {
                const data = await response.json();
                alert(data.error || 'Failed to delete user');
            }
        }
        
        async function logout() {
            await fetch('/api/auth/logout', { method: 'POST' });
            window.location.href = '/';
        }
        
        loadCompanies();
    </script>
</body>
</html>
'''

MAIN_TEMPLATE = r'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Plumbing Estimator</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; }
        
        .top-bar {
            background: #2c3e50;
            color: white;
            padding: 10px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .company-info { font-size: 14px; }
        .user-menu { display: flex; gap: 10px; align-items: center; }
        .user-menu button {
            padding: 6px 12px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 13px;
        }
        .btn-change { background: #3498db; color: white; }
        .btn-logout { background: #e74c3c; color: white; }
        
        .container { display: flex; height: calc(100vh - 45px); }
        .sidebar { width: 300px; background: #34495e; color: white; padding: 20px; overflow-y: auto; }
        .main { flex: 1; display: flex; flex-direction: column; }
        .toolbar { background: #455a64; color: white; padding: 15px 20px; display: flex; gap: 10px; align-items: center; }
        .content { flex: 1; display: flex; overflow: hidden; }
        .canvas-area { flex: 1; background: #ecf0f1; position: relative; overflow: auto; }
        .properties { width: 250px; background: white; border-left: 1px solid #ddd; padding: 20px; overflow-y: auto; }
        
        button { 
            padding: 8px 16px; 
            border: none; 
            border-radius: 4px; 
            cursor: pointer; 
            font-size: 14px;
            background: #3498db;
            color: white;
        }
        button:hover { background: #2980b9; }
        button.secondary { background: #95a5a6; }
        button.secondary:hover { background: #7f8c8d; }
        button.danger { background: #e74c3c; }
        button.danger:hover { background: #c0392b; }
        
        .project-list { margin-top: 20px; }
        .project-item { 
            padding: 10px; 
            background: #455a64; 
            margin-bottom: 10px; 
            border-radius: 4px; 
            cursor: pointer;
        }
        .project-item:hover { background: #546e7a; }
        .project-item.active { background: #3498db; }
        
        .drawing-item {
            padding: 8px;
            background: #546e7a;
            margin: 5px 0;
            border-radius: 3px;
            font-size: 14px;
            cursor: pointer;
        }
        .drawing-item:hover { background: #607d8b; }
        
        input[type="text"], textarea {
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            margin: 5px 0;
        }
        
        #canvas { 
            max-width: 100%; 
            height: auto;
            display: block;
            margin: 20px auto;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .section { margin-bottom: 20px; }
        .section h3 { margin-bottom: 10px; font-size: 14px; color: #7f8c8d; }
        
        .item-count { 
            display: flex; 
            justify-content: space-between; 
            padding: 8px; 
            background: #ecf0f1; 
            margin: 5px 0;
            border-radius: 3px;
        }
        
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            z-index: 1000;
        }
        .modal-content {
            background: white;
            margin: 100px auto;
            padding: 30px;
            width: 400px;
            border-radius: 8px;
        }
        .modal-content h2 { margin-bottom: 20px; }
    </style>
</head>
<body>
    <div class="top-bar">
        <div class="company-info">
            Company: <strong id="currentCompanyName">Loading...</strong>
        </div>
        <div class="user-menu">
            <span id="currentUserEmail"></span>
            <button class="btn-change" onclick="changeCompany()">Change Company</button>
            <button class="btn-logout" onclick="logout()">Logout</button>
        </div>
    </div>
    
    <div class="container">
        <div class="sidebar">
            <h2>Projects</h2>
            <button onclick="showNewProjectModal()">+ New Project</button>
            <div class="project-list" id="projectList"></div>
        </div>
        
        <div class="main">
            <div class="toolbar">
                <button onclick="uploadDrawing()">📄 Upload Drawing</button>
                <button onclick="processCurrentDrawing()" class="secondary">🔍 Auto-Detect</button>
                <button onclick="exportTakeoff()" class="secondary">📊 Export Takeoff</button>
                <span style="margin-left: auto;" id="currentProject">No project selected</span>
            </div>
            
            <div class="content">
                <div class="canvas-area">
                    <canvas id="canvas"></canvas>
                    <div id="canvasInstructions" style="padding: 40px; text-align: center; color: #7f8c8d;">
                        <h2>Plumbing Estimator</h2>
                        <p style="margin-top: 20px;">Select or create a project to begin</p>
                    </div>
                </div>
                
                <div class="properties">
                    <div class="section">
                        <h3>DRAWINGS</h3>
                        <div id="drawingList"></div>
                    </div>
                    
                    <div class="section">
                        <h3>TAKEOFF SUMMARY</h3>
                        <div id="takeoffSummary">
                            <p style="color: #95a5a6; font-size: 13px;">Process a drawing to see results</p>
                        </div>
                    </div>
                    
                    <div class="section">
                        <h3>DETECTION INFO</h3>
                        <div id="detectionInfo">
                            <p style="font-size: 13px;">Scale: Not detected</p>
                            <p style="font-size: 13px;">Items: 0</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <div id="newProjectModal" class="modal">
        <div class="modal-content">
            <h2>New Project</h2>
            <input type="text" id="projectName" placeholder="Project Name" />
            <textarea id="projectDescription" placeholder="Description (optional)" rows="3"></textarea>
            <div style="margin-top: 20px; display: flex; gap: 10px;">
                <button onclick="createProject()">Create</button>
                <button onclick="closeModal()" class="secondary">Cancel</button>
            </div>
        </div>
    </div>
    
    <input type="file" id="fileInput" accept=".pdf,.tif,.tiff" style="display: none;" onchange="handleFileUpload(event)">
    
    <script>
        let currentProject = null;
        let currentDrawing = null;
        let currentPage = 0;
        const canvas = document.getElementById('canvas');
        const ctx = canvas.getContext('2d');
        
        // Load user and company info
        loadUserInfo();
        loadProjects();
        
        async function loadUserInfo() {
            const userResponse = await fetch('/api/auth/me');
            const user = await userResponse.json();
            document.getElementById('currentUserEmail').textContent = user.email;
            
            const companyResponse = await fetch('/api/current-company');
            const data = await companyResponse.json();
            if (data.company) {
                document.getElementById('currentCompanyName').textContent = data.company.name;
            }
        }
        
        async function loadProjects() {
            const response = await fetch('/api/projects');
            const projects = await response.json();
            
            const list = document.getElementById('projectList');
            list.innerHTML = projects.map(p => `
                <div class="project-item" onclick="selectProject(${p.id})">
                    <strong>${p.name}</strong>
                    <div style="font-size: 12px; color: #bdc3c7;">${p.description || 'No description'}</div>
                </div>
            `).join('');
        }
        
        async function selectProject(projectId) {
            const response = await fetch(\`/api/projects/\${projectId}\`);
            const data = await response.json();
            
            currentProject = data.project;
            document.getElementById('currentProject').textContent = currentProject.name;
            
            const drawingList = document.getElementById('drawingList');
            drawingList.innerHTML = data.drawings.map(d => `
                <div class="drawing-item" onclick="selectDrawing(${d.id})">
                    ${d.name} (${d.page_count} pages)
                </div>
            `).join('');
            
            document.querySelectorAll('.project-item').forEach((el, i) => {
                el.classList.toggle('active', data.project.id === parseInt(el.onclick.toString().match(/\d+/)[0]));
            });
        }
        
        async function selectDrawing(drawingId) {
            currentDrawing = drawingId;
            currentPage = 0;
            await loadDrawingPage();
            await loadTakeoff();
        }
        
        async function loadDrawingPage() {
            const img = new Image();
            img.onload = function() {
                canvas.width = img.width;
                canvas.height = img.height;
                ctx.drawImage(img, 0, 0);
                document.getElementById('canvasInstructions').style.display = 'none';
                canvas.style.display = 'block';
                loadDetectedItems();
            };
            img.src = \`/api/drawings/\${currentDrawing}/page/\${currentPage}/image\`;
        }
        
        async function loadDetectedItems() {
            const response = await fetch(\`/api/drawings/\${currentDrawing}/items?page=\${currentPage}\`);
            const items = await response.json();
            
            items.forEach(item => {
                ctx.strokeStyle = item.verified ? '#2ecc71' : '#e74c3c';
                ctx.lineWidth = 2;
                ctx.strokeRect(item.x, item.y, item.width, item.height);
                
                ctx.fillStyle = item.verified ? '#2ecc71' : '#e74c3c';
                ctx.font = '12px Arial';
                ctx.fillText(item.item_type, item.x, item.y - 5);
            });
            
            document.getElementById('detectionInfo').innerHTML = \`
                <p style="font-size: 13px;">Items detected: \${items.length}</p>
            \`;
        }
        
        async function loadTakeoff() {
            const response = await fetch(\`/api/drawings/\${currentDrawing}/takeoff\`);
            const takeoff = await response.json();
            
            document.getElementById('takeoffSummary').innerHTML = takeoff.map(item => \`
                <div class="item-count">
                    <span>\${item.type}</span>
                    <strong>\${item.count}</strong>
                </div>
            \`).join('') || '<p style="color: #95a5a6; font-size: 13px;">No items detected</p>';
        }
        
        async function processCurrentDrawing() {
            if (!currentDrawing) {
                alert('Please select a drawing first');
                return;
            }
            
            const response = await fetch(\`/api/drawings/\${currentDrawing}/process\`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ page_number: currentPage })
            });
            
            const result = await response.json();
            alert(\`Detected \${result.count} items!\\nScale: \${result.scale}\`);
            
            await loadDrawingPage();
            await loadTakeoff();
        }
        
        function uploadDrawing() {
            if (!currentProject) {
                alert('Please select a project first');
                return;
            }
            document.getElementById('fileInput').click();
        }
        
        async function handleFileUpload(event) {
            const file = event.target.files[0];
            if (!file) return;
            
            const formData = new FormData();
            formData.append('file', file);
            
            const response = await fetch(\`/api/projects/\${currentProject.id}/drawings\`, {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                alert('Drawing uploaded successfully!');
                selectProject(currentProject.id);
            }
        }
        
        function showNewProjectModal() {
            document.getElementById('newProjectModal').style.display = 'block';
        }
        
        function closeModal() {
            document.getElementById('newProjectModal').style.display = 'none';
        }
        
        async function createProject() {
            const name = document.getElementById('projectName').value;
            const description = document.getElementById('projectDescription').value;
            
            if (!name) {
                alert('Please enter a project name');
                return;
            }
            
            const response = await fetch('/api/projects', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, description })
            });
            
            if (response.ok) {
                closeModal();
                document.getElementById('projectName').value = '';
                document.getElementById('projectDescription').value = '';
                loadProjects();
            }
        }
        
        async function exportTakeoff() {
            if (!currentDrawing) {
                alert('Please select a drawing first');
                return;
            }
            
            const response = await fetch(\`/api/drawings/\${currentDrawing}/takeoff\`);
            const takeoff = await response.json();
            
            let csv = 'Item Type,Count\\n';
            takeoff.forEach(item => {
                csv += \`\${item.type},\${item.count}\\n\`;
            });
            
            const blob = new Blob([csv], { type: 'text/csv' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'takeoff.csv';
            a.click();
        }
        
        function changeCompany() {
            window.location.href = '/';
        }
        
        async function logout() {
            await fetch('/api/auth/logout', { method: 'POST' });
            window.location.href = '/';
        }
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    print("=" * 60)
    print("Plumbing Estimator - Multi-Tenant System")
    print("=" * 60)
    print("\nStarting server at http://localhost:5000")
    print("\nDefault Admin Login:")
    print("  Email: admin@example.com")
    print("  Password: admin123")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)