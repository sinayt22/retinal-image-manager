from datetime import datetime
import logging
from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.models.image import AnatomyScore, EyeSide, ImageQualityScore
from app.services.image_service import ImageService
from app.services.patient_service import PatientService
from app.services.site_service import SiteService


image_bp = Blueprint("images", __name__)

image_service = ImageService()
patient_service = PatientService()
site_service = SiteService()

logger = logging.getLogger(__name__)


@image_bp.route("/upload/<int:patient_id>", methods=["GET"])
def upload_form(patient_id):
    patient = patient_service.get_patient_by_id(patient_id)

    if not patient:
        logger.warning(
            f"Attempted to access upload form for non-existent patient with id={patient_id}"
        )
        flash("Patient with id {patient_id} not found", "error")
        return redirect(url_for("patients.index"))

    sites = site_service.get_all_sites()

    logger.debug(f"Displaying upload form for patient with id={patient_id}")
    return render_template("images/upload.html", patient=patient, sites=sites)


@image_bp.route("/upload/<int:patient_id>", methods=["POST"])
def upload(patient_id):
    patient = patient_service.get_patient_by_id(patient_id)
    if not patient:
        logger.warning(
            f"Attempted to upload an image for non-existent patient with id={patient_id}"
        )
        flash(f"Patient with id {patient_id} not found", "error")
        return redirect(url_for("patients.index"))

    eye_side = request.form.get("eye_side")
    quality_score = request.form.get("quality_score")
    anatomy_score = request.form.get("anatomy_score")
    site_id = request.form.get("site_id")
    site_name = request.form.get("site_name")  # For custom site entry
    site_location = request.form.get("site_location")  # For custom site location
    acquisition_date_str = request.form.get("acquisition_date")

    sites = site_service.get_all_sites()

    errors = validate_image_data(
        eye_side, quality_score, anatomy_score, acquisition_date_str
    )
    if errors:
        for error in errors:
            flash(error, "error")
        return render_template("images/upload.html", patient=patient, sites=sites), 400

    if "image_file" not in request.files:
        flash("No image was provided", "error")
        return render_template("images/upload.html", patient=patient, sites=sites), 400

    image_file = request.files["image_file"]
    if image_file.filename == "":
        flash("No image was provided", "error")
        return render_template("images/upload.html", patient=patient, sites=sites), 400
    
    acquisition_date = datetime.strptime(acquisition_date_str, "%Y-%m-%d") if acquisition_date_str else None

    image_data = {
        "patient_id": patient_id,
        "eye_side": EyeSide[eye_side] if eye_side else None,
        "quality_score": ImageQualityScore[quality_score] if quality_score else None,
        "anatomy_score": AnatomyScore[anatomy_score] if anatomy_score else None,
        "acquisition_date": acquisition_date,
    }

    # Handle site selection or creation
    if site_id and site_id != "custom":
        # Using existing site
        image_data["site_id"] = int(site_id)
    elif site_name:
        # Creating new site or using existing one by name
        image_data["site_name"] = site_name
        image_data["site_location"] = site_location

    try:
        image = image_service.create_image(image_data, image_file)
        logger.info(
            f"Image uploaded successfully for patient {patient_id}, image ID: {image.id}"
        )
        flash("Image uploaded successfully", "success")
        return redirect(url_for("patients.show", id=patient_id))

    except Exception as e:
        logger.error(
            f"Failed to upload image for patient {patient_id}: {str(e)}", exc_info=True
        )
        flash(f"Error uploading image: {str(e)}", "error")
        return render_template("images/upload.html", patient=patient, sites=sites), 500


@image_bp.route("/<int:image_id>", methods=["GET"])
def show(image_id):
    image = image_service.get_image_by_id(image_id)

    if not image:
        logger.warning(f"Attempted to access non-existent image with ID={image_id}")
        flash(f"Image with id {image_id} not found", "error")
        return redirect(url_for("patients.index"))

    patient = patient_service.get_patient_by_id(image.patient_id)
    if not patient:
        logger.warning(
            f"Image {image_id} references non-existent patient with id={image.patient_id}"
        )
        flash("Patient not found", "error")
        return redirect(url_for("patients.index"))

    logger.debug(f"Showing image with id={image_id}")
    return render_template("images/show.html", image=image, patient=patient)


@image_bp.route("/<int:image_id>/edit", methods=['GET'])
def edit(image_id):
    image = image_service.get_image_by_id(image_id)
    if not image:
        logger.warning(f"Attempted to access non-existent image with ID={image_id}")
        flash(f"Image with id {image_id} not found", "error")
        return redirect(url_for("patients.index"))

    patient = patient_service.get_patient_by_id(image.patient_id)
    if not patient:
        logger.warning(
            f"Image {image_id} references non-existent patient with id={image.patient_id}"
        )
        flash("Patient not found", "error")
        return redirect(url_for("patients.index"))

    sites = site_service.get_all_sites()

    logger.debug(f"Editing image with id={image_id}")
    return render_template("images/edit.html", image=image, patient=patient, sites=sites)


