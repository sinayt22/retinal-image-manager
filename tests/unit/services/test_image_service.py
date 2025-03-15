import pytest
import os
from datetime import datetime, timezone
from app.models.image import Image, EyeSide, ImageQualityScore, AnatomyScore
from app.services.image_service import ImageService


@pytest.mark.usefixtures('app_context')
class TestImageService:
    @pytest.fixture
    def image_service(self):
        return ImageService()
    
    @pytest.fixture
    def db_session(self, monkeypatch):
        """
        Create a mock db session with methods that can be monitored
        """
        class MockSession:
            def __init__(self):
                self.added = []
                self.deleted = []
                self.committed = False
            
            def add(self, obj):
                self.added.append(obj)
            
            def delete(self, obj):
                self.deleted.append(obj)
            
            def commit(self):
                self.committed = True
                
            def remove(self):
                pass  # Required for teardown_appcontext
        
        mock_session = MockSession()
        
        # Patch the db.session in the app
        monkeypatch.setattr('app.services.image_service.db.session', mock_session)
        
        return mock_session
    
    @pytest.fixture
    def mock_image_file(self, monkeypatch, tmp_path):
        """
        Create a mock file for testing file uploads
        """
        class MockFile:
            def __init__(self):
                self.filename = "test_image.jpg"
                self.saved_path = None
            
            def save(self, path):
                self.saved_path = path
                # Create an empty file
                with open(path, 'w') as f:
                    f.write("test")
        
        # Create a test upload folder
        upload_folder = tmp_path / "uploads"
        upload_folder.mkdir()
        
        # Mock the current_app.config
        class MockConfig:
            def __getitem__(self, key):
                if key == 'UPLOAD_FOLDER':
                    return str(upload_folder)
                return None
        
        class MockApp:
            config = MockConfig()
        
        monkeypatch.setattr('app.services.image_service.current_app', MockApp())
        
        return MockFile()
    
    def test_get_patient_images(self, image_service, monkeypatch):
        # Mock data
        mock_images = [
            Image(id=1, patient_id=1, eye_side=EyeSide.LEFT, image_path="image1.jpg"),
            Image(id=2, patient_id=1, eye_side=EyeSide.RIGHT, image_path="image2.jpg"),
        ]
        
        # Mock the query
        class MockQuery:
            def filter_by(self, patient_id):
                return self
            
            def order_by(self, _):
                return self
            
            def all(self):
                return mock_images
        
        monkeypatch.setattr(Image, 'query', MockQuery())
        
        # Test
        images = image_service.get_patient_images(1)
        
        # Assertions
        assert len(images) == 2
        assert images[0].id == 1
        assert images[1].id == 2
    
    def test_get_image_by_id(self, image_service, monkeypatch):
        # Mock data
        mock_image = Image(
            id=1, 
            patient_id=1, 
            eye_side=EyeSide.LEFT, 
            quality_score=ImageQualityScore.HIGH, 
            image_path="image1.jpg"
        )
        
        # Mock the query
        class MockQuery:
            def get(self, id):
                if id == 1:
                    return mock_image
                return None
        
        monkeypatch.setattr(Image, 'query', MockQuery())
        
        # Test
        image = image_service.get_image_by_id(1)
        
        # Assertions
        assert image is not None
        assert image.id == 1
        assert image.patient_id == 1
        assert image.eye_side == EyeSide.LEFT
        assert image.quality_score == ImageQualityScore.HIGH
        
        # Test non-existent image
        image = image_service.get_image_by_id(999)
        assert image is None
    
    def test_create_image_without_file(self, image_service, db_session, monkeypatch):
        # Mock data
        image_data = {
            'patient_id': 1,
            'eye_side': EyeSide.LEFT,
            'quality_score': ImageQualityScore.HIGH,
            'anatomy_score': AnatomyScore.GOOD,
            'site': 'Main Clinic',
            'over_illuminated': False,
            'image_path': 'existing_image.jpg',
            'acquisition_date': datetime(2025, 3, 1, tzinfo=timezone.utc)
        }
        
        # Instead of mocking __init__, mock the entire Image class
        class MockImage:
            def __init__(self, **kwargs):
                self.id = 1
                for key, value in kwargs.items():
                    setattr(self, key, value)
        
        # Replace the Image class in the service
        monkeypatch.setattr('app.services.image_service.Image', MockImage)
        
        # Test
        image = image_service.create_image(image_data)
        
        # Assertions
        assert image is not None
        assert image.id == 1
        assert image.patient_id == 1
        assert image.eye_side == EyeSide.LEFT
        assert image.quality_score == ImageQualityScore.HIGH
        assert image.image_path == 'existing_image.jpg'
        
        # Check if session methods were called
        assert len(db_session.added) == 1
        assert db_session.committed is True
    
    def test_create_image_with_file(self, image_service, db_session, mock_image_file, monkeypatch):
        # Mock data
        image_data = {
            'patient_id': 1,
            'eye_side': EyeSide.LEFT,
            'quality_score': ImageQualityScore.HIGH,
            'anatomy_score': AnatomyScore.GOOD,
            'site': 'Main Clinic',
            'over_illuminated': False
        }
        
        # Mock datetime.now
        fixed_datetime = datetime(2025, 3, 1, 12, 0, 0, tzinfo=timezone.utc)
        monkeypatch.setattr('app.services.image_service.datetime', type('MockDatetime', (), {
            'now': lambda *args: fixed_datetime,
            'timezone': timezone
        }))
        
        # Instead of mocking __init__, mock the entire Image class
        class MockImage:
            def __init__(self, **kwargs):
                self.id = 1
                for key, value in kwargs.items():
                    setattr(self, key, value)
        
        # Replace the Image class in the service
        monkeypatch.setattr('app.services.image_service.Image', MockImage)
        
        # Mock secure_filename
        monkeypatch.setattr('app.services.image_service.secure_filename', lambda x: x)
        
        # Test
        image = image_service.create_image(image_data, mock_image_file)
        
        # Assertions
        assert image is not None
        assert image.id == 1
        assert image.patient_id == 1
        assert image.eye_side == EyeSide.LEFT
        assert image.quality_score == ImageQualityScore.HIGH
        
        # Check if file was saved
        assert mock_image_file.saved_path is not None
        assert "20250301120000_test_image.jpg" in mock_image_file.saved_path
        
        # Check if image path was set correctly
        assert image.image_path == "20250301120000_test_image.jpg"
        
        # Check if session methods were called
        assert len(db_session.added) == 1
        assert db_session.committed is True
    
    def test_update_image(self, image_service, db_session, monkeypatch):
        # Mock data
        mock_image = Image(
            id=1, 
            patient_id=1, 
            eye_side=EyeSide.LEFT, 
            quality_score=ImageQualityScore.ACCEPTABLE, 
            anatomy_score=AnatomyScore.ACCEPTABLE,
            site=None,
            over_illuminated=False,
            image_path="image1.jpg"
        )
        
        # Mock the get_image_by_id method
        monkeypatch.setattr(
            image_service, 
            'get_image_by_id', 
            lambda id: mock_image if id == 1 else None
        )
        
        # Update data
        update_data = {
            'quality_score': ImageQualityScore.HIGH,
            'anatomy_score': AnatomyScore.GOOD,
            'site': 'Updated Clinic',
            'over_illuminated': True
        }
        
        # Test
        updated_image = image_service.update_image(1, update_data)
        
        # Assertions
        assert updated_image is not None
        assert updated_image.quality_score == ImageQualityScore.HIGH
        assert updated_image.anatomy_score == AnatomyScore.GOOD
        assert updated_image.site == 'Updated Clinic'
        assert updated_image.over_illuminated is True
        assert db_session.committed is True
        
        # Test updating non-existent image
        with pytest.raises(ValueError, match="Image with ID 999 not found"):
            image_service.update_image(999, update_data)
    
    def test_delete_image_without_file(self, image_service, db_session, monkeypatch):
        # Mock data
        mock_image = Image(
            id=1, 
            patient_id=1, 
            eye_side=EyeSide.LEFT, 
            image_path=None  # No file to delete
        )
        
        # Mock the get_image_by_id method
        monkeypatch.setattr(
            image_service, 
            'get_image_by_id', 
            lambda id: mock_image if id == 1 else None
        )
        
        # Test
        result = image_service.delete_image(1)
        
        # Assertions
        assert result is True
        assert len(db_session.deleted) == 1
        assert db_session.committed is True
        
        # Test deleting non-existent image
        with pytest.raises(ValueError, match="Image with ID 999 not found"):
            image_service.delete_image(999)
    
    def test_delete_image_with_file(self, image_service, db_session, monkeypatch, tmp_path):
        # Create a test file
        upload_folder = tmp_path / "uploads"
        upload_folder.mkdir()
        test_file_path = upload_folder / "test_image.jpg"
        with open(test_file_path, 'w') as f:
            f.write("test")
        
        # Mock data
        mock_image = Image(
            id=1, 
            patient_id=1, 
            eye_side=EyeSide.LEFT, 
            image_path="test_image.jpg"
        )
        
        # Mock the get_image_by_id method
        monkeypatch.setattr(
            image_service, 
            'get_image_by_id', 
            lambda id: mock_image if id == 1 else None
        )
        
        # Mock the current_app.config
        class MockConfig:
            def __getitem__(self, key):
                if key == 'UPLOAD_FOLDER':
                    return str(upload_folder)
                return None
        
        class MockApp:
            config = MockConfig()
        
        monkeypatch.setattr('app.services.image_service.current_app', MockApp())
        
        # Test
        result = image_service.delete_image(1)
        
        # Assertions
        assert result is True
        assert len(db_session.deleted) == 1
        assert db_session.committed is True
        
        # Check if file was deleted
        assert not os.path.exists(test_file_path)