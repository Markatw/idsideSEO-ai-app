import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, jsonify, request, make_response
from flask_cors import CORS
from src.models.user import db
from src.routes.user import user_bp
from src.routes.auth import auth_bp
from src.routes.content import content_bp
from src.routes.analytics import analytics_bp
from src.routes.generate import generate_bp
from src.auth_middleware import check_frontend_auth

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'), static_url_path='')
CORS(app, origins="*", supports_credentials=False)

# Production-ready configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'asdf#FGSgvasgf$5$WGT')

# Register all blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(user_bp, url_prefix='/api/user')
app.register_blueprint(content_bp, url_prefix='/api/content')
app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
app.register_blueprint(generate_bp, url_prefix='/api/generate')

# Health check endpoint
@app.route("/api/health")
def health_check():
    return jsonify({"status": "healthy", "message": "IdsideSEO API is running"})

# Production database configuration
database_url = os.environ.get('DATABASE_URL')
if database_url:
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # Fallback to local database for development
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'idsideseo.db')}"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def init_database():
    """Initialize database tables - called only when needed"""
    with app.app_context():
        # Get the database URL from the app config
        db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
        
        # Create database directory if needed
        if db_uri.startswith('sqlite:///'):
            db_path = db_uri.replace('sqlite:///', '')
            db_dir = os.path.dirname(db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
        
        db.create_all()

# Initialize database only if running directly (not with Gunicorn workers)
if __name__ == '__main__':
    init_database()

@app.route('/app', defaults={'path': ''})
@app.route('/app/<path:path>')
def serve_app(path):
    """Serve the main application (protected route)"""
    # Check authentication
    is_authenticated, user_data = check_frontend_auth()
    if not is_authenticated:
        return make_response("Unauthorized", 401)
    
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404

    # Handle static files
    file_path = os.path.join(static_folder_path, path)
    if path != "" and os.path.exists(file_path):
        return send_from_directory(static_folder_path, path)
    
    # For all other routes, serve index.html (SPA routing)
    index_path = os.path.join(static_folder_path, 'index.html')
    if os.path.exists(index_path):
        return send_from_directory(static_folder_path, 'index.html')
    else:
        return "index.html not found", 404

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    """Main route handler with authentication check"""
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404

    # Handle static assets (CSS, JS, images, etc.)
    if path and any(path.endswith(ext) for ext in ['.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.woff', '.woff2', '.ttf', '.eot']):
        file_path = os.path.join(static_folder_path, path)
        if os.path.exists(file_path):
            return send_from_directory(static_folder_path, path)
        return "File not found", 404
    
    # Check authentication for main application routes
    is_authenticated, user_data = check_frontend_auth()
    
    # If authenticated, serve the main application
    if is_authenticated:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404
    
    # If not authenticated, serve login page
    login_path = os.path.join(static_folder_path, 'login.html')
    if os.path.exists(login_path):
        return send_from_directory(static_folder_path, 'login.html')
    else:
        return "Login page not found", 404

# For Gunicorn compatibility
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
