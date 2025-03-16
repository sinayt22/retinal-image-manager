import sqlalchemy
import enum
from datetime import datetime, timezone
from app import db
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean


class EyeSide(enum.Enum):
    LEFT = "LEFT"
    RIGHT = "RIGHT"


class ImageQualityScore(enum.Enum):
    LOW = "LOW"
    ACCEPTABLE = "ACCEPTABLE"
    HIGH = "HIGH"


class AnatomyScore(enum.Enum):
    POOR = "POOR"
    ACCEPTABLE = "ACCEPTABLE"
    GOOD = "GOOD"


class Image(db.Model):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    eye_side = Column(sqlalchemy.Enum(EyeSide), nullable=False)
    quality_score = Column(sqlalchemy.Enum(ImageQualityScore), nullable=True)
    anatomy_score = Column(sqlalchemy.Enum(AnatomyScore), nullable=True)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=True)
    over_illuminated = Column(Boolean, default=False)
    image_path = Column(String(255), nullable=False)
    acquisition_date = Column(
        sqlalchemy.DateTime, default=datetime.now(timezone.utc), nullable=True
    )
    created_at = Column(sqlalchemy.DateTime, default=datetime.now(timezone.utc))
    modified_at = Column(
        sqlalchemy.DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )

    def __repr__(self):
        return f"<image {self.id} - {self.eye_side}>"


    def to_dict(self):
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "eye_side": self.eye_side.value if self.eye_side else None,
            "quality_score": self.quality_score.value if self.quality_score else None,
            "anatomy_score": self.anatomy_score.value if self.anatomy_score else None,
            "site_id": self.site_id,
            "site_name": (
                self.site_data.name
                if hasattr(self, "site_data") and self.site_data
                else None
            ),
            "site_location": (
                self.site_data.location
                if hasattr(self, "site_data") and self.site_data
                else None
            ),
            "over_illumination": self.over_illuminated,
            "image_path": self.image_path,
            "acquisition_date": (
                self.acquisition_date.isoformat() if self.acquisition_date else None
            ),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.modified_at.isoformat() if self.modified_at else None,
        }