@image_bp.route("/<int:image_id>/update", methods=["POST"])
def update(image_id):
    image = image_service.get_image_by_id(image_id)

    if not image:
        logger.warning(f"Attempted to update non-existent image with id={image_id}")
        flash(f"Image with id {image_id} not found", "error")
        return redirect(url_for("patients.index"))

    # Get form data
    eye_side = request.form.get("eye_side")
    quality_score = request.form.get("quality_score")
    anatomy_score = request.form.get("anatomy_score")
    site_id = request.form.get("site_id")
    site_name = request.form.get("site_name")
    site_location = request.form.get("site_location")
    acquisition_date_str = request.form.get("acquisition_date")

    # Get all sites for re-rendering if needed
    sites = site_service.get_all_sites()
    patient = patient_service.get_patient_by_id(image.patient_id)

    # Validate form data
    errors = validate_image_data(
        eye_side, quality_score, anatomy_score, acquisition_date_str
    )
    if errors:
        for error in errors:
            flash(error, "error")
        return redirect(url_for("images.edit", patient=patient, sites=sites, image_id=image_id)), 400

    acquisition_date = datetime.strptime(acquisition_date_str, "%Y-%m-%d") if acquisition_date_str else None

    # Prepare image data
    image_data = {
        "eye_side": EyeSide[eye_side] if eye_side else None,
        "quality_score": ImageQualityScore[quality_score] if quality_score else None,
        "anatomy_score": AnatomyScore[anatomy_score] if anatomy_score else None,
        "acquisition_date": acquisition_date,
    }

    # Handle site selection or creation
    if site_id and site_id != "custom":
        # Using existing site
        image_data["site_id"] = int(site_id)
    elif site_name:
        # Creating new site or using existing one by name
        image_data["site_name"] = site_name
        image_data["site_location"] = site_location

    try:
        # Update image
        image = image_service.update_image(image_id, image_data)
        logger.info(f"Image {image_id} updated successfully")
        flash("Image updated successfully", "success")
        return redirect(url_for("images.show", image_id=image_id))
    except Exception as e:
        logger.error(f"Failed to update image {image_id}: {str(e)}", exc_info=True)
        flash(f"Error updating image: {str(e)}", "error")
        return redirect(url_for("images.edit", image_id=image_id, patient=patient, sites=sites)), 500


@image_bp.route("/<int:image_id>/delete", methods=["POST"])
def delete(image_id):
    """Delete an image."""
    image = image_service.get_image_by_id(image_id)
    if not image:
        logger.warning(f"Attempted to delete non-existent image with id={image_id}")
        flash(f"Image with id {image_id} not found", "error")
        return redirect(url_for("patients.index"))

    patient_id = image.patient_id

    try:
        image_service.delete_image(image_id)
        logger.info(f"Image {image_id} deleted successfully")
        flash("Image deleted successfully", "success")
        return redirect(url_for("patients.show", id=patient_id))
    except Exception as e:
        logger.error(f"Failed to delete image {image_id}: {str(e)}", exc_info=True)
        flash(f"Error deleting image: {str(e)}", "error")
        return redirect(url_for("images.show", image_id=image_id))


def validate_image_data(eye_side, quality_score, anatomy_score, acquisition_date):
    """Validate image form data."""
    errors = []

    if not eye_side:
        errors.append("Eye side is required")
    elif eye_side not in [side.name for side in EyeSide]:
        errors.append(
            f"Eye side must be one of: {', '.join([side.name for side in EyeSide])}"
        )

    if quality_score and quality_score not in [
        score.name for score in ImageQualityScore
    ]:
        errors.append(
            f"Quality score must be one of: {', '.join([score.name for score in ImageQualityScore])}"
        )

    if anatomy_score and anatomy_score not in [score.name for score in AnatomyScore]:
        errors.append(
            f"Anatomy score must be one of: {', '.join([score.name for score in AnatomyScore])}"
        )

    if acquisition_date:
        try:
            acquisition_date_parsed = datetime.strptime(acquisition_date, "%Y-%m-%d")
            # Check if the date is not in the future
            if acquisition_date_parsed.date() > datetime.now().date():
                errors.append("Acquisition date cannot be in the future")
        except ValueError:
            errors.append("Acquisition date must be in YYYY-MM-DD format")

    return errors
