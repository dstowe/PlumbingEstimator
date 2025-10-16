# database/materials_db.py
"""
Materials Database Schema and Functions
"""
import sqlite3
from database.db import get_db

# Default Materials Database - Schedule 40 PVC and DWV Fittings
DEFAULT_MATERIALS = [
    # Schedule 40 PVC Pipe
    ('PVC04005', 'PVC Sch 40 Pipe', '1/2" Sch 40 PVC Plain End Pipe', '1/2"', 'LF', 0.85, 0.05),
    ('PVC04007', 'PVC Sch 40 Pipe', '3/4" Sch 40 PVC Plain End Pipe', '3/4"', 'LF', 1.15, 0.06),
    ('PVC04010', 'PVC Sch 40 Pipe', '1" Sch 40 PVC Plain End Pipe', '1"', 'LF', 1.45, 0.07),
    ('PVC04012', 'PVC Sch 40 Pipe', '1-1/4" Sch 40 PVC Plain End Pipe', '1-1/4"', 'LF', 1.95, 0.08),
    ('PVC04015', 'PVC Sch 40 Pipe', '1-1/2" Sch 40 PVC Plain End Pipe', '1-1/2"', 'LF', 2.35, 0.09),
    ('PVC04020', 'PVC Sch 40 Pipe', '2" Sch 40 PVC Plain End Pipe', '2"', 'LF', 3.25, 0.10),
    ('PVC04025', 'PVC Sch 40 Pipe', '2-1/2" Sch 40 PVC Plain End Pipe', '2-1/2"', 'LF', 5.15, 0.12),
    ('PVC04030', 'PVC Sch 40 Pipe', '3" Sch 40 PVC Plain End Pipe', '3"', 'LF', 6.85, 0.14),
    ('PVC04040', 'PVC Sch 40 Pipe', '4" Sch 40 PVC Plain End Pipe', '4"', 'LF', 10.25, 0.16),
    ('PVC04060', 'PVC Sch 40 Pipe', '6" Sch 40 PVC Plain End Pipe', '6"', 'LF', 18.50, 0.20),
    ('PVC04080', 'PVC Sch 40 Pipe', '8" Sch 40 PVC Plain End Pipe', '8"', 'LF', 32.75, 0.25),
    
    # PVC DWV 90° Elbows
    ('PVC00402', 'PVC DWV Fittings', '1-1/2" PVC DWV 90° Elbow', '1-1/2"', 'EA', 2.15, 0.15),
    ('PVC00404', 'PVC DWV Fittings', '2" PVC DWV 90° Elbow', '2"', 'EA', 2.85, 0.17),
    ('PVC00406', 'PVC DWV Fittings', '3" PVC DWV 90° Elbow', '3"', 'EA', 5.25, 0.20),
    ('PVC00408', 'PVC DWV Fittings', '4" PVC DWV 90° Elbow', '4"', 'EA', 8.50, 0.22),
    
    # PVC DWV 45° Elbows
    ('PVC00412', 'PVC DWV Fittings', '1-1/2" PVC DWV 45° Elbow', '1-1/2"', 'EA', 1.95, 0.15),
    ('PVC00414', 'PVC DWV Fittings', '2" PVC DWV 45° Elbow', '2"', 'EA', 2.65, 0.17),
    ('PVC00416', 'PVC DWV Fittings', '3" PVC DWV 45° Elbow', '3"', 'EA', 4.85, 0.20),
    ('PVC00418', 'PVC DWV Fittings', '4" PVC DWV 45° Elbow', '4"', 'EA', 7.95, 0.22),
    
    # PVC DWV Sanitary Tees
    ('PVC00422', 'PVC DWV Fittings', '1-1/2" PVC DWV Sanitary Tee', '1-1/2"', 'EA', 3.25, 0.20),
    ('PVC00424', 'PVC DWV Fittings', '2" PVC DWV Sanitary Tee', '2"', 'EA', 4.50, 0.22),
    ('PVC00426', 'PVC DWV Fittings', '3" PVC DWV Sanitary Tee', '3"', 'EA', 8.75, 0.25),
    ('PVC00428', 'PVC DWV Fittings', '4" PVC DWV Sanitary Tee', '4"', 'EA', 14.50, 0.28),
    
    # PVC DWV Wyes
    ('PVC00432', 'PVC DWV Fittings', '1-1/2" PVC DWV Wye', '1-1/2"', 'EA', 3.50, 0.20),
    ('PVC00434', 'PVC DWV Fittings', '2" PVC DWV Wye', '2"', 'EA', 4.85, 0.22),
    ('PVC00436', 'PVC DWV Fittings', '3" PVC DWV Wye', '3"', 'EA', 9.25, 0.25),
    ('PVC00438', 'PVC DWV Fittings', '4" PVC DWV Wye', '4"', 'EA', 15.75, 0.28),
    
    # PVC DWV Couplings
    ('PVC00442', 'PVC DWV Fittings', '1-1/2" PVC DWV Coupling', '1-1/2"', 'EA', 1.25, 0.10),
    ('PVC00444', 'PVC DWV Fittings', '2" PVC DWV Coupling', '2"', 'EA', 1.65, 0.12),
    ('PVC00446', 'PVC DWV Fittings', '3" PVC DWV Coupling', '3"', 'EA', 2.95, 0.14),
    ('PVC00448', 'PVC DWV Fittings', '4" PVC DWV Coupling', '4"', 'EA', 4.25, 0.16),
    
    # PVC DWV P-Traps
    ('PVC00452', 'PVC DWV Fittings', '1-1/2" PVC DWV P-Trap', '1-1/2"', 'EA', 4.50, 0.25),
    ('PVC00454', 'PVC DWV Fittings', '2" PVC DWV P-Trap', '2"', 'EA', 6.25, 0.28),
    
    # PVC DWV Cleanouts
    ('PVC00464', 'PVC DWV Fittings', '2" PVC DWV Cleanout Adapter', '2"', 'EA', 3.85, 0.20),
    ('PVC00466', 'PVC DWV Fittings', '3" PVC DWV Cleanout Adapter', '3"', 'EA', 6.50, 0.22),
    ('PVC00468', 'PVC DWV Fittings', '4" PVC DWV Cleanout Adapter', '4"', 'EA', 9.75, 0.25),
]

