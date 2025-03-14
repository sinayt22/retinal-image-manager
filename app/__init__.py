from flask import Flask
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
        from app.models import patient, image


    from app.controllers.web.patient_controller import patient_bp
    app.register_blueprint(patient_bp, url_prefix='/patients')
    
    setup_upload_destination(app)

    return app


def setup_upload_destination(app):
    import os
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)