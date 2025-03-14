import pytest
from app.models.patient import Patient, Sex
from app.services.patient_service import PatientService


@pytest.mark.usefixtures('app_context')
class TestPatientService:
    @pytest.fixture
    def patient_service(self):
        return PatientService()
    
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
        monkeypatch.setattr('app.services.patient_service.db.session', mock_session)
        
        return mock_session
    
    def test_get_all_patients(self, patient_service, monkeypatch):
        # Mock data
        mock_patients = [
            Patient(id=1, age=30, sex=Sex.MALE),
            Patient(id=2, age=45, sex=Sex.FEMALE)
        ]
        
        # Mock the query
        class MockQuery:
            def order_by(self, _):
                return self
                
            def all(self):
                return mock_patients
        
        monkeypatch.setattr(Patient, 'query', MockQuery())
        
        # Test
        patients = patient_service.get_all_patients()
        
        # Assertions
        assert len(patients) == 2
        assert patients[0].id == 1
        assert patients[1].id == 2
    
    def test_get_patient_by_id(self, patient_service, monkeypatch):
        # Mock data
        mock_patient = Patient(id=1, age=30, sex=Sex.MALE)
        
        # Mock the query
        class MockQuery:
            def get(self, id):
                if id == 1:
                    return mock_patient
                return None
        
        monkeypatch.setattr(Patient, 'query', MockQuery())
        
        # Test
        patient = patient_service.get_patient_by_id(1)
        
        # Assertions
        assert patient is not None
        assert patient.id == 1
        assert patient.age == 30
        assert patient.sex == Sex.MALE
        
        # Test non-existent patient
        patient = patient_service.get_patient_by_id(999)
        assert patient is None
    
    def test_create_patient(self, patient_service, db_session, monkeypatch):
        # Mock data
        patient_data = {
            'age': 25,
            'sex': Sex.FEMALE
        }
        
        # Instead of mocking __init__, mock the entire Patient class
        class MockPatient:
            def __init__(self, **kwargs):
                self.id = 1
                self.age = kwargs.get('age')
                self.sex = kwargs.get('sex')
        
        # Replace the Patient class in the service
        monkeypatch.setattr('app.services.patient_service.Patient', MockPatient)
        
        # Test
        patient = patient_service.create_patient(patient_data)
        
        # Assertions
        assert patient is not None
        assert patient.id == 1
        assert patient.age == 25
        assert patient.sex == Sex.FEMALE
        
        # Check if session methods were called
        assert len(db_session.added) == 1
        assert db_session.committed is True
    
    def test_update_patient(self, patient_service, db_session, monkeypatch):
        # Mock data
        mock_patient = Patient(id=1, age=30, sex=Sex.MALE)
        
        # Mock the get_patient_by_id method
        monkeypatch.setattr(
            patient_service, 
            'get_patient_by_id', 
            lambda id: mock_patient if id == 1 else None
        )
        
        # Update data
        update_data = {
            'age': 31,
            'sex': Sex.OTHER
        }
        
        # Test
        updated_patient = patient_service.update_patient(1, update_data)
        
        # Assertions
        assert updated_patient is not None
        assert updated_patient.age == 31
        assert updated_patient.sex == Sex.OTHER
        assert db_session.committed is True
        
        # Test updating non-existent patient
        with pytest.raises(ValueError, match="Patient with ID None not found"):
            patient_service.update_patient(999, update_data)
    
    def test_delete_patient(self, patient_service, db_session, monkeypatch):
        # Mock data
        mock_patient = Patient(id=1, age=30, sex=Sex.MALE)
        
        # Mock the get_patient_by_id method
        monkeypatch.setattr(
            patient_service, 
            'get_patient_by_id', 
            lambda id: mock_patient if id == 1 else None
        )
        
        # Test
        result = patient_service.delete_patient(1)
        
        # Assertions
        assert result is True
        assert len(db_session.deleted) == 1
        assert db_session.committed is True
        
        # Test deleting non-existent patient
        with pytest.raises(ValueError, match="Patient with ID 999 not found"):
            patient_service.delete_patient(999)