def init_materials_tables():
    """Initialize materials database tables"""
    db = get_db()
    c = db.cursor()
    
    # Company Materials table
    c.execute('''CREATE TABLE IF NOT EXISTS company_materials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER NOT NULL,
        part_number TEXT NOT NULL,
        category TEXT NOT NULL,
        description TEXT NOT NULL,
        size TEXT,
        unit TEXT NOT NULL,
        list_price REAL NOT NULL,
        labor_units REAL NOT NULL,
        is_active BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
        UNIQUE(company_id, part_number)
    )''')
    
    # Material Takeoff Items table
    c.execute('''CREATE TABLE IF NOT EXISTS takeoff_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        drawing_id INTEGER NOT NULL,
        page_number INTEGER NOT NULL,
        material_id INTEGER NOT NULL,
        wbs_category_id INTEGER,
        quantity REAL NOT NULL,
        multiplier REAL DEFAULT 1.0,
        measurement_type TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (drawing_id) REFERENCES drawings(id) ON DELETE CASCADE,
        FOREIGN KEY (material_id) REFERENCES company_materials(id),
        FOREIGN KEY (wbs_category_id) REFERENCES wbs_categories(id)
    )''')
    
    # RFQs table
    c.execute('''CREATE TABLE IF NOT EXISTS rfqs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        rfq_number TEXT NOT NULL,
        supplier_name TEXT,
        supplier_email TEXT,
        supplier_phone TEXT,
        status TEXT DEFAULT 'draft',
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        sent_at TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
        UNIQUE(project_id, rfq_number)
    )''')
    
    # RFQ Items table
    c.execute('''CREATE TABLE IF NOT EXISTS rfq_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rfq_id INTEGER NOT NULL,
        material_id INTEGER NOT NULL,
        quantity REAL NOT NULL,
        unit TEXT NOT NULL,
        notes TEXT,
        FOREIGN KEY (rfq_id) REFERENCES rfqs(id) ON DELETE CASCADE,
        FOREIGN KEY (material_id) REFERENCES company_materials(id)
    )''')
    
    db.commit()
    print("✓ Materials tables initialized")

