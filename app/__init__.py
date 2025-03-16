from flask import Flask, redirect, url_for
from app.config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    
    with app.app_context():
        from app.models import patient, image, site


    from app.controllers.web.patient_controller import patient_bp
    app.register_blueprint(patient_bp, url_prefix='/patients')

    from app.controllers.web.image_controller import image_bp
    app.register_blueprint(image_bp, url_prefix='/images')
    
    from app.controllers.web.site_controller import site_bp
    app.register_blueprint(site_bp, url_prefix='/sites')

    from app.controllers.web.dashboard_controller import dashboard_bp
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')

    @app.route('/')
    def index():
        return redirect(url_for('patients.index'))


    @app.cli.command("reset-db")
    def reset_db():
        """Reset all data in the database while preserving the schema."""
        with app.app_context():
            db.drop_all()
            db.create_all()
            print("Database has been reset!")


    setup_upload_destination(app)

    return app



def setup_upload_destination(app):
    import os
    # Create the main upload folder
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Create a static symlink to the uploads folder for web access
    static_uploads = os.path.join(app.static_folder, 'uploads')
    os.makedirs(static_uploads, exist_ok=True)
    
    # Create a specific folder for images inside static/uploads
    static_images = os.path.join(static_uploads, 'images')
    # Create a symlink from the app's UPLOAD_FOLDER to static/uploads/images if it doesn't exist
    upload_folder = os.path.abspath(app.config['UPLOAD_FOLDER'])

    if os.path.exists(static_images):
        # If it exists but is not a symlink, remove it to replace with symlink
        if not os.path.islink(static_images):
            import shutil
            shutil.rmtree(static_images)

    if not os.path.exists(static_images):
        try:
            # For Unix/Linux systems
            if os.name == 'posix':
                if not os.path.islink(static_images):
                    os.symlink(upload_folder, static_images)
            elif os.name == 'nt':
                import ctypes
                if not os.path.islink(static_images):
                    kdll = ctypes.windll.LoadLibrary("kernel32.dll")
                    kdll.CreateSymbolicLinkA(static_images.encode(), upload_folder.encode(), 1)
        except (OSError, AttributeError, PermissionError):
            # If symlink creation fails, just ensure the directory exists
            os.makedirs(static_images, exist_ok=True)