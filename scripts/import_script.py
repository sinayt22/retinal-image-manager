#!/usr/bin/env python
import os
import sys
import csv
import argparse
import logging
from datetime import datetime

# Add the parent directory to the Python path so we can import the app package
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root =os.path.dirname(script_dir)
sys.path.insert(0, project_root)

# Now we can import from the app package
from app import create_app
from app.models.patient import Patient, Sex
from app.models.image import Image, EyeSide
from app.services.patient_service import PatientService
from app.services.image_service import ImageService

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("import.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Import patient data and images')
    parser.add_argument('--csv-file', 
                      default='scripts/test_data/patients.csv',
                      help='Path to the CSV file with patient data (default: %(default)s)')
    parser.add_argument('--images-folder', 
                      default='scripts/test_data/images',
                      help='Path to the folder containing images (default: %(default)s)')
    return parser.parse_args()

def map_sex_value(sex_str):
    """Map CSV sex string to Sex enum value."""
    sex_map = {
        'Male': Sex.MALE,
        'Female': Sex.FEMALE,
        'Other': Sex.OTHER,
        # Add more mappings if needed
    }
    return sex_map.get(sex_str, Sex.OTHER)

def extract_id_from_filename(filename):
    """Extract patient ID and eye side from image filename."""
    base_name = os.path.splitext(filename)[0]  # Remove file extension
    
    if '_left' in base_name.lower():
        eye_side = EyeSide.LEFT
        patient_code = base_name.lower().replace('_left', '')
    elif '_right' in base_name.lower():
        eye_side = EyeSide.RIGHT
        patient_code = base_name.lower().replace('_right', '')
    else:
        return None, None  # Unrecognized format
    
    # Extract numeric ID
    if patient_code.startswith('rs-'):
        try:
            patient_id = int(patient_code[3:])
            return patient_id, eye_side
        except ValueError:
            return None, None
    return None, None

def import_patients(csv_file, patient_service):
    """Import patients from CSV file."""
    updated_count = 0
    created_count = 0
    error_count = 0
    
    try:
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                try:
                    # Extract patient ID (remove RS- prefix and convert to int)
                    patient_code = row['subject_id']
                    if patient_code.startswith('RS-'):
                        patient_id = int(patient_code[3:])
                    else:
                        patient_id = int(patient_code)
                    
                    # Parse date of birth
                    dob = datetime.strptime(row['date_of_birth'], '%Y-%m-%d').date()
                    
                    # Map sex value
                    sex = map_sex_value(row['sex'])
                    
                    # Prepare patient data
                    patient_data = {
                        'birth_date': dob,
                        'sex': sex
                    }
                    
                    # Check if patient exists
                    existing_patient = patient_service.get_patient_by_id(patient_id)
                    
                    if existing_patient:
                        # Update existing patient
                        patient_service.update_patient(patient_id, patient_data)
                        logger.info(f"Updated patient: ID={patient_id}, DOB={dob}, Sex={sex.value}")
                        updated_count += 1
                    else:
                        # Create new patient with specified ID
                        # This requires a custom method since the service doesn't allow setting ID
                        from app import db
                        patient = Patient(id=patient_id, birth_date=dob, sex=sex)
                        db.session.add(patient)
                        db.session.commit()
                        logger.info(f"Created patient: ID={patient_id}, DOB={dob}, Sex={sex.value}")
                        created_count += 1
                        
                except Exception as e:
                    logger.error(f"Error processing patient {row.get('subject_id', 'unknown')}: {str(e)}")
                    error_count += 1
    
    except Exception as e:
        logger.error(f"Error opening or reading CSV file: {str(e)}")
        return 0, 0, 0
    
    return created_count, updated_count, error_count

def import_images(images_folder, patient_service, image_service):
    """Import images from the specified folder."""
    if not os.path.exists(images_folder):
        logger.error(f"Images folder not found: {images_folder}")
        return 0, 0
    
    processed_count = 0
    error_count = 0
    
    for filename in os.listdir(images_folder):
        if not (filename.lower().endswith('.jpg') or 
                filename.lower().endswith('.jpeg') or 
                filename.lower().endswith('.png')):
            continue
        
        patient_id, eye_side = extract_id_from_filename(filename)
        
        if not patient_id or not eye_side:
            logger.warning(f"Couldn't extract patient ID or eye side from filename: {filename}")
            error_count += 1
            continue
        
        # Check if patient exists
        patient = patient_service.get_patient_by_id(patient_id)
        if not patient:
            logger.warning(f"Patient with ID {patient_id} does not exist for image: {filename}")
            error_count += 1
            continue
        
        try:
            # Prepare image data
            image_data = {
                'patient_id': patient_id,
                'eye_side': eye_side,
                'acquisition_date': datetime.now()
            }
            
            # Create image file object
            from werkzeug.datastructures import FileStorage
            file_path = os.path.join(images_folder, filename)
            with open(file_path, 'rb') as img_file:
                file = FileStorage(
                    stream=img_file,
                    filename=filename,
                    content_type='image/jpeg' if filename.lower().endswith(('.jpg', '.jpeg')) else 'image/png'
                )
                
                # Create the image
                image = image_service.create_image(image_data, file)
                logger.info(f"Imported image: {filename} for patient ID={patient_id}, Eye={eye_side.value}")
                processed_count += 1
                
        except Exception as e:
            logger.error(f"Error importing image {filename}: {str(e)}")
            error_count += 1
    
    return processed_count, error_count

def main():
    """Main function to run the import script."""
    args = parse_args()
    
    # Initialize Flask app
    app = create_app()
    
    # Check if files/folders exist
    if not os.path.exists(args.csv_file):
        logger.error(f"CSV file not found: {args.csv_file}")
        print(f"Error: CSV file not found: {args.csv_file}")
        return
    
    with app.app_context():
        patient_service = PatientService()
        image_service = ImageService()
        
        # Import patients
        logger.info(f"Starting patient import from {args.csv_file}")
        created, updated, errors = import_patients(args.csv_file, patient_service)
        logger.info(f"Patient import completed: {created} created, {updated} updated, {errors} errors")
        print(f"Patient import completed: {created} created, {updated} updated, {errors} errors")
        
        # Import images if folder provided and exists
        if args.images_folder:
            if os.path.exists(args.images_folder):
                logger.info(f"Starting image import from {args.images_folder}")
                processed, errors = import_images(args.images_folder, patient_service, image_service)
                logger.info(f"Image import completed: {processed} processed, {errors} errors")
                print(f"Image import completed: {processed} processed, {errors} errors")
            else:
                logger.warning(f"Images folder not found: {args.images_folder}")
                print(f"Warning: Images folder not found: {args.images_folder}")
        else:
            logger.info("No images folder specified, skipping image import")
        
        logger.info("Import process completed")
        print("Import process completed")

if __name__ == "__main__":
    main()