def load_default_materials_for_company(company_id):
    """Load default materials database for a new company"""
    db = get_db()
    c = db.cursor()
    
    # Check if company already has materials
    existing = c.execute(
        'SELECT COUNT(*) FROM company_materials WHERE company_id = ?',
        (company_id,)
    ).fetchone()[0]
    
    if existing > 0:
        print(f"Company {company_id} already has materials, skipping default load")
        return
    
    # Insert default materials
    for material in DEFAULT_MATERIALS:
        c.execute('''
            INSERT INTO company_materials 
            (company_id, part_number, category, description, size, unit, list_price, labor_units)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (company_id,) + material)
    
    db.commit()
    print(f"✓ Loaded {len(DEFAULT_MATERIALS)} default materials for company {company_id}")

# ============ CRUD Functions ============

def get_company_materials(company_id, category=None, active_only=True):
    """Get all materials for a company"""
    db = get_db()
    
    query = 'SELECT * FROM company_materials WHERE company_id = ?'
    params = [company_id]
    
    if active_only:
        query += ' AND is_active = 1'
    
    if category:
        query += ' AND category = ?'
        params.append(category)
    
    query += ' ORDER BY category, size, description'
    
    return db.execute(query, params).fetchall()

def get_material(material_id):
    """Get a specific material"""
    db = get_db()
    return db.execute(
        'SELECT * FROM company_materials WHERE id = ?',
        (material_id,)
    ).fetchone()

def create_material(company_id, part_number, category, description, size, unit, list_price, labor_units):
    """Create a new material (admin only)"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
        INSERT INTO company_materials 
        (company_id, part_number, category, description, size, unit, list_price, labor_units)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (company_id, part_number, category, description, size, unit, list_price, labor_units))
    
    db.commit()
    return cursor.lastrowid

def update_material(material_id, **kwargs):
    """Update a material (admin only)"""
    db = get_db()
    
    allowed_fields = ['part_number', 'category', 'description', 'size', 'unit', 'list_price', 'labor_units', 'is_active']
    
    for field, value in kwargs.items():
        if field in allowed_fields and value is not None:
            db.execute(
                f'UPDATE company_materials SET {field} = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                (value, material_id)
            )
    
    db.commit()

def delete_material(material_id):
    """Soft delete a material (admin only)"""
    db = get_db()
    db.execute(
        'UPDATE company_materials SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
        (material_id,)
    )
    db.commit()

# ============ Takeoff Functions ============

def create_takeoff_item(drawing_id, page_number, material_id, wbs_category_id, quantity, multiplier=1.0, measurement_type=None, notes=None):
    """Add a material to the takeoff"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
        INSERT INTO takeoff_items 
        (drawing_id, page_number, material_id, wbs_category_id, quantity, multiplier, measurement_type, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (drawing_id, page_number, material_id, wbs_category_id, quantity, multiplier, measurement_type, notes))
    
    db.commit()
    return cursor.lastrowid

def get_takeoff_items(drawing_id, page_number=None, wbs_category_id=None):
    """Get takeoff items for a drawing"""
    db = get_db()
    
    query = '''
        SELECT 
            ti.*,
            cm.part_number,
            cm.category,
            cm.description,
            cm.size,
            cm.unit,
            cm.list_price,
            cm.labor_units,
            wc.name as wbs_name
        FROM takeoff_items ti
        JOIN company_materials cm ON ti.material_id = cm.id
        LEFT JOIN wbs_categories wc ON ti.wbs_category_id = wc.id
        WHERE ti.drawing_id = ?
    '''
    params = [drawing_id]
    
    if page_number is not None:
        query += ' AND ti.page_number = ?'
        params.append(page_number)
    
    if wbs_category_id is not None:
        query += ' AND ti.wbs_category_id = ?'
        params.append(wbs_category_id)
    
    query += ' ORDER BY ti.page_number, wc.sort_order, cm.category, cm.description'
    
    return db.execute(query, params).fetchall()

def get_project_takeoff_summary(project_id):
    """Get takeoff summary for entire project grouped by WBS"""
    db = get_db()
    
    return db.execute('''
        SELECT 
            wc.id as wbs_category_id,
            wc.name as wbs_name,
            cm.id as material_id,
            cm.part_number,
            cm.description,
            cm.size,
            cm.unit,
            cm.list_price,
            cm.labor_units,
            SUM(ti.quantity * ti.multiplier) as total_quantity,
            SUM(ti.quantity * ti.multiplier * cm.list_price) as total_price,
            SUM(ti.quantity * cm.labor_units) as total_labor
        FROM takeoff_items ti
        JOIN drawings d ON ti.drawing_id = d.id
        JOIN company_materials cm ON ti.material_id = cm.id
        LEFT JOIN wbs_categories wc ON ti.wbs_category_id = wc.id
        WHERE d.project_id = ?
        GROUP BY wc.id, cm.id
        ORDER BY wc.sort_order, cm.category, cm.description
    ''', (project_id,)).fetchall()

def update_takeoff_item(item_id, quantity=None, multiplier=None, wbs_category_id=None, notes=None):
    """Update a takeoff item"""
    db = get_db()
    
    if quantity is not None:
        db.execute('UPDATE takeoff_items SET quantity = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', (quantity, item_id))
    
    if multiplier is not None:
        db.execute('UPDATE takeoff_items SET multiplier = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', (multiplier, item_id))
    
    if wbs_category_id is not None:
        db.execute('UPDATE takeoff_items SET wbs_category_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', (wbs_category_id, item_id))
    
    if notes is not None:
        db.execute('UPDATE takeoff_items SET notes = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', (notes, item_id))
    
    db.commit()

def delete_takeoff_item(item_id):
    """Delete a takeoff item"""
    db = get_db()
    db.execute('DELETE FROM takeoff_items WHERE id = ?', (item_id,))
    db.commit()

# ============ RFQ Functions ============

def create_rfq(project_id, rfq_number, supplier_name=None, supplier_email=None, supplier_phone=None, notes=None):
    """Create a new RFQ"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
        INSERT INTO rfqs 
        (project_id, rfq_number, supplier_name, supplier_email, supplier_phone, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (project_id, rfq_number, supplier_name, supplier_email, supplier_phone, notes))
    
    db.commit()
    return cursor.lastrowid

def add_rfq_item(rfq_id, material_id, quantity, unit, notes=None):
    """Add an item to an RFQ"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
        INSERT INTO rfq_items (rfq_id, material_id, quantity, unit, notes)
        VALUES (?, ?, ?, ?, ?)
    ''', (rfq_id, material_id, quantity, unit, notes))
    
    db.commit()
    return cursor.lastrowid

