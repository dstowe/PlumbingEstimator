"""
Database connection and initialization
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
    """Initialize database with schema"""
    conn = sqlite3.connect(Config.DATABASE_PATH)
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
        print("✓ Default admin user created: admin@example.com / admin123")
    
    conn.commit()
    conn.close()
    print("✓ Database initialized successfully")