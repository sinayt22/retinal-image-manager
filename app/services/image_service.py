from datetime import datetime, timezone
import os
import shutil

from flask import current_app
from app import db
from app.models.image import Image
from app.services.site_service import SiteService
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage


class ImageService:
    def __init__(self):
        self.site_service = SiteService()

    def get_patient_images(self, patient_id):
        return (
            Image.query.filter_by(patient_id=patient_id)
            .order_by(Image.acquisition_date.desc())
            .all()
        )

    def get_image_by_id(self, image_id):
        return Image.query.get(image_id)

    def create_image(self, image_data, image_file=None):
        """
        Create a new image record and save the uploaded file

        Args:
            image_data (dict): Dictionary containing image metadata
            image_file (FileStorage, optional): The uploaded image file

        Returns:
            Image: The created image
        """
        # Handle file upload if provided
        image_path = None
        is_io = image_data.get("over_illuminated")

        if image_file:
            filename = secure_filename(image_file.filename)
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            unique_filename = f"{timestamp}_{filename}"

            # Save to upload folder
            upload_folder = current_app.config["UPLOAD_FOLDER"]
            file_path = os.path.join(upload_folder, unique_filename)
            image_file.save(file_path)

            # Copy to static folder for web access
            static_folder = os.path.join(current_app.static_folder, "uploads/images")
            static_path = os.path.join(static_folder, unique_filename)
            shutil.copy2(file_path, static_path)

            image_path = unique_filename

        # Handle site - get or create by name
        site_id = None
        if "site_id" in image_data:
            site_id = image_data["site_id"]
        elif image_data.get("site_name"):
            site = self.site_service.find_or_create_site(
                name=image_data["site_name"], location=image_data.get("site_location")
            )
            site_id = site.id

        # Create image record
        image = Image(
            patient_id=image_data.get("patient_id"),
            eye_side=image_data.get("eye_side"),
            quality_score=image_data.get("quality_score"),
            anatomy_score=image_data.get("anatomy_score"),
            site_id=site_id,
            over_illuminated=is_io if is_io is not None else False,
            image_path=image_path or image_data.get("image_path"),
            acquisition_date=image_data.get(
                "acquisition_date", datetime.now(timezone.utc)
            ),
        )

        db.session.add(image)
        db.session.commit()
        return image

    def update_image(self, image_id, image_data):
        image = self.get_image_by_id(image_id)
        if not image:
            raise ValueError(f"Image with ID {image_id} not found")

        if "eye_side" in image_data:
            image.eye_side = image_data["eye_side"]
        if "quality_score" in image_data:
            image.quality_score = image_data["quality_score"]
        if "anatomy_score" in image_data:
            image.anatomy_score = image_data["anatomy_score"]

        # Handle site update
        if "site_id" in image_data:
            image.site_id = image_data["site_id"]
        elif "site_name" in image_data and image_data["site_name"]:
            site = self.site_service.find_or_create_site(
                name=image_data["site_name"], location=image_data.get("site_location")
            )
            image.site_id = site.id

        if "over_illuminated" in image_data:
            image.over_illuminated = image_data["over_illuminated"]
        if "acquisition_date" in image_data:
            image.acquisition_date = image_data["acquisition_date"]

        db.session.commit()
        return image

    def delete_image(self, image_id):
        image = self.get_image_by_id(image_id)
        if not image:
            raise ValueError(f"Image with ID {image_id} not found")

        # Remove from upload folder
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], image.image_path)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Remove from static folder
        static_path = os.path.join(current_app.static_folder, 'uploads/images', image.image_path)
        if os.path.exists(static_path):
            os.remove(static_path)

        db.session.delete(image)
        db.session.commit()
        return True


def is_over_illuminated(image_path, threshold=0.9):
    import numpy as np
    from PIL import Image

    PX_MAX_VALUE = 255.0
    # Load image
    img = Image.open(image_path)
    img_array = np.array(img)

    # Convert to luminance using perceptual weights
    # These weights reflect human perception of brightness
    luminance = (
        0.2126 * img_array[:, :, 0]
        + 0.7152 * img_array[:, :, 1]
        + 0.0722 * img_array[:, :, 2]
    ) / PX_MAX_VALUE

    # Identify pixels with luminance above threshold
    overexposed_mask = luminance > threshold

    # The image is over illuminated if it has pixels above the threshold
    return np.sum(overexposed_mask) > 0
