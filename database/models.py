"""
Database models and query functions
"""
import os
from .db import get_db
from werkzeug.security import generate_password_hash

# Company Functions
def create_company(name, address=None, phone=None):
    """Create a new company"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        'INSERT INTO companies (name, address, phone) VALUES (?, ?, ?)',
        (name, address, phone)
    )
    db.commit()
    return cursor.lastrowid

def get_companies():
    """Get all companies"""
    db = get_db()
    return db.execute('SELECT * FROM companies ORDER BY name').fetchall()

def get_company(company_id):
    """Get a specific company"""
    db = get_db()
    return db.execute('SELECT * FROM companies WHERE id = ?', (company_id,)).fetchone()

def delete_company(company_id):
    """Delete a company"""
    db = get_db()
    db.execute('DELETE FROM companies WHERE id = ?', (company_id,))
    db.commit()

# User Functions
def create_user(email, password, first_name=None, last_name=None, is_admin=False):
    """Create a new user"""
    db = get_db()
    cursor = db.cursor()
    password_hash = generate_password_hash(password)
    cursor.execute(
        'INSERT INTO users (email, password_hash, first_name, last_name, is_admin) VALUES (?, ?, ?, ?, ?)',
        (email, password_hash, first_name, last_name, is_admin)
    )
    db.commit()
    return cursor.lastrowid

def get_users():
    """Get all users with their companies"""
    db = get_db()
    return db.execute('''
        SELECT u.*, GROUP_CONCAT(c.name, ', ') as companies
        FROM users u
        LEFT JOIN user_companies uc ON u.id = uc.user_id
        LEFT JOIN companies c ON uc.company_id = c.id
        GROUP BY u.id
        ORDER BY u.email
    ''').fetchall()

def get_user_by_email(email):
    """Get user by email"""
    db = get_db()
    return db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()

def get_user_by_id(user_id):
    """Get user by ID"""
    db = get_db()
    return db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()

def delete_user(user_id):
    """Delete a user"""
    db = get_db()
    db.execute('DELETE FROM users WHERE id = ?', (user_id,))
    db.commit()

# User-Company Relationship Functions
def add_user_to_company(user_id, company_id, role='user'):
    """Add user to a company"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        'INSERT INTO user_companies (user_id, company_id, role) VALUES (?, ?, ?)',
        (user_id, company_id, role)
    )
    db.commit()

def get_user_companies(user_id):
    """Get all companies for a user"""
    db = get_db()
    return db.execute('''
        SELECT c.*, uc.role 
        FROM companies c
        JOIN user_companies uc ON c.id = uc.company_id
        WHERE uc.user_id = ?
        ORDER BY c.name
    ''', (user_id,)).fetchall()

def check_user_company_access(user_id, company_id):
    """Check if user has access to a company"""
    db = get_db()
    result = db.execute(
        'SELECT 1 FROM user_companies WHERE user_id = ? AND company_id = ?',
        (user_id, company_id)
    ).fetchone()
    return result is not None

# Project Functions
def create_project(company_id, name, description=None):
    """Create a new project"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        'INSERT INTO projects (company_id, name, description) VALUES (?, ?, ?)',
        (company_id, name, description)
    )
    db.commit()
    return cursor.lastrowid

def get_projects_by_company(company_id):
    """Get all projects for a company"""
    db = get_db()
    return db.execute(
        'SELECT * FROM projects WHERE company_id = ? ORDER BY updated_at DESC',
        (company_id,)
    ).fetchall()

def get_project(project_id):
    """Get a specific project"""
    db = get_db()
    return db.execute('SELECT * FROM projects WHERE id = ?', (project_id,)).fetchone()

def delete_project(project_id):
    """Delete a project"""
    db = get_db()
    db.execute('DELETE FROM projects WHERE id = ?', (project_id,))
    db.commit()

# Drawing Functions
def create_drawing(project_id, name, file_path, page_count):
    """Create a new drawing"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        'INSERT INTO drawings (project_id, name, file_path, page_count) VALUES (?, ?, ?, ?)',
        (project_id, name, file_path, page_count)
    )
    db.commit()
    return cursor.lastrowid

