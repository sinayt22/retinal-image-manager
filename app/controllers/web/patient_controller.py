
from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.models.patient import Sex
from app.services.patient_service import PatientService


patient_bp = Blueprint('patients', __name__)

patient_service = PatientService()

@patient_bp.route('/', methods=['GET', 'POST'])
def index():
    def create_patient():
        age = request.form.get('age')
        sex = request.form.get('sex')
        
        errors = validate_patient_data(age, sex)
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('patients/new.html'), 400
        
        try:
            patient_data = {'age': int(age), 'sex': sex}
            patient = patient_service.create_patient(patient_data)
            flash("Patient created successfully!", "success")
            return redirect(url_for('patients.show', id=patient.id))
        except Exception as e:
            flash(f"Error saving patient", 'error')
            return render_template('patients/new.html'), 400



    if request.method == 'POST':
        return create_patient()
    else:
        patients = patient_service.get_all_patients()
        return render_template('patients/index.html', patients=patients)

@patient_bp.route('/new', methods=['GET'])
def new():
    return render_template('patients/new.html')

@patient_bp.route('/<int:id>', methods=['GET'])
def show(id):
    patient = patient_service.get_patient_by_id(id)
    if not patient:
        flash(f"Patient with id {id} Not found")
        return redirect(url_for("patients.index"))

@patient_bp.route('/<int:id>/edit', methods=['GET'])
def edit(id):
    patient = patient_service.get_patient_by_id(id)
    if not patient:
        flash("Patient not found", "error")
        redirect(url_for("patients.index"))
    
    return render_template("patients/edit.html", patient=patient)

@patient_bp.route('/<int:id>/update', methods=['POST'])
def update(id):
    patient = patient_service.get_patient_by_id(id)

    if not patient:
        flash("Patient not found", "error")
        redirect(url_for("patients.index"))
    
    age = request.form.get('age')
    sex = request.form.get('sex')
    errors = validate_patient_data(age, sex)
    if errors:
        for error in errors:
            flash(error, 'error')
        return render_template('patients/edit.html', patient=patient), 400
    
    try:
        patient_data = {'age': int(age), 'sex': sex}
        patient_service.update_patient(id, patient_data)
        flash(f"Patient updated successfully!", "success")
        return render_template(url_for("patient.show", patient=patient))
    except Exception:
        flash(f"Error updating the patient", "error")
        return render_template("patients/edit.html", patient=patient), 500

@patient_bp
def delete(id):
    patient = patient_service.get_patient_by_id(id)
    if not patient:
        flash(f"Patient with id {id} not found")
        return redirect(url_for("patients.index"))
    
    try:
        patient_service.delete_patient(id)
        flash(f"Patient id {id} deleted successfully", 'success')
        return redirect(url_for("patients.index"))
    except:
        flash(f"Error deleting patient with id: {id}", "error")
        return redirect(url_for("patients.index"))
    

def validate_patient_data(age, sex):
    errors = []
    if not age:
        errors.append('Age is required')
    elif not age.isdigit() or int(age) <= 0:
        errors.append('Age must be a positive number')

    if not sex:
        errors.append("Sex is required")
    elif sex not in [sex_type.value for sex_type in Sex]:
        errors.append(f'Sex must be one of: {", ".join([sex_type.value for sex_type in Sex])}')
    
    return errors