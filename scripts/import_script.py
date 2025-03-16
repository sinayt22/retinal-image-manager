#!/usr/bin/env python
import os
import sys
import csv
import argparse
import logging
import random
from datetime import datetime, timedelta
from collections import defaultdict

# Add the parent directory to the Python path so we can import the app package
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

# Now we can import from the app package
from app import create_app, db
from app.models.patient import Patient, Sex
from app.models.image import Image, EyeSide, ImageQualityScore, AnatomyScore
from app.models.site import Site
from app.services.patient_service import PatientService
from app.services.image_service import ImageService
from app.services.site_service import SiteService

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

# Default locations for site generation
DEFAULT_LOCATIONS = [
    "New York, NY", "Los Angeles, CA", "Chicago, IL", "Houston, TX", "Phoenix, AZ",
    "Philadelphia, PA", "San Antonio, TX", "San Diego, CA", "Dallas, TX", "San Jose, CA",
    "Austin, TX", "Jacksonville, FL", "Fort Worth, TX", "Columbus, OH", "Charlotte, NC"
]

# Default site names for site generation
DEFAULT_SITE_NAMES = [
    "Main Hospital", "Downtown Clinic", "University Medical Center", "Rural Health Clinic",
    "Community Hospital", "Eye Care Center", "Ophthalmology Department", "Vision Care Center",
    "Regional Medical Facility", "Eye Health Specialists", "Mobile Eye Care Unit",
    "Surgical Eye Care", "Family Vision Care", "Advanced Eye Center", "Medical Eye Services"
]

# Site quality profiles for more realistic data distribution
SITE_QUALITY_PROFILES = {
    'high_quality': {
        'quality_score': {'HIGH': 0.7, 'ACCEPTABLE': 0.25, 'LOW': 0.05},
        'anatomy_score': {'GOOD': 0.7, 'ACCEPTABLE': 0.25, 'POOR': 0.05},
        'over_illuminated': 0.05  # Probability of being over illuminated
    },
    'medium_quality': {
        'quality_score': {'HIGH': 0.4, 'ACCEPTABLE': 0.4, 'LOW': 0.2},
        'anatomy_score': {'GOOD': 0.4, 'ACCEPTABLE': 0.4, 'POOR': 0.2},
        'over_illuminated': 0.15
    },
    'low_quality': {
        'quality_score': {'HIGH': 0.2, 'ACCEPTABLE': 0.3, 'LOW': 0.5},
        'anatomy_score': {'GOOD': 0.2, 'ACCEPTABLE': 0.3, 'POOR': 0.5},
        'over_illuminated': 0.3
    }
}

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Import patient data and images')
    parser.add_argument('--csv-file', 
                      default='scripts/test_data/patients.csv',
                      help='Path to the CSV file with patient data (default: %(default)s)')
    parser.add_argument('--images-folder', 
                      default='scripts/test_data/images',
                      help='Path to the folder containing images (default: %(default)s)')
    parser.add_argument('--randomize',
                      action='store_true',
                      help='Randomize image quality, anatomy scores, and site values')
    parser.add_argument('--num-sites',
                      type=int,
                      default=5,
                      help='Number of sites to generate if not specified (default: %(default)s)')
    parser.add_argument('--num-patients',
                      type=int,
                      default=0,
                      help='Number of patients to generate if there are not enough (default: 0, no generation)')
    parser.add_argument('--max-images-per-patient',
                      type=int,
                      default=4,
                      help='Maximum number of images per patient for generated data (default: %(default)s)')
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

def weighted_choice(choices_dict):
    """Select an item from a dictionary based on weights."""
    items = list(choices_dict.keys())
    weights = list(choices_dict.values())
    total = sum(weights)
    r = random.uniform(0, total)
    upto = 0
    for i, w in enumerate(weights):
        if upto + w >= r:
            return items[i]
        upto += w
    return items[-1]  # Fallback

def get_score_based_on_profile(profile, score_type):
    """Get a score value based on the site's quality profile."""
    score_dict = profile[score_type]
    choice = weighted_choice(score_dict)
    if score_type == 'quality_score':
        return ImageQualityScore[choice]
    elif score_type == 'anatomy_score':
        return AnatomyScore[choice]
    return choice