def get_drawings_by_project(project_id):
    """Get all drawings for a project"""
    db = get_db()
    return db.execute(
        'SELECT * FROM drawings WHERE project_id = ? ORDER BY created_at',
        (project_id,)
    ).fetchall()

def get_drawing(drawing_id):
    """Get a specific drawing"""
    db = get_db()
    return db.execute('SELECT * FROM drawings WHERE id = ?', (drawing_id,)).fetchone()

def update_drawing_scale(drawing_id, scale):
    """Update drawing scale"""
    db = get_db()
    db.execute('UPDATE drawings SET scale = ? WHERE id = ?', (scale, drawing_id))
    db.commit()

def delete_drawing(drawing_id):
    """Delete a drawing and its physical file"""
    db = get_db()
    
    # Get the drawing to retrieve file path before deleting
    drawing = db.execute('SELECT file_path FROM drawings WHERE id = ?', (drawing_id,)).fetchone()
    
    if drawing:
        # Delete the physical file if it exists
        file_path = drawing['file_path']
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"✓ Deleted file: {file_path}")
            except Exception as e:
                print(f"⚠ Warning: Could not delete file {file_path}: {e}")
                # Continue with database deletion even if file deletion fails
    
    # Delete the database record (this will cascade delete detected_items)
    db.execute('DELETE FROM drawings WHERE id = ?', (drawing_id,))
    db.commit()

