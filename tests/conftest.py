import pytest
import os
from app import create_app, db
from app.config import Config
from datetime import datetime, timezone, date
from app.models.patient import Patient, Sex
from app.models.image import Image, EyeSide, ImageQualityScore, AnatomyScore


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    UPLOAD_FOLDER = 'tests/uploads'
    SECRET_KEY = '0b2920f184a7a210c914bff56e52fcb1'


@pytest.fixture
def app():
    """Create and configure a Flask app for testing."""
    app = create_app(TestConfig)
    
    # Create upload folder if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Create test database and tables
    with app.app_context():
        db.create_all()
        
        # Add sample data
        sample_patients = [
            Patient(birth_date=date(1990, 1, 15), sex=Sex.MALE),
            Patient(birth_date=date(1975, 5, 20), sex=Sex.FEMALE),
            Patient(birth_date=date(1995, 10, 5), sex=Sex.OTHER)
        ]
        db.session.add_all(sample_patients)
        db.session.commit()
        
        # Add sample images
        sample_images = [
            Image(
                patient_id=1,
                eye_side=EyeSide.LEFT,
                quality_score=ImageQualityScore.HIGH,
                anatomy_score=AnatomyScore.GOOD,
                site_id=1,
                over_illuminated=False,
                image_path="sample1.jpg",
                acquisition_date=datetime.now(timezone.utc)
            ),
            Image(
                patient_id=1,
                eye_side=EyeSide.RIGHT,
                quality_score=ImageQualityScore.ACCEPTABLE,
                anatomy_score=AnatomyScore.ACCEPTABLE,
                site_id=1,
                over_illuminated=True,
                image_path="sample2.jpg",
                acquisition_date=datetime.now(timezone.utc)
            )
        ]
        db.session.add_all(sample_images)
        db.session.commit()
        
        yield app
        
        # Clean up
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """A test CLI runner for the app."""
    return app.test_cli_runner()

@pytest.fixture
def app_context(app):
    with app.app_context():
        yield