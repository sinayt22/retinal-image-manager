from app.models.patient import Patient
from app import db

class PatientService:
    def get_all_patients(self):
        return Patient.query.order_by(Patient.created_at.desc()).all()

    def get_patient_by_id(self, patient_id):
        return Patient.query.get(patient_id)

    def create_patient(self, patient_data):
        patient = Patient(
            birth_date = patient_data.get('birth_date'),
            sex = patient_data.get('sex')
        )
        db.session.add(patient)
        db.session.commit()
        return patient
    
    def update_patient(self, patient_id, patient_data):
        patient = self.get_patient_by_id(patient_id)
        if not patient:
            raise ValueError(f"Patient with ID {patient} not found")
        
        if 'birth_date' in patient_data:
            patient.birth_date = patient_data['birth_date']
        if 'sex' in patient_data:
            patient.sex = patient_data['sex']
        
        db.session.commit()
        return patient
    
    def delete_patient(self, patient_id):
        patient = self.get_patient_by_id(patient_id)
        if not patient:
            raise ValueError(f"Patient with ID {patient_id} not found")
        
        db.session.delete(patient)
        db.session.commit()
        return True