def generate_sites(num_sites, site_service):
    """Generate or retrieve existing sites with quality profiles."""
    existing_sites = site_service.get_all_sites()
    existing_count = len(existing_sites)
    
    if existing_count >= num_sites:
        logger.info(f"Using {num_sites} existing sites")
        return existing_sites[:num_sites]
    
    # Determine how many more sites we need to create
    sites_to_create = num_sites - existing_count
    logger.info(f"Creating {sites_to_create} additional sites")
    
    # Create new sites with random names and locations
    created_sites = []
    existing_names = [site.name for site in existing_sites]
    
    # Assign quality profiles to the sites we'll create
    # Distribute quality profiles to make a realistic mix
    quality_distribution = []
    quality_distribution.extend(['high_quality'] * int(sites_to_create * 0.3))  # 30% high quality
    quality_distribution.extend(['medium_quality'] * int(sites_to_create * 0.5))  # 50% medium quality
    quality_distribution.extend(['low_quality'] * int(sites_to_create * 0.2))  # 20% low quality
    
    # If any rounding issues, fill with medium quality
    while len(quality_distribution) < sites_to_create:
        quality_distribution.append('medium_quality')
    
    # Shuffle the quality distribution
    random.shuffle(quality_distribution)
    
    for i in range(sites_to_create):
        # Find a name that doesn't exist yet
        while True:
            name = random.choice(DEFAULT_SITE_NAMES)
            site_name = f"{name} {i+1}"
            if site_name not in existing_names:
                existing_names.append(site_name)
                break
        
        location = random.choice(DEFAULT_LOCATIONS)
        site_data = {'name': site_name, 'location': location}
        
        try:
            site = site_service.create_site(site_data)
            
            # Store the quality profile in a site attribute
            # This is for our script's use, not persisted in the database
            site.quality_profile = SITE_QUALITY_PROFILES[quality_distribution[i]]
            
            created_sites.append(site)
            logger.info(f"Created site: {site.name} in {site.location} with {quality_distribution[i]} profile")
        except Exception as e:
            logger.error(f"Error creating site: {str(e)}")
    
    # Assign quality profiles to existing sites if any
    for i, site in enumerate(existing_sites):
        # Randomly assign quality profiles to existing sites
        profile_type = random.choice(list(SITE_QUALITY_PROFILES.keys()))
        site.quality_profile = SITE_QUALITY_PROFILES[profile_type]
        logger.info(f"Assigned {profile_type} to existing site: {site.name}")
    
    # Return the combined list of existing and new sites
    return existing_sites + created_sites

def generate_random_patients(num_patients, patient_service):
    """Generate random patients if needed."""
    existing_count = len(patient_service.get_all_patients())
    
    if existing_count >= num_patients:
        logger.info(f"Already have {existing_count} patients, no need to generate more")
        return 0
    
    patients_to_create = num_patients - existing_count
    logger.info(f"Generating {patients_to_create} additional patients")
    
    created_count = 0
    error_count = 0
    generated_patients = []
    
    # Get the highest existing patient ID
    highest_id = 1
    try:
        # This is a simplified approach - in a real DB you might use a MAX query
        existing_patients = patient_service.get_all_patients()
        if existing_patients:
            highest_id = max(patient.id for patient in existing_patients) + 1
    except Exception as e:
        logger.error(f"Error finding highest patient ID: {str(e)}")
    
    # Generate new patients
    for i in range(patients_to_create):
        try:
            # Generate random birth date between 1950 and 2010
            year = random.randint(1950, 2010)
            month = random.randint(1, 12)
            day = random.randint(1, 28)  # Keeping it simple by avoiding edge cases with day ranges
            birth_date = datetime(year, month, day).date()
            
            # Randomly select sex
            sex = random.choice(list(Sex))
            
            # Create patient
            patient = Patient(
                id=highest_id + i,
                birth_date=birth_date,
                sex=sex
            )
            db.session.add(patient)
            db.session.commit()
            
            logger.info(f"Generated patient: ID={patient.id}, DOB={birth_date}, Sex={sex.value}")
            created_count += 1
            generated_patients.append(patient)
            
        except Exception as e:
            logger.error(f"Error generating patient: {str(e)}")
            error_count += 1
    
    logger.info(f"Patient generation completed: {created_count} created, {error_count} errors")
    return generated_patients

def get_image_files(images_folder):
    """Get all valid image files from a folder."""
    images = []
    
    if os.path.exists(images_folder):
        for filename in os.listdir(images_folder):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                images.append(os.path.join(images_folder, filename))
    
    return images

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

