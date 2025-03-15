from datetime import datetime, timezone, date
from app import db
from enum import Enum
from dateutil.relativedelta import relativedelta

class Sex(Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"


class Patient(db.Model):
    __tablename__ = "patients"

    id = db.Column(db.Integer, primary_key=True)
    birth_date = db.Column(db.Date, nullable=False)
    sex = db.Column(db.Enum(Sex), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    modified_at = db.Column(
        db.DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )

    images = db.relationship(
        "Image", backref="patient", lazy=True, cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Patient {self.id}>"
    
    @property
    def age(self):
        """Calculate age based on birth_date"""
        if not self.birth_date:
            return None
        today = date.today()
        if self.birth_date > today:
            return 0
        return relativedelta(today, self.birth_date).years

    def to_dict(self):
        return {
            "id": self.id,
            "birth_date": self.birth_date.isoformat() if self.birth_date else None,
            "age": self.age,
            "sex": self.sex,
            "create_at": self.created_at.isoformat() if self.created_at else None,
            "modified_at": self.modified_at.isoformat() if self.modified_at else None,
        }