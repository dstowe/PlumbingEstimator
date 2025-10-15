"""
Database package initialization
"""
from .db import get_db, init_db, close_db
from .models import (
    create_company, get_companies, delete_company, get_company,
    create_user, get_users, get_user_by_email, get_user_by_id, delete_user,
    add_user_to_company, get_user_companies, check_user_company_access,
    create_project, get_projects_by_company, get_project, update_project, delete_project,
    create_drawing, get_drawings_by_project, get_drawing, update_drawing, delete_drawing, update_drawing_scale,
    create_detected_item, get_detected_items, update_detected_item, delete_detected_item,
    get_takeoff_summary,
    create_default_wbs_categories, get_wbs_categories, get_wbs_category, get_wbs_categories_tree,
    create_wbs_category, update_wbs_category, delete_wbs_category, get_wbs_path,
    get_takeoff_by_wbs, get_takeoff_by_wbs_for_drawing,
    update_detected_item_wbs, bulk_update_items_wbs,
    check_wbs_category_has_items, check_wbs_category_has_children
)

__all__ = [
    'get_db', 'init_db', 'close_db',
    'create_company', 'get_companies', 'delete_company', 'get_company',
    'create_user', 'get_users', 'get_user_by_email', 'get_user_by_id', 'delete_user',
    'add_user_to_company', 'get_user_companies', 'check_user_company_access',
    'create_project', 'get_projects_by_company', 'get_project', 'update_project', 'delete_project',
    'create_drawing', 'get_drawings_by_project', 'get_drawing', 'update_drawing', 'delete_drawing', 'update_drawing_scale',
    'create_detected_item', 'get_detected_items', 'update_detected_item', 'delete_detected_item',
    'get_takeoff_summary',
    'create_default_wbs_categories', 'get_wbs_categories', 'get_wbs_category', 'get_wbs_categories_tree',
    'create_wbs_category', 'update_wbs_category', 'delete_wbs_category', 'get_wbs_path',
    'get_takeoff_by_wbs', 'get_takeoff_by_wbs_for_drawing',
    'update_detected_item_wbs', 'bulk_update_items_wbs',
    'check_wbs_category_has_items', 'check_wbs_category_has_children'
]