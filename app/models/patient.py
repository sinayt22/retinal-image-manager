from datetime import datetime, timezone
from app import db
from enum import Enum

class Sex(Enum):
    MALE = 'Male'
    FEMALE = 'Female'
    OTHER = 'Other'

class Patient(db.Model):
    __tablename__ = 'patients'

    id = db.Column(db.Integer, primary_key=True)
    age = db.Column(db.Integer, nullable=False)
    sex = db.Column(db.Enum(Sex), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    modified_at = db.Column(db.DateTime, default=datetime.now(timezone.utc),
                            onupdate=datetime.now(timezone.utc))
    
    images = db.relationship('Image', backref='patient', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Patient {self.id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'age': self.age,
            'sex': self.sex,
            'create_at': self.created_at.isoformat() if self.created_at else None,
            'modified_at': self.created_at.isoformat() if self.modified_at else None
        }
    