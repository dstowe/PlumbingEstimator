# database/db.py - UPDATED VERSION
"""
Database connection and initialization with Materials Database
"""
import sqlite3
from flask import g
from werkzeug.security import generate_password_hash
from config import Config

def get_db():
    """Get database connection"""
    if 'db' not in g:
        g.db = sqlite3.connect(Config.DATABASE_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    """Close database connection"""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """Initialize database with complete schema including materials"""
    conn = sqlite3.connect(Config.DATABASE_PATH)
    c = conn.cursor()
    
    print("=" * 60)
    print("Initializing Database Schema...")
    print("=" * 60)
    
    # ============ Core Tables ============
    
    # Companies table
    c.execute('''CREATE TABLE IF NOT EXISTS companies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        address TEXT,
        phone TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    print("✓ Companies table")
    
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
    print("✓ Users table")
    
    # User-Company relationship
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
    print("✓ User-Companies relationship table")
    
    # Projects table
    c.execute('''CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
    )''')
    print("✓ Projects table")
    
    # WBS Categories table
    c.execute('''CREATE TABLE IF NOT EXISTS wbs_categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        parent_id INTEGER,
        name TEXT NOT NULL,
        sort_order INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
        FOREIGN KEY (parent_id) REFERENCES wbs_categories(id) ON DELETE CASCADE
    )''')
    print("✓ WBS Categories table")
    
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
    print("✓ Drawings table")
    
    # Custom Scales table
    c.execute('''CREATE TABLE IF NOT EXISTS custom_scales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        pixels_per_unit REAL NOT NULL,
        unit TEXT DEFAULT 'feet',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
    )''')
    print("✓ Custom Scales table")
    
    # Page Scales table
    c.execute('''CREATE TABLE IF NOT EXISTS page_scales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        drawing_id INTEGER NOT NULL,
        page_number INTEGER NOT NULL,
        scale_id TEXT,
        scale_name TEXT,
        pixels_per_unit REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (drawing_id) REFERENCES drawings(id) ON DELETE CASCADE,
        UNIQUE(drawing_id, page_number)
    )''')
    print("✓ Page Scales table")
    
    # Scale Zones table
    c.execute('''CREATE TABLE IF NOT EXISTS scale_zones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        drawing_id INTEGER NOT NULL,
        page_number INTEGER NOT NULL,
        name TEXT NOT NULL,
        x REAL NOT NULL,
        y REAL NOT NULL,
        width REAL NOT NULL,
        height REAL NOT NULL,
        scale_id TEXT,
        scale_name TEXT,
        pixels_per_unit REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (drawing_id) REFERENCES drawings(id) ON DELETE CASCADE
    )''')
    print("✓ Scale Zones table")
    
    # Detected items table (legacy - for auto-detection)
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
        wbs_category_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (drawing_id) REFERENCES drawings(id) ON DELETE CASCADE,
        FOREIGN KEY (wbs_category_id) REFERENCES wbs_categories(id)
    )''')
    print("✓ Detected Items table")
    
    # ============ Materials Database Tables ============
    
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
    print("✓ Company Materials table")
    
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
    print("✓ Takeoff Items table")
    
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
    print("✓ RFQs table")
    
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
    print("✓ RFQ Items table")
    
    # ============ Create Default Admin User ============
    
    admin_exists = c.execute('SELECT COUNT(*) FROM users WHERE is_admin = 1').fetchone()[0]
    if admin_exists == 0:
        admin_hash = generate_password_hash('admin123')
        c.execute(
            'INSERT INTO users (email, password_hash, first_name, last_name, is_admin) VALUES (?, ?, ?, ?, ?)',
            ('admin@example.com', admin_hash, 'Admin', 'User', 1)
        )
        print("✓ Default admin user created")
        print("  Email: admin@example.com")
        print("  Password: admin123")
    
    conn.commit()
    conn.close()
    
    print("=" * 60)
    print("Database initialization complete!")
    print("=" * 60)

def load_default_materials_for_company(company_id):
    """Load default materials database when a new company is created"""
    from database.materials_db import DEFAULT_MATERIALS
    
    conn = sqlite3.connect(Config.DATABASE_PATH)
    c = conn.cursor()
    
    # Check if company already has materials
    existing = c.execute(
        'SELECT COUNT(*) FROM company_materials WHERE company_id = ?',
        (company_id,)
    ).fetchone()[0]
    
    if existing > 0:
        print(f"Company {company_id} already has materials")
        conn.close()
        return
    
    # Insert default materials
    for material in DEFAULT_MATERIALS:
        c.execute('''
            INSERT INTO company_materials 
            (company_id, part_number, category, description, size, unit, list_price, labor_units)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (company_id,) + material)
    
    conn.commit()
    conn.close()
    
    print(f"✓ Loaded {len(DEFAULT_MATERIALS)} default materials for company {company_id}")