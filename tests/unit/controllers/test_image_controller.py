import pytest
from datetime import date, datetime, timezone
from flask import url_for
from app.models.image import Image, EyeSide, ImageQualityScore, AnatomyScore
from app.models.patient import Patient, Sex


class TestImageController:
    @pytest.fixture
    def mock_services(self, monkeypatch):
        """
        Mock both PatientService and ImageService to avoid database interactions
        """
        # Create sample patient
        sample_patient = Patient(
            id=1,
            birth_date=date(1990, 1, 15),
            sex=Sex.MALE
        )
        
        # Create sample images
        sample_images = [
            Image(
                id=1,
                patient_id=1,
                eye_side=EyeSide.LEFT,
                quality_score=ImageQualityScore.HIGH,
                anatomy_score=AnatomyScore.GOOD,
                site_id=1,
                over_illuminated=False,
                image_path="sample1.jpg",
                acquisition_date=datetime(2025, 3, 1, tzinfo=timezone.utc)
            ),
            Image(
                id=2,
                patient_id=1,
                eye_side=EyeSide.RIGHT,
                quality_score=ImageQualityScore.ACCEPTABLE,
                anatomy_score=AnatomyScore.ACCEPTABLE,
                site_id=2,
                over_illuminated=True,
                image_path="sample2.jpg",
                acquisition_date=datetime(2025, 3, 2, tzinfo=timezone.utc)
            )
        ]
        
        class MockImageService:
            def get_patient_images(self, patient_id):
                if patient_id == 1:
                    return sample_images
                return []
                
            def get_image_by_id(self, image_id):
                if image_id == 1:
                    return sample_images[0]
                elif image_id == 2:
                    return sample_images[1]
                return None
                
            def create_image(self, image_data, image_file=None):
                # Return a mocked image with id=3
                mock_image = Image(
                    id=3,
                    patient_id=image_data.get('patient_id'),
                    eye_side=image_data.get('eye_side'),
                    quality_score=image_data.get('quality_score'),
                    anatomy_score=image_data.get('anatomy_score'),
                    site_id=image_data.get('site_id'),
                    over_illuminated=image_data.get('over_illuminated', False),
                    image_path='new_image.jpg' if image_file else image_data.get('image_path'),
                    acquisition_date=image_data.get('acquisition_date')
                )
                return mock_image
                
            def update_image(self, image_id, image_data):
                if image_id not in [1, 2]:
                    raise ValueError(f"Image with ID {image_id} not found")
                
                # Create an updated image with the new data
                image = next((img for img in sample_images if img.id == image_id), None)
                
                # Update attributes
                if 'eye_side' in image_data:
                    image.eye_side = image_data['eye_side']
                if 'quality_score' in image_data:
                    image.quality_score = image_data['quality_score']
                if 'anatomy_score' in image_data:
                    image.anatomy_score = image_data['anatomy_score']
                if 'site' in image_data:
                    image.site = image_data['site']
                if 'over_illuminated' in image_data:
                    image.over_illuminated = image_data['over_illuminated']
                if 'acquisition_date' in image_data:
                    image.acquisition_date = image_data['acquisition_date']
                
                return image
                
            def delete_image(self, image_id):
                if image_id not in [1, 2]:
                    raise ValueError(f"Image with ID {image_id} not found")
                return True
        
        class MockPatientService:
            def get_patient_by_id(self, patient_id):
                if patient_id == 1:
                    return sample_patient
                return None
        
        # Replace the services in the controller
        monkeypatch.setattr('app.controllers.web.image_controller.image_service', MockImageService())
        monkeypatch.setattr('app.controllers.web.image_controller.patient_service', MockPatientService())
    
    def test_upload_form_valid(self, client, mock_services):
        """Test GET request to upload form with valid patient ID."""
        response = client.get(url_for('images.upload_form', patient_id=1))
        
        # Assertions
        assert response.status_code == 200
        assert b'Upload Image for Patient' in response.data
        assert b'Image Upload' in response.data
        assert b'Eye Side' in response.data
    
    def test_upload_form_invalid(self, client, mock_services):
        """Test GET request to upload form with invalid patient ID."""
        response = client.get(url_for('images.upload_form', patient_id=999))
        
        # Assertions
        assert response.status_code == 302  # Redirect
        assert response.headers.get('Location').endswith('/patients/')
    
    def test_upload_valid(self, client, mock_services, monkeypatch):
        """Test POST request to upload with valid data."""
        import io
        from werkzeug.datastructures import FileStorage
        
        # Create a mock file using FileStorage
        mock_file = FileStorage(
            stream=io.BytesIO(b"test file content"),
            filename="test_image.jpg",
            content_type="image/jpeg",
        )
        
        # Mock the request in the controller to use our test file
        class MockRequest:
            @property
            def files(self):
                return {'image_file': mock_file}
            
            @property
            def form(self):
                return {
                    'eye_side': 'LEFT',
                    'quality_score': 'HIGH',
                    'anatomy_score': 'GOOD',
                    'acquisition_date': '2025-03-01'
                }
        
        # Replace the actual request with our mock
        monkeypatch.setattr('app.controllers.web.image_controller.request', MockRequest())
        
        # Now make the request
        response = client.post(
            url_for('images.upload', patient_id=1)
        )
        
        # Assertions
        assert response.status_code == 302  # Redirect
        assert response.headers.get('Location').endswith('/patients/1')
    
    def test_upload_invalid_data(self, client, mock_services, monkeypatch):
        """Test POST request to upload with invalid data."""
        import io
        from werkzeug.datastructures import FileStorage
        
        # Create a mock file using FileStorage
        mock_file = FileStorage(
            stream=io.BytesIO(b"test file content"),
            filename="test_image.jpg",
            content_type="image/jpeg",
        )
        
        # Mock the request in the controller to use our test file but with invalid data
        class MockRequest:
            @property
            def files(self):
                return {'image_file': mock_file}
            
            @property
            def form(self):
                return {
                    'eye_side': 'INVALID',  # Invalid eye_side value
                    'quality_score': 'HIGH',
                    'anatomy_score': 'GOOD',
                    'site': 'Test Clinic',
                    'acquisition_date': '2025-03-01'
                }
        
        # Replace the actual request with our mock
        monkeypatch.setattr('app.controllers.web.image_controller.request', MockRequest())
        
        # Now make the request
        response = client.post(
            url_for('images.upload', patient_id=1)
        )
        
        # Assertions
        assert response.status_code == 400
        assert b'Eye side must be one of' in response.data
    
    def test_show_valid(self, client, mock_services):
        """Test GET request to show with valid image ID."""
        response = client.get(url_for('images.show', image_id=1))
        
        # Assertions
        assert response.status_code == 200
        assert b'Image Details' in response.data
        assert b'LEFT' in response.data
    
    def test_show_invalid(self, client, mock_services):
        """Test GET request to show with invalid image ID."""
        response = client.get(url_for('images.show', image_id=999))
        
        # Assertions
        assert response.status_code == 302  # Redirect
        assert response.headers.get('Location').endswith('/patients/')
    
    def test_edit_valid(self, client, mock_services):
        """Test GET request to edit with valid image ID."""
        response = client.get(url_for('images.edit', image_id=1))
        
        # Assertions
        assert response.status_code == 200
        assert b'Edit Image' in response.data
        assert b'Current Image' in response.data
        assert b'Edit Image Information' in response.data
    
    def test_edit_invalid(self, client, mock_services):
        """Test GET request to edit with invalid image ID."""
        response = client.get(url_for('images.edit', image_id=999))
        
        # Assertions
        assert response.status_code == 302  # Redirect
        assert response.headers.get('Location').endswith('/patients/')
    
    def test_update_valid(self, client, mock_services):
        """Test POST request to update with valid data."""
        response = client.post(
            url_for('images.update', image_id=1),
            data={
                'eye_side': 'RIGHT',
                'quality_score': 'ACCEPTABLE',
                'anatomy_score': 'ACCEPTABLE',
                'site': 'Updated Clinic',
                'acquisition_date': '2025-03-15'
            }
        )
        
        # Assertions
        assert response.status_code == 302  # Redirect
        assert response.headers.get('Location').endswith('/images/1')
    
    def test_update_invalid_data(self, client, mock_services, monkeypatch):
        """Test POST request to update with invalid data."""
        # Create the request - we don't need to mock the file for update
        response = client.post(
            url_for('images.update', image_id=1),
            data={
                'eye_side': 'INVALID',  # Invalid eye_side value
                'quality_score': 'HIGH',
                'anatomy_score': 'GOOD',
                'site': 'Test Clinic',
                'acquisition_date': '2025-03-01'
            }
        )
        
        # Assertions - in this case, we should check for a redirect with status code 400
        assert response.status_code == 400
        # The controller redirects back to the edit page when validation fails
        location = response.headers.get('Location')
        assert location is not None
        assert '/images/1/edit' in location
    
    def test_update_invalid_id(self, client, mock_services):
        """Test POST request to update with invalid image ID."""
        response = client.post(
            url_for('images.update', image_id=999),
            data={
                'eye_side': 'RIGHT',
                'quality_score': 'ACCEPTABLE',
                'anatomy_score': 'ACCEPTABLE',
                'site': 'Updated Clinic',
                'acquisition_date': '2025-03-15'
            }
        )
        
        # Assertions
        assert response.status_code == 302  # Redirect
        assert response.headers.get('Location').endswith('/patients/')
    
    def test_delete_valid(self, client, mock_services):
        """Test POST request to delete with valid image ID."""
        response = client.post(url_for('images.delete', image_id=1))
        
        # Assertions
        assert response.status_code == 302  # Redirect
        assert response.headers.get('Location').endswith('/patients/1')
    
    def test_delete_invalid(self, client, mock_services):
        """Test POST request to delete with invalid image ID."""
        response = client.post(url_for('images.delete', image_id=999))
        
        # Assertions
        assert response.status_code == 302  # Redirect
        assert response.headers.get('Location').endswith('/patients/')