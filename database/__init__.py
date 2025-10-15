"""
Database package initialization
"""
from .db import get_db, init_db, close_db
from .models import (
    create_company, get_companies, delete_company,
    create_user, get_users, get_user_by_email, delete_user,
    add_user_to_company, get_user_companies,
    create_project, get_projects_by_company, get_project, update_project, delete_project,
    create_drawing, get_drawings_by_project, get_drawing, update_drawing, delete_drawing,
    create_detected_item, get_detected_items, delete_detected_item,
    get_takeoff_summary
)

__all__ = [
    'get_db', 'init_db', 'close_db',
    'create_company', 'get_companies', 'delete_company',
    'create_user', 'get_users', 'get_user_by_email', 'delete_user',
    'add_user_to_company', 'get_user_companies',
    'create_project', 'get_projects_by_company', 'get_project', 'update_project', 'delete_project',
    'create_drawing', 'get_drawings_by_project', 'get_drawing', 'update_drawing', 'delete_drawing',
    'create_detected_item', 'get_detected_items', 'delete_detected_item',
    'get_takeoff_summary'
]