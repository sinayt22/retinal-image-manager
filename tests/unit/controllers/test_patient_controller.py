import pytest
from flask import url_for
from app.models.patient import Patient, Sex
from app.services.patient_service import PatientService


class TestPatientController:
    @pytest.fixture
    def mock_patient_service(self, monkeypatch):
        """
        Mock PatientService to avoid database interactions
        """
        class MockPatientService:
            def get_all_patients(self):
                return [
                    Patient(id=1, age=30, sex=Sex.MALE),
                    Patient(id=2, age=45, sex=Sex.FEMALE)
                ]
            
            def get_patient_by_id(self, patient_id):
                if patient_id == 1:
                    return Patient(id=1, age=30, sex=Sex.MALE)
                if patient_id == 2:
                    return Patient(id=2, age=45, sex=Sex.FEMALE)
                return None
            
            def create_patient(self, patient_data):
                patient = Patient(
                    id=3,
                    age=patient_data.get('age'),
                    sex=patient_data.get('sex')
                )
                return patient
            
            def update_patient(self, patient_id, patient_data):
                if patient_id not in [1, 2]:
                    raise ValueError(f"Patient with ID {patient_id} not found")
                
                patient = Patient(
                    id=patient_id,
                    age=patient_data.get('age', 30),
                    sex=patient_data.get('sex', Sex.MALE)
                )
                return patient
            
            def delete_patient(self, patient_id):
                if patient_id not in [1, 2]:
                    raise ValueError(f"Patient with ID {patient_id} not found")
                return True
        
        # Replace the service in the controller
        monkeypatch.setattr('app.controllers.web.patient_controller.patient_service', MockPatientService())
    
    def test_index_get(self, client, mock_patient_service):
        # Test GET request to index
        response = client.get(url_for('patients.index'))
        
        # Assertions
        assert response.status_code == 200
        assert b'Patients List' in response.data
        assert b'ID' in response.data
        assert b'Age' in response.data
        assert b'Sex' in response.data
    
    def test_index_post_valid(self, client, mock_patient_service):
        # Test POST request to index with valid data
        response = client.post(
            url_for('patients.index'), 
            data={'age': '25', 'sex': 'MALE'}
        )
        
        # Assertions
        assert response.status_code == 302  # Redirect
        location = response.headers.get('Location')
        assert '/patients/3' in location
    
    def test_index_post_invalid(self, client, mock_patient_service):
        # Test POST request to index with invalid data
        response = client.post(
            url_for('patients.index'), 
            data={'age': 'invalid', 'sex': 'Male'}
        )
        
        # Assertions
        assert response.status_code == 400
        assert b'Age must be a positive number' in response.data
        
        # Test with missing data
        response = client.post(
            url_for('patients.index'), 
            data={'age': '25'}  # Missing sex
        )
        
        # Assertions
        assert response.status_code == 400
        assert b'Sex is required' in response.data
    
    def test_new(self, client, mock_patient_service):
        # Test GET request to new
        response = client.get(url_for('patients.new'))
        
        # Assertions
        assert response.status_code == 200
        assert b'Add New Patient' in response.data
        assert b'Age' in response.data
        assert b'Sex' in response.data
    
    def test_show_valid(self, client, mock_patient_service):
        # Test GET request to show with valid ID
        response = client.get(url_for('patients.show', id=1))
        
        # Assertions
        assert response.status_code == 200
        assert b'Patient Details' in response.data
        assert b'Age' in response.data
        assert b'Sex' in response.data
    
    def test_show_invalid(self, client, mock_patient_service):
        # Test GET request to show with invalid ID
        response = client.get(url_for('patients.show', id=999))
        
        # Assertions
        assert response.status_code == 302  # Redirect
        location = response.headers.get('Location')
        assert '/patients/' in location
    
    def test_edit_valid(self, client, mock_patient_service):
        # Test GET request to edit with valid ID
        response = client.get(url_for('patients.edit', id=1))
        
        # Assertions
        assert response.status_code == 200
        assert b'Edit Patient' in response.data
        assert b'Age' in response.data
        assert b'Sex' in response.data
    
    def test_update_valid(self, client, mock_patient_service):
        # Test POST request to update with valid data
        response = client.post(
            url_for('patients.update', id=1), 
            data={'age': '35', 'sex': 'FEMALE'}
        )
        
        # Assertions
        assert response.status_code == 302  # Redirect
        location = response.headers.get('Location')
        assert '/patients/1' in location
    
    def test_update_invalid_data(self, client, mock_patient_service):
        # Test POST request to update with invalid data
        response = client.post(
            url_for('patients.update', id=1), 
            data={'age': '-5', 'sex': 'FEMALE'}
        )
        
        # Assertions
        assert response.status_code == 400
        assert b'Age must be a positive number' in response.data
    
    def test_update_invalid_id(self, client, mock_patient_service):
        # Test POST request to update with invalid ID
        response = client.post(
            url_for('patients.update', id=999), 
            data={'age': '35', 'sex': 'Female'}
        )
        
        # Assertions
        assert response.status_code == 302  # Redirect
        location = response.headers.get('Location')
        assert '/patients/' in location
    
    def test_delete_valid(self, client, mock_patient_service):
        # Test POST request to delete with valid ID
        response = client.post(url_for('patients.delete', id=1))
        
        # Assertions
        assert response.status_code == 302  # Redirect
        location = response.headers.get('Location')
        assert '/patients/' in location
    
    def test_delete_invalid(self, client, mock_patient_service):
        # Test POST request to delete with invalid ID
        response = client.post(url_for('patients.delete', id=999))
        
        # Assertions
        assert response.status_code == 302  # Redirect
        location = response.headers.get('Location')
        assert '/patients/' in location