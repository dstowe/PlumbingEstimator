"""
Routes package
API endpoint blueprints
"""
from .auth import auth_bp
from .admin import admin_bp
from .projects import projects_bp
from .drawings import drawings_bp
from .wbs import wbs_bp
from .scales import scales_bp

__all__ = ['auth_bp', 'admin_bp', 'projects_bp', 'drawings_bp', 'wbs_bp', 'scales_bp']