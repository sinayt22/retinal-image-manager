import os
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

            clean_upload_directory(app)

    setup_upload_destination(app)

    return app



def clean_upload_directory(app):
    """Remove all files and subdirectories from the upload folder."""
    try:
        import shutil
        if os.path.exists(app.config['UPLOAD_FOLDER']):
            for file in os.listdir(app.config['UPLOAD_FOLDER']):
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], file)
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            print("All uploaded files have been removed!")
    except Exception as e:
        print(f"Error cleaning upload directory: {e}")


def setup_upload_destination(app):
    """
    Set up the upload directory structure without symlinks.
    """
    # Create the main upload folder
    upload_folder = os.path.abspath(app.config['UPLOAD_FOLDER'])
    os.makedirs(upload_folder, exist_ok=True)
    
    # Create the static uploads folder for web access
    static_uploads = os.path.join(app.static_folder, 'uploads/images')
    os.makedirs(static_uploads, exist_ok=True)
    
    # Set permissions to ensure both Flask and Docker can write
    try:
        os.chmod(upload_folder, 0o777)
        os.chmod(static_uploads, 0o777)
    except Exception as e:
        print(f"Warning: Could not set permissions: {e}")
        
    print(f"Upload folder: {upload_folder}")
    print(f"Static images folder: {static_uploads}")