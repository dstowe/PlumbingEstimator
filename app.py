"""
Plumbing Estimator - Main Application
Multi-tenant construction estimation system
"""
from flask import Flask, render_template, session, redirect
from flask_cors import CORS

from config import Config
from database import init_db, close_db

# Import route blueprints
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.projects import projects_bp
from routes.drawings import drawings_bp
from routes.wbs import wbs_bp
from routes.scales import scales_bp

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
    
    # Register cleanup
    app.teardown_appcontext(close_db)
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(drawings_bp)
    app.register_blueprint(wbs_bp)
    app.register_blueprint(scales_bp)
    
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
        
        # Check if user is admin (will be validated by route decorators)
        return render_template('admin.html')
    
    return app

if __name__ == '__main__':
    app = create_app()
    
    print("=" * 60)
    print("Plumbing Estimator - Multi-Tenant System")
    print("=" * 60)
    print(f"\n🚀 Server starting at http://localhost:{Config.PORT}")
    print("\n👤 Default Admin Login:")
    print("   Email: admin@example.com")
    print("   Password: admin123")
    print("\n⚠️  Press Ctrl+C to stop the server")
    print("=" * 60)
    
    app.run(
        debug=Config.DEBUG,
        host=Config.HOST,
        port=Config.PORT
    )