import logging
from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.models.patient import Sex
from app.services.patient_service import PatientService


patient_bp = Blueprint('patients', __name__)

patient_service = PatientService()

logger = logging.getLogger(__name__)

@patient_bp.route('/', methods=['GET', 'POST'])
def index():
    def create_patient():
        age = request.form.get('age')
        sex = request.form.get('sex')
        
        errors = validate_patient_data(age, sex)
        if errors:
            logger.warning(f"Invalid patient data: age={age}, sex={sex}, errors={errors}")
            for error in errors:
                flash(error, 'error')
            return render_template('patients/new.html'), 400
        
        try:
            patient_data = {'age': int(age), 'sex': sex}
            patient = patient_service.create_patient(patient_data)
            logger.info(f"Patient created successfully with id={patient.id}")
            flash("Patient created successfully!", "success")
            return redirect(url_for('patients.show', id=patient.id))
        except Exception as e:
            logger.error(f"Failed to create patient: {str(e)}", exc_info=True)
            flash("Error saving patient", 'error')
            return render_template('patients/new.html'), 500

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
        logger.warning(f"Attempted to access non-existent patient with id={id}")
        flash(f"Patient with id {id} Not found")
        return redirect(url_for("patients.index"))
    logger.debug(f"Showing patient with id={id}")
    return render_template("patients/show.html", patient=patient)

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
        logger.warning(f"Attempted to update non-existent patient with id={id}")
        flash("Patient not found", "error")
        return redirect(url_for("patients.index"))
    
    age = request.form.get('age')
    sex = request.form.get('sex')
    errors = validate_patient_data(age, sex)
    if errors:
        logger.warning(f"Invalid update data for patient {id}: age={age}, sex={sex}, errors={errors}")
        for error in errors:
            flash(error, 'error')
        return render_template('patients/edit.html', patient=patient), 400
    
    try:
        patient_data = {'age': int(age), 'sex': sex}
        patient_service.update_patient(id, patient_data)
        logger.info(f"Patient {id} updated successfully")
        flash(f"Patient updated successfully!", "success")
        return redirect(url_for("patients.show", id=patient.id))
    except Exception as e:
        logger.error(f"Failed to update patient {id}: {str(e)}", exc_info=True)
        flash("Error updating the patient", "error")
        return render_template("patients/edit.html", patient=patient), 500

@patient_bp.route('/<int:id>/delete', methods=['POST'])
def delete(id):
    patient = patient_service.get_patient_by_id(id)
    if not patient:
        logger.warning(f"Attempted to delete non-existent patient with id={id}")
        flash(f"Patient with id {id} not found")
        return redirect(url_for("patients.index"))
    
    try:
        patient_service.delete_patient(id)
        logger.info(f"Patient {id} deleted successfully")
        flash(f"Patient id {id} deleted successfully", 'success')
        return redirect(url_for("patients.index"))
    except Exception as e:
        logger.error(f"Failed to delete patient {id}: {str(e)}", exc_info=True)
        flash("Error deleting patient", "error")
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