def get_project_rfqs(project_id):
    """Get all RFQs for a project"""
    db = get_db()
    return db.execute(
        'SELECT * FROM rfqs WHERE project_id = ? ORDER BY created_at DESC',
        (project_id,)
    ).fetchall()

def get_rfq_with_items(rfq_id):
    """Get RFQ with all items"""
    db = get_db()
    
    rfq = db.execute('SELECT * FROM rfqs WHERE id = ?', (rfq_id,)).fetchone()
    
    items = db.execute('''
        SELECT 
            ri.*,
            cm.part_number,
            cm.description,
            cm.size,
            cm.list_price,
            cm.labor_units
        FROM rfq_items ri
        JOIN company_materials cm ON ri.material_id = cm.id
        WHERE ri.rfq_id = ?
        ORDER BY cm.category, cm.description
    ''', (rfq_id,)).fetchall()
    
    return {
        'rfq': dict(rfq) if rfq else None,
        'items': [dict(item) for item in items]
    }

def update_rfq_status(rfq_id, status):
    """Update RFQ status"""
    db = get_db()
    db.execute('UPDATE rfqs SET status = ? WHERE id = ?', (status, rfq_id))
    
    if status == 'sent':
        db.execute('UPDATE rfqs SET sent_at = CURRENT_TIMESTAMP WHERE id = ?', (rfq_id,))
    
    db.commit()