# Detected Items Functions
def create_detected_item(drawing_id, page_number, item_type, x, y, width, height, confidence, verified=False):
    """Create a detected item"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        '''INSERT INTO detected_items 
        (drawing_id, page_number, item_type, x, y, width, height, confidence, verified)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (drawing_id, page_number, item_type, x, y, width, height, confidence, verified)
    )
    db.commit()
    return cursor.lastrowid

def get_detected_items(drawing_id, page_number=None):
    """Get detected items for a drawing"""
    db = get_db()
    if page_number is not None:
        return db.execute(
            'SELECT * FROM detected_items WHERE drawing_id = ? AND page_number = ?',
            (drawing_id, page_number)
        ).fetchall()
    else:
        return db.execute(
            'SELECT * FROM detected_items WHERE drawing_id = ?',
            (drawing_id,)
        ).fetchall()

def update_detected_item(item_id, item_type=None, verified=None, notes=None):
    """Update a detected item"""
    db = get_db()
    db.execute(
        'UPDATE detected_items SET item_type = ?, verified = ?, notes = ? WHERE id = ?',
        (item_type, verified, notes, item_id)
    )
    db.commit()

def delete_detected_item(item_id):
    """Delete a detected item"""
    db = get_db()
    db.execute('DELETE FROM detected_items WHERE id = ?', (item_id,))
    db.commit()

def get_takeoff_summary(drawing_id):
    """Get takeoff summary (counts by type)"""
    db = get_db()
    return db.execute(
        'SELECT item_type, COUNT(*) as count FROM detected_items WHERE drawing_id = ? GROUP BY item_type',
        (drawing_id,)
    ).fetchall()

# Add these functions to database/models.py

def update_project(project_id, name=None, description=None):
    """Update project details"""
    db = get_db()
    if name is not None:
        db.execute(
            'UPDATE projects SET name = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
            (name, project_id)
        )
    if description is not None:
        db.execute(
            'UPDATE projects SET description = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
            (description, project_id)
        )
    db.commit()

def update_drawing(drawing_id, name):
    """Update drawing name"""
    db = get_db()
    db.execute('UPDATE drawings SET name = ? WHERE id = ?', (name, drawing_id))
    db.commit()

# WBS Category Functions (ADD THESE TO YOUR EXISTING FILE)

def create_default_wbs_categories(project_id):
    """Create default WBS categories for a new project"""
    from .db import get_db
    
    default_categories = [
        'UG Water',
        'UG Sanitary', 
        'UG Storm',
        'UG Gas',
        'AG Water',
        'AG Sanitary',
        'AG Storm',
        'AG Gas',
        'Fixtures',
        'Equipment'
    ]
    
    db = get_db()
    cursor = db.cursor()
    
    for i, name in enumerate(default_categories):
        cursor.execute(
            'INSERT INTO wbs_categories (project_id, name, sort_order) VALUES (?, ?, ?)',
            (project_id, name, i)
        )
    
    db.commit()

def get_wbs_categories(project_id):
    """Get all WBS categories for a project"""
    from .db import get_db
    db = get_db()
    return db.execute(
        'SELECT * FROM wbs_categories WHERE project_id = ? ORDER BY sort_order, name',
        (project_id,)
    ).fetchall()

def get_wbs_category(category_id):
    """Get a specific WBS category"""
    from .db import get_db
    db = get_db()
    return db.execute('SELECT * FROM wbs_categories WHERE id = ?', (category_id,)).fetchone()

def create_wbs_category(project_id, name, sort_order=None):
    """Create a new WBS category"""
    from .db import get_db
    db = get_db()
    cursor = db.cursor()
    
    if sort_order is None:
        # Get max sort_order and add 1
        max_order = db.execute(
            'SELECT MAX(sort_order) FROM wbs_categories WHERE project_id = ?',
            (project_id,)
        ).fetchone()[0]
        sort_order = (max_order or 0) + 1
    
    cursor.execute(
        'INSERT INTO wbs_categories (project_id, name, sort_order) VALUES (?, ?, ?)',
        (project_id, name, sort_order)
    )
    db.commit()
    return cursor.lastrowid

def update_wbs_category(category_id, name=None, sort_order=None):
    """Update a WBS category"""
    from .db import get_db
    db = get_db()
    
    if name is not None:
        db.execute('UPDATE wbs_categories SET name = ? WHERE id = ?', (name, category_id))
    
    if sort_order is not None:
        db.execute('UPDATE wbs_categories SET sort_order = ? WHERE id = ?', (sort_order, category_id))
    
    db.commit()

def delete_wbs_category(category_id):
    """Delete a WBS category"""
    from .db import get_db
    db = get_db()
    
    # Set wbs_category_id to NULL for all items in this category
    db.execute('UPDATE detected_items SET wbs_category_id = NULL WHERE wbs_category_id = ?', (category_id,))
    
    # Delete the category
    db.execute('DELETE FROM wbs_categories WHERE id = ?', (category_id,))
    db.commit()

def get_takeoff_by_wbs(project_id):
    """Get takeoff summary grouped by WBS category for entire project"""
    from .db import get_db
    db = get_db()
    
    return db.execute('''
        SELECT 
            wc.id as wbs_category_id,
            wc.name as wbs_category,
            di.item_type,
            COUNT(*) as count
        FROM detected_items di
        JOIN drawings d ON di.drawing_id = d.id
        LEFT JOIN wbs_categories wc ON di.wbs_category_id = wc.id
        WHERE d.project_id = ?
        GROUP BY wc.id, wc.name, di.item_type
        ORDER BY wc.sort_order, wc.name, di.item_type
    ''', (project_id,)).fetchall()

def get_takeoff_by_wbs_for_drawing(drawing_id):
    """Get takeoff summary grouped by WBS category for a specific drawing"""
    from .db import get_db
    db = get_db()
    
    return db.execute('''
        SELECT 
            wc.id as wbs_category_id,
            wc.name as wbs_category,
            di.item_type,
            COUNT(*) as count
        FROM detected_items di
        LEFT JOIN wbs_categories wc ON di.wbs_category_id = wc.id
        WHERE di.drawing_id = ?
        GROUP BY wc.id, wc.name, di.item_type
        ORDER BY wc.sort_order, wc.name, di.item_type
    ''', (drawing_id,)).fetchall()

def update_detected_item_wbs(item_id, wbs_category_id):
    """Update the WBS category for a detected item"""
    from .db import get_db
    db = get_db()
    db.execute(
        'UPDATE detected_items SET wbs_category_id = ? WHERE id = ?',
        (wbs_category_id, item_id)
    )
    db.commit()

def bulk_update_items_wbs(item_ids, wbs_category_id):
    """Update WBS category for multiple items at once"""
    from .db import get_db
    db = get_db()
    
    placeholders = ','.join('?' * len(item_ids))
    db.execute(
        f'UPDATE detected_items SET wbs_category_id = ? WHERE id IN ({placeholders})',
        [wbs_category_id] + item_ids
    )
    db.commit()

# WBS Category Functions (ADD THESE TO YOUR EXISTING FILE)

def create_default_wbs_categories(project_id):
    """Create default WBS categories for a new project"""
    from .db import get_db
    
    default_categories = [
        'UG Water',
        'UG Sanitary', 
        'UG Storm',
        'UG Gas',
        'AG Water',
        'AG Sanitary',
        'AG Storm',
        'AG Gas',
        'Fixtures'
    ]
    
    db = get_db()
    cursor = db.cursor()
    
    for i, name in enumerate(default_categories):
        cursor.execute(
            'INSERT INTO wbs_categories (project_id, parent_id, name, sort_order) VALUES (?, ?, ?, ?)',
            (project_id, None, name, i)
        )
    
    db.commit()

def get_wbs_categories(project_id):
    """Get all WBS categories for a project in hierarchical order"""
    from .db import get_db
    db = get_db()
    return db.execute(
        'SELECT * FROM wbs_categories WHERE project_id = ? ORDER BY parent_id NULLS FIRST, sort_order, name',
        (project_id,)
    ).fetchall()

def get_wbs_categories_tree(project_id):
    """Get WBS categories as a hierarchical tree structure"""
    from .db import get_db
    db = get_db()
    
    # Get all categories
    categories = db.execute(
        'SELECT * FROM wbs_categories WHERE project_id = ? ORDER BY sort_order, name',
        (project_id,)
    ).fetchall()
    
    # Build tree structure
    tree = []
    category_map = {}
    
    # First pass: create map of all categories
    for cat in categories:
        cat_dict = dict(cat)
        cat_dict['children'] = []
        category_map[cat['id']] = cat_dict
    
    # Second pass: build tree
    for cat in categories:
        cat_dict = category_map[cat['id']]
        if cat['parent_id'] is None:
            tree.append(cat_dict)
        else:
            parent = category_map.get(cat['parent_id'])
            if parent:
                parent['children'].append(cat_dict)
    
    return tree

def get_wbs_category(category_id):
    """Get a specific WBS category"""
    from .db import get_db
    db = get_db()
    return db.execute('SELECT * FROM wbs_categories WHERE id = ?', (category_id,)).fetchone()

def create_wbs_category(project_id, name, parent_id=None, sort_order=None):
    """Create a new WBS category"""
    from .db import get_db
    db = get_db()
    cursor = db.cursor()
    
    if sort_order is None:
        # Get max sort_order at the same level
        if parent_id is None:
            max_order = db.execute(
                'SELECT MAX(sort_order) FROM wbs_categories WHERE project_id = ? AND parent_id IS NULL',
                (project_id,)
            ).fetchone()[0]
        else:
            max_order = db.execute(
                'SELECT MAX(sort_order) FROM wbs_categories WHERE project_id = ? AND parent_id = ?',
                (project_id, parent_id)
            ).fetchone()[0]
        sort_order = (max_order or 0) + 1
    
    cursor.execute(
        'INSERT INTO wbs_categories (project_id, parent_id, name, sort_order) VALUES (?, ?, ?, ?)',
        (project_id, parent_id, name, sort_order)
    )
    db.commit()
    return cursor.lastrowid

def update_wbs_category(category_id, name=None, sort_order=None):
    """Update a WBS category"""
    from .db import get_db
    db = get_db()
    
    if name is not None:
        db.execute('UPDATE wbs_categories SET name = ? WHERE id = ?', (name, category_id))
    
    if sort_order is not None:
        db.execute('UPDATE wbs_categories SET sort_order = ? WHERE id = ?', (sort_order, category_id))
    
    db.commit()

def delete_wbs_category(category_id):
    """Delete a WBS category and all its children"""
    from .db import get_db
    db = get_db()
    
    # Get all child categories recursively
    def get_all_children(cat_id):
        children = db.execute(
            'SELECT id FROM wbs_categories WHERE parent_id = ?', (cat_id,)
        ).fetchall()
        child_ids = [cat_id]
        for child in children:
            child_ids.extend(get_all_children(child['id']))
        return child_ids
    
    all_ids = get_all_children(category_id)
    
    # Set wbs_category_id to NULL for all items in these categories
    placeholders = ','.join('?' * len(all_ids))
    db.execute(f'UPDATE detected_items SET wbs_category_id = NULL WHERE wbs_category_id IN ({placeholders})', all_ids)
    
    # Delete all categories (will cascade due to foreign key)
    db.execute('DELETE FROM wbs_categories WHERE id = ?', (category_id,))
    db.commit()

def get_wbs_path(category_id):
    """Get the full path of a category (e.g., 'UG Water > Service Lines')"""
    from .db import get_db
    db = get_db()
    
    path = []
    current_id = category_id
    
    while current_id is not None:
        cat = db.execute('SELECT id, name, parent_id FROM wbs_categories WHERE id = ?', (current_id,)).fetchone()
        if cat:
            path.insert(0, cat['name'])
            current_id = cat['parent_id']
        else:
            break
    
    return ' > '.join(path)

def get_takeoff_by_wbs(project_id):
    """Get takeoff summary grouped by WBS category for entire project"""
    from .db import get_db
    db = get_db()
    
    return db.execute('''
        SELECT 
            wc.id as wbs_category_id,
            wc.parent_id,
            wc.name as wbs_category,
            di.item_type,
            COUNT(*) as count
        FROM detected_items di
        JOIN drawings d ON di.drawing_id = d.id
        LEFT JOIN wbs_categories wc ON di.wbs_category_id = wc.id
        WHERE d.project_id = ?
        GROUP BY wc.id, wc.parent_id, wc.name, di.item_type
        ORDER BY wc.sort_order, wc.name, di.item_type
    ''', (project_id,)).fetchall()

def get_takeoff_by_wbs_for_drawing(drawing_id):
    """Get takeoff summary grouped by WBS category for a specific drawing"""
    from .db import get_db
    db = get_db()
    
    return db.execute('''
        SELECT 
            wc.id as wbs_category_id,
            wc.parent_id,
            wc.name as wbs_category,
            di.item_type,
            COUNT(*) as count
        FROM detected_items di
        LEFT JOIN wbs_categories wc ON di.wbs_category_id = wc.id
        WHERE di.drawing_id = ?
        GROUP BY wc.id, wc.parent_id, wc.name, di.item_type
        ORDER BY wc.sort_order, wc.name, di.item_type
    ''', (drawing_id,)).fetchall()

def update_detected_item_wbs(item_id, wbs_category_id):
    """Update the WBS category for a detected item"""
    from .db import get_db
    db = get_db()
    db.execute(
        'UPDATE detected_items SET wbs_category_id = ? WHERE id = ?',
        (wbs_category_id, item_id)
    )
    db.commit()

def bulk_update_items_wbs(item_ids, wbs_category_id):
    """Update WBS category for multiple items at once"""
    from .db import get_db
    db = get_db()
    
    placeholders = ','.join('?' * len(item_ids))
    db.execute(
        f'UPDATE detected_items SET wbs_category_id = ? WHERE id IN ({placeholders})',
        [wbs_category_id] + item_ids
    )
    db.commit()
"""
Database models and query functions
(Add these functions to your existing database/models.py file)
"""

# WBS Category Functions (ADD THESE TO YOUR EXISTING FILE)

def create_default_wbs_categories(project_id):
    """Create default WBS categories for a new project"""
    from .db import get_db
    
    default_categories = [
        'UG Water',
        'UG Sanitary', 
        'UG Storm',
        'UG Gas',
        'AG Water',
        'AG Sanitary',
        'AG Storm',
        'AG Gas',
        'Fixtures',
        'Equipment'
    ]
    
    db = get_db()
    cursor = db.cursor()
    
    for i, name in enumerate(default_categories):
        cursor.execute(
            'INSERT INTO wbs_categories (project_id, name, sort_order) VALUES (?, ?, ?)',
            (project_id, name, i)
        )
    
    db.commit()

def get_wbs_categories(project_id):
    """Get all WBS categories for a project"""
    from .db import get_db
    db = get_db()
    return db.execute(
        'SELECT * FROM wbs_categories WHERE project_id = ? ORDER BY sort_order, name',
        (project_id,)
    ).fetchall()

def get_wbs_category(category_id):
    """Get a specific WBS category"""
    from .db import get_db
    db = get_db()
    return db.execute('SELECT * FROM wbs_categories WHERE id = ?', (category_id,)).fetchone()

def create_wbs_category(project_id, name, sort_order=None):
    """Create a new WBS category"""
    from .db import get_db
    db = get_db()
    cursor = db.cursor()
    
    if sort_order is None:
        # Get max sort_order and add 1
        max_order = db.execute(
            'SELECT MAX(sort_order) FROM wbs_categories WHERE project_id = ?',
            (project_id,)
        ).fetchone()[0]
        sort_order = (max_order or 0) + 1
    
    cursor.execute(
        'INSERT INTO wbs_categories (project_id, name, sort_order) VALUES (?, ?, ?)',
        (project_id, name, sort_order)
    )
    db.commit()
    return cursor.lastrowid

def update_wbs_category(category_id, name=None, sort_order=None):
    """Update a WBS category"""
    from .db import get_db
    db = get_db()
    
    if name is not None:
        db.execute('UPDATE wbs_categories SET name = ? WHERE id = ?', (name, category_id))
    
    if sort_order is not None:
        db.execute('UPDATE wbs_categories SET sort_order = ? WHERE id = ?', (sort_order, category_id))
    
    db.commit()

def delete_wbs_category(category_id):
    """Delete a WBS category"""
    from .db import get_db
    db = get_db()
    
    # Set wbs_category_id to NULL for all items in this category
    db.execute('UPDATE detected_items SET wbs_category_id = NULL WHERE wbs_category_id = ?', (category_id,))
    
    # Delete the category
    db.execute('DELETE FROM wbs_categories WHERE id = ?', (category_id,))
    db.commit()

def get_takeoff_by_wbs(project_id):
    """Get takeoff summary grouped by WBS category for entire project"""
    from .db import get_db
    db = get_db()
    
    return db.execute('''
        SELECT 
            wc.id as wbs_category_id,
            wc.name as wbs_category,
            di.item_type,
            COUNT(*) as count
        FROM detected_items di
        JOIN drawings d ON di.drawing_id = d.id
        LEFT JOIN wbs_categories wc ON di.wbs_category_id = wc.id
        WHERE d.project_id = ?
        GROUP BY wc.id, wc.name, di.item_type
        ORDER BY wc.sort_order, wc.name, di.item_type
    ''', (project_id,)).fetchall()

def get_takeoff_by_wbs_for_drawing(drawing_id):
    """Get takeoff summary grouped by WBS category for a specific drawing"""
    from .db import get_db
    db = get_db()
    
    return db.execute('''
        SELECT 
            wc.id as wbs_category_id,
            wc.name as wbs_category,
            di.item_type,
            COUNT(*) as count
        FROM detected_items di
        LEFT JOIN wbs_categories wc ON di.wbs_category_id = wc.id
        WHERE di.drawing_id = ?
        GROUP BY wc.id, wc.name, di.item_type
        ORDER BY wc.sort_order, wc.name, di.item_type
    ''', (drawing_id,)).fetchall()

def update_detected_item_wbs(item_id, wbs_category_id):
    """Update the WBS category for a detected item"""
    from .db import get_db
    db = get_db()
    db.execute(
        'UPDATE detected_items SET wbs_category_id = ? WHERE id = ?',
        (wbs_category_id, item_id)
    )
    db.commit()

def bulk_update_items_wbs(item_ids, wbs_category_id):
    """Update WBS category for multiple items at once"""
    from .db import get_db
    db = get_db()
    
    placeholders = ','.join('?' * len(item_ids))
    db.execute(
        f'UPDATE detected_items SET wbs_category_id = ? WHERE id IN ({placeholders})',
        [wbs_category_id] + item_ids
    )
    db.commit()