from app import db
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String


class Site(db.Model):
    __tablename__ = "sites"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    location = Column(String(255), nullable=True)
    created_at = Column(db.DateTime, default=datetime.now(timezone.utc))
    modified_at = Column(db.DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )

    images = db.relationship("Image", backref="site_data", lazy=True)

    def __repr__(self):
        return f"<Site {self.id}: {self.name}>"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "location": self.location,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "modified_at": self.modified_at.isoformat() if self.modified_at else None,
        }
