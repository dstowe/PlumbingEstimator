# app.py - UPDATED VERSION
"""
Plumbing Estimator - Complete Application
Multi-tenant construction estimation system with Materials Database
"""
from flask import Flask, render_template, session, redirect, request
from flask_cors import CORS

from config import Config
from database.db import init_db, close_db
from database.materials_db import init_materials_tables

# Import route blueprints
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.projects import projects_bp
from routes.drawings import drawings_bp
from routes.wbs import wbs_bp
from routes.scales import scales_bp
from routes.materials import materials_bp

def create_app():
    """Application factory"""
    app = Flask(__name__, template_folder='templates')
    
    # Load configuration
    app.config.from_object(Config)
    Config.init_app(app)
    
    # Enable CORS
    CORS(app)
    
    # Initialize database
    with app.app_context():
        init_db()
        # Initialize materials tables (safe to run multiple times)
        from database.db import get_db
        try:
            init_materials_tables()
        except Exception as e:
            print(f"Materials tables already exist: {e}")
    
    # Register cleanup
    app.teardown_appcontext(close_db)
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(drawings_bp)
    app.register_blueprint(wbs_bp)
    app.register_blueprint(scales_bp)
    app.register_blueprint(materials_bp)  # NEW: Materials routes
    
    # Main routes
    @app.route('/')
    def index():
        """Main application entry point"""
        if 'user_id' not in session:
            return render_template('login.html')
        
        if 'company_id' not in session:
            return render_template('company_select.html')
        
        return render_template('main.html')
    
    @app.route('/admin')
    def admin_panel():
        """Admin panel"""
        if 'user_id' not in session:
            return redirect('/')
        
        return render_template('admin.html')
    
    @app.route('/materials')
    def materials_manager():
        """Materials database manager (admin only)"""
        if 'user_id' not in session:
            return redirect('/')
        
        # Check if user is admin (will be validated by route decorators)
        return render_template('materials.html')
    
    
    @app.route('/takeoff')
    def takeoff_interface():
        """Takeoff measurement interface"""
        if 'user_id' not in session:
            return redirect('/')
        
        if 'company_id' not in session:
            return redirect('/')
        
        # Get drawing_id and project_id from query parameters
        drawing_id = request.args.get('drawing_id', type=int)
        project_id = request.args.get('project_id', type=int)
        page_number = request.args.get('page', default=0, type=int)
        
        # If no drawing specified, show selection page
        if not drawing_id:
            return render_template('select_drawing.html')
        
        # Pass parameters to template
        return render_template('takeoff.html', 
                            drawing_id=drawing_id, 
                            project_id=project_id,
                            page_number=page_number)    
    return app

if __name__ == '__main__':
    app = create_app()
    
    print("\n" + "=" * 70)
    print(" " * 15 + "PLUMBING ESTIMATOR - COMPLETE SYSTEM")
    print("=" * 70)
    print(f"\n🚀 Server starting at http://localhost:{Config.PORT}")
    print("\n" + "-" * 70)
    print("DEFAULT CREDENTIALS:")
    print("-" * 70)
    print("  Email:    admin@example.com")
    print("  Password: admin123")
    print("-" * 70)
    print("\nFEATURES:")
    print("  ✓ Multi-tenant company management")
    print("  ✓ Project & drawing management")
    print("  ✓ WBS (Work Breakdown Structure)")
    print("  ✓ Materials database (admin-managed)")
    print("  ✓ On-screen measurement tools")
    print("  ✓ Interactive takeoff system")
    print("  ✓ RFQ generation")
    print("-" * 70)
    print("\nACCESS POINTS:")
    print(f"  Main App:     http://localhost:{Config.PORT}/")
    print(f"  Admin Panel:  http://localhost:{Config.PORT}/admin")
    print(f"  Materials DB: http://localhost:{Config.PORT}/materials")
    print(f"  Takeoff UI:   http://localhost:{Config.PORT}/takeoff")
    print("-" * 70)
    print("\n⚠️  Press Ctrl+C to stop the server\n")
    print("=" * 70 + "\n")
    
    app.run(
        debug=Config.DEBUG,
        host=Config.HOST,
        port=Config.PORT
    )