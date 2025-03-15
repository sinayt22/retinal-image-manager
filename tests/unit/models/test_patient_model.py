import pytest
from datetime import date, datetime, timezone
from dateutil.relativedelta import relativedelta
from app.models.patient import Patient, Sex


class TestPatientModel:
    @pytest.fixture
    def sample_patient(self):
        """Create a sample patient for testing."""
        return Patient(
            id=1,
            birth_date=date(1990, 1, 15),
            sex=Sex.MALE,
            created_at=datetime(2025, 3, 1, tzinfo=timezone.utc),
            modified_at=datetime(2025, 3, 1, tzinfo=timezone.utc)
        )
    
    def test_patient_creation(self, sample_patient):
        """Test the creation of a patient instance."""
        assert sample_patient.id == 1
        assert sample_patient.birth_date == date(1990, 1, 15)
        assert sample_patient.sex == Sex.MALE
        assert sample_patient.created_at.year == 2025
        assert sample_patient.created_at.month == 3
    
    def test_patient_repr(self, sample_patient):
        """Test the string representation of a patient."""
        assert repr(sample_patient) == "<Patient 1>"
    
    def test_patient_age_calculation(self, sample_patient, monkeypatch):
        """Test the age calculation property."""
        test_date = date(2025, 3, 15)
        
        def mock_relativedelta(today, birth_date):
            # Simple age calculation for testing
            years = today.year - birth_date.year
            if (today.month, today.day) < (birth_date.month, birth_date.day):
                years -= 1
            return type('obj', (object,), {'years': years})()
        
        monkeypatch.setattr('app.models.patient.date', type('obj', (object,), {'today': lambda: test_date}))
        
        # The patient born on 1990-01-15 would be 35 years old on 2025-03-15
        assert sample_patient.age == 35
        
        # Test with a different birth date
        sample_patient.birth_date = date(2000, 5, 20)
        # Person born on 2000-05-20 would be 24 years old on 2025-03-15
        assert sample_patient.age == 24
        
        # Test with a birth date after today's date
        sample_patient.birth_date = date(2025, 4, 1)  # Future date
        # Age should be 0 for future birth dates
        assert sample_patient.age == 0
    
    def test_to_dict(self, sample_patient):
        """Test the to_dict method."""
        patient_dict = sample_patient.to_dict()
        
        assert patient_dict["id"] == 1
        assert patient_dict["birth_date"] == "1990-01-15"
        assert "age" in patient_dict
        assert patient_dict["sex"] == Sex.MALE
        assert "create_at" in patient_dict
        assert "modified_at" in patient_dict
    
    def test_sex_enum_values(self):
        """Test sex enum values."""
        assert Sex.MALE.value == "MALE"
        assert Sex.FEMALE.value == "FEMALE"
        assert Sex.OTHER.value == "OTHER"