def import_images_with_randomization(images_folder, patient_service, image_service, site_service, num_patients=0, num_sites=5, max_images_per_patient=4):
    """Import images with randomized metadata and consistent site assignment per patient."""
    # Generate sites if randomizing
    sites = generate_sites(num_sites, site_service)
    if not sites:
        logger.error("No sites available for randomization")
        return 0, 0
    
    # Get all existing patients
    existing_patients = patient_service.get_all_patients()
    
    # Generate additional patients if needed
    generated_patients = []
    if num_patients > 0:
        generated_patients = generate_random_patients(num_patients, patient_service)
    
    # Get all patients (existing + newly generated)
    all_patients = patient_service.get_all_patients()
    if not all_patients:
        logger.error("No patients available")
        return 0, 0
    
    # Get all image files
    image_files = get_image_files(images_folder)
    if not image_files:
        logger.error(f"No images found in {images_folder}")
        return 0, 0
    
    # Process original images first (those with extractable patient IDs)
    processed_count = 0
    error_count = 0
    patient_sites = {}  # Track which site a patient is assigned to
    patient_images = defaultdict(list)  # Track how many images each patient has
    
    # First pass: process images with original patient IDs
    for file_path in image_files:
        filename = os.path.basename(file_path)
        patient_id, eye_side = extract_id_from_filename(filename)
        
        if patient_id and eye_side:
            # Get or find patient
            patient = patient_service.get_patient_by_id(patient_id)
            if not patient:
                continue  # Skip if patient doesn't exist
            
            # Get or assign a site to this patient
            if patient_id not in patient_sites:
                patient_sites[patient_id] = random.choice(sites)
                logger.info(f"Assigned patient {patient_id} to site: {patient_sites[patient_id].name}")
            
            site = patient_sites[patient_id]
            
            try:
                # Get quality scores based on site profile
                profile = getattr(site, 'quality_profile', SITE_QUALITY_PROFILES['medium_quality'])
                quality_score = get_score_based_on_profile(profile, 'quality_score')
                anatomy_score = get_score_based_on_profile(profile, 'anatomy_score')
                is_over_illuminated = random.random() < profile['over_illuminated']
                
                # Prepare image data
                image_data = {
                    'patient_id': patient_id,
                    'eye_side': eye_side,
                    'quality_score': quality_score,
                    'anatomy_score': anatomy_score,
                    'site_id': site.id,
                    'over_illuminated': is_over_illuminated,
                    'acquisition_date': datetime.now() - timedelta(days=random.randint(0, 365))
                }
                
                # Create image file object
                from werkzeug.datastructures import FileStorage
                with open(file_path, 'rb') as img_file:
                    file = FileStorage(
                        stream=img_file,
                        filename=filename,
                        content_type='image/jpeg' if filename.lower().endswith(('.jpg', '.jpeg')) else 'image/png'
                    )
                    
                    # Create the image
                    image = image_service.create_image(image_data, file)
                    
                    # Log the details
                    logger.info(
                        f"Imported image: {filename} for patient ID={patient_id}, "
                        f"Eye={eye_side.value}, "
                        f"Quality={quality_score.value}, "
                        f"Anatomy={anatomy_score.value}, "
                        f"Site={site.name}, "
                        f"Over-illuminated={is_over_illuminated}"
                    )
                    processed_count += 1
                    patient_images[patient_id].append((eye_side, file_path))
                    
            except Exception as e:
                logger.error(f"Error importing image {filename}: {str(e)}")
                error_count += 1
    
    # Second pass: Assign remaining images to generated patients
    if generated_patients:
        logger.info(f"Processing {len(generated_patients)} generated patients for image assignment")
        
        # Assign sites to generated patients
        for patient in generated_patients:
            if patient.id not in patient_sites:
                patient_sites[patient.id] = random.choice(sites)
        
        # Get a list of all patients who don't have any images yet
        patients_without_images = [p.id for p in all_patients if p.id not in patient_images]
        
        # Decide how many of these patients will have images (not all should have images)
        percentage_with_images = 0.7  # 70% of patients will have images
        patients_to_get_images = random.sample(
            patients_without_images, 
            k=min(len(patients_without_images), int(len(patients_without_images) * percentage_with_images))
        )
        
        logger.info(f"{len(patients_to_get_images)} patients without images will be assigned some")
        
        # For each patient that should get images, assign 1-max_images_per_patient images
        for patient_id in patients_to_get_images:
            site = patient_sites[patient_id]
            profile = getattr(site, 'quality_profile', SITE_QUALITY_PROFILES['medium_quality'])
            
            # Decide how many images this patient will have (1 to max_images_per_patient)
            num_images = random.randint(1, max_images_per_patient)
            
            # Randomly select images from the pool
            for _ in range(num_images):
                file_path = random.choice(image_files)
                filename = os.path.basename(file_path)
                eye_side = random.choice(list(EyeSide))
                
                try:
                    quality_score = get_score_based_on_profile(profile, 'quality_score')
                    anatomy_score = get_score_based_on_profile(profile, 'anatomy_score')
                    is_over_illuminated = random.random() < profile['over_illuminated']
                    
                    # Prepare image data
                    image_data = {
                        'patient_id': patient_id,
                        'eye_side': eye_side,
                        'quality_score': quality_score,
                        'anatomy_score': anatomy_score,
                        'site_id': site.id,
                        'over_illuminated': is_over_illuminated,
                        'acquisition_date': datetime.now() - timedelta(days=random.randint(0, 365))
                    }
                    
                    # Create image file object
                    from werkzeug.datastructures import FileStorage
                    with open(file_path, 'rb') as img_file:
                        file = FileStorage(
                            stream=img_file,
                            filename=f"generated_{patient_id}_{eye_side.value.lower()}_{random.randint(1000, 9999)}.jpg",
                            content_type='image/jpeg' if filename.lower().endswith(('.jpg', '.jpeg')) else 'image/png'
                        )
                        
                        # Create the image
                        image = image_service.create_image(image_data, file)
                        
                        # Log the details
                        logger.info(
                            f"Generated image for patient ID={patient_id}, "
                            f"Eye={eye_side.value}, "
                            f"Quality={quality_score.value}, "
                            f"Anatomy={anatomy_score.value}, "
                            f"Site={site.name}, "
                            f"Over-illuminated={is_over_illuminated}"
                        )
                        processed_count += 1
                        
                except Exception as e:
                    logger.error(f"Error generating image for patient {patient_id}: {str(e)}")
                    error_count += 1
    
    # Generate statistics for future dashboard
    generate_site_statistics(sites, patient_service, image_service)
    
    return processed_count, error_count

