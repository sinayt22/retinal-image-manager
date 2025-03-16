from sqlalchemy.sql import func
from app import db
from app.models.image import AnatomyScore, EyeSide, Image, ImageQualityScore
from app.models.patient import Patient
from app.models.site import Site


class StatisticsService:
    def get_sites_statistics(self):
        sites = Site.query.order_by(Site.name).all()
        site_stats = []

        for site in sites:
            patients_with_images = (
                db.session.query(Patient.id)
                .distinct()
                .join(Image, Patient.id == Image.patient_id)
                .filter(Image.site_id == site.id)
                .all()
            )

            patients_with_images = [p[0] for p in patients_with_images]
            total_patients = len(patients_with_images)

            patients_available = 0
            for patient_id in patients_with_images:
                if self._is_patient_available(patient_id, site.id):
                    patients_available += 1

            availability_percentage = (
                (patients_available / total_patients * 100) if total_patients > 0 else 0
            )

            site_stats.append(
                {
                    "id": site.id,
                    "name": site.name,
                    "location": site.location,
                    "total_patients": total_patients,
                    "available_for_ai": patients_available,
                    "availability_percentage": round(availability_percentage, 1),
                }
            )

        return site_stats

    def _is_patient_available(self, patient_id, site_id):
        good_quality = [ImageQualityScore.HIGH, ImageQualityScore.ACCEPTABLE]
        good_anatomy = [AnatomyScore.GOOD, AnatomyScore.ACCEPTABLE]

        left_eye_good = (
            db.session.query(Image)
            .filter(
                Image.patient_id == patient_id,
                Image.site_id == site_id,
                Image.eye_side == EyeSide.LEFT,
                Image.quality_score.in_(good_quality),
                Image.anatomy_score.in_(good_anatomy),
                Image.over_illuminated == False,
            )
            .first()
            is not None
        )

        right_eye_good = (
            db.session.query(Image)
            .filter(
                Image.patient_id == patient_id,
                Image.site_id == site_id,
                Image.eye_side == EyeSide.RIGHT,
                Image.quality_score.in_(good_quality),
                Image.anatomy_score.in_(good_anatomy),
                Image.over_illuminated == False,
            )
            .first()
            is not None
        )

        return left_eye_good and right_eye_good

    def get_image_quality_statistics(self):
        total_images = Image.query.count()

        # Quality score distribution
        quality_counts = (
            db.session.query(Image.quality_score, func.count(Image.id))
            .group_by(Image.quality_score)
            .all()
        )

        quality_stats = {"HIGH": 0, "ACCEPTABLE": 0, "LOW": 0, "UNRATED": 0}

        for quality, count in quality_counts:
            if quality:
                quality_stats[quality.value] = count
            else:
                quality_stats["UNRATED"] = count

        # Anatomy score distribution
        anatomy_counts = (
            db.session.query(Image.anatomy_score, func.count(Image.id))
            .group_by(Image.anatomy_score)
            .all()
        )

        anatomy_stats = {"GOOD": 0, "ACCEPTABLE": 0, "POOR": 0, "UNRATED": 0}

        for anatomy, count in anatomy_counts:
            if anatomy:
                anatomy_stats[anatomy.value] = count
            else:
                anatomy_stats["UNRATED"] = count

        # Over-illumination statistics
        illumination_counts = (
            db.session.query(Image.over_illuminated, func.count(Image.id))
            .group_by(Image.over_illuminated)
            .all()
        )

        illumination_stats = {"OVER_ILLUMINATED": 0, "NORMAL": 0}

        for illuminated, count in illumination_counts:
            if illuminated:
                illumination_stats["OVER_ILLUMINATED"] = count
            else:
                illumination_stats["NORMAL"] = count

        return {
            "total_images": total_images,
            "quality": quality_stats,
            "anatomy": anatomy_stats,
            "illumination": illumination_stats,
        }