def generate_site_statistics(sites, patient_service, image_service):
    """Generate statistics about site quality for future dashboard use."""
    stats = {}
    
    for site in sites:
        site_id = site.id
        site_name = site.name
        
        # Get all patients with images from this site
        patients_with_images = db.session.query(Patient.id).distinct(). \
            join(Image, Patient.id == Image.patient_id). \
            filter(Image.site_id == site_id).all()
        
        patients_with_images = [p[0] for p in patients_with_images]
        total_patients = len(patients_with_images)
        
        # Count patients available for AI (those with high quality images for both eyes)
        patients_available_for_ai = 0
        
        for patient_id in patients_with_images:
            # Get all images for this patient at this site
            images = db.session.query(Image). \
                filter(Image.patient_id == patient_id, Image.site_id == site_id).all()
            
            # Check if patient has at least one good image for each eye
            left_eye_good = False
            right_eye_good = False
            
            for img in images:
                # Check if this image meets quality criteria
                is_good_quality = (
                    img.quality_score in [ImageQualityScore.HIGH, ImageQualityScore.ACCEPTABLE] and
                    img.anatomy_score in [AnatomyScore.GOOD, AnatomyScore.ACCEPTABLE] and
                    not img.over_illuminated
                )
                
                if is_good_quality:
                    if img.eye_side == EyeSide.LEFT:
                        left_eye_good = True
                    elif img.eye_side == EyeSide.RIGHT:
                        right_eye_good = True
            
            # Patient is available for AI if both eyes have good images
            if left_eye_good and right_eye_good:
                patients_available_for_ai += 1
        
        # Calculate availability percentage
        availability_percentage = (patients_available_for_ai / total_patients * 100) if total_patients > 0 else 0
        
        # Store stats
        stats[site_name] = {
            'total_patients': total_patients,
            'patients_available_for_ai': patients_available_for_ai,
            'availability_percentage': availability_percentage
        }
        
        logger.info(f"Site: {site_name} - Total patients: {total_patients}, Available for AI: {patients_available_for_ai} ({availability_percentage:.1f}%)")
    
    return stats

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
        site_service = SiteService()
        
        # Import patients
        logger.info(f"Starting patient import from {args.csv_file}")
        created, updated, errors = import_patients(args.csv_file, patient_service)
        logger.info(f"Patient import completed: {created} created, {updated} updated, {errors} errors")
        print(f"Patient import completed: {created} created, {updated} updated, {errors} errors")
        
        # Import images if folder provided
        if args.images_folder:
            logger.info(f"Starting image import from {args.images_folder}")
            
            if args.randomize:
                logger.info(f"Randomizing image metadata with {args.num_sites} sites")
                print(f"Randomizing image metadata with {args.num_sites} sites")
                
                # Import with randomization
                processed, errors = import_images_with_randomization(
                    args.images_folder,
                    patient_service,
                    image_service,
                    site_service,
                    num_patients=args.num_patients,
                    num_sites=args.num_sites,
                    max_images_per_patient=args.max_images_per_patient
                )
            else:
                logger.info("Not randomizing metadata (use --randomize for this feature)")
                print("Not randomizing metadata (use --randomize for this feature)")
                
                # Regular import without metadata
                processed, errors = 0, 0
                
            logger.info(f"Image import completed: {processed} processed, {errors} errors")
            print(f"Image import completed: {processed} processed, {errors} errors")
        else:
            logger.info("No images folder specified, skipping image import")
        
        logger.info("Import process completed")
        print("Import process completed")

if __name__ == "__main__":
    main()