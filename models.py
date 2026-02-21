from extensions import db
from datetime import datetime


# Job Model (represents a table in the database)
class Job(db.Model):
    
    # Primary Key (unique identifier)
    id = db.Column(db.Integer, primary_key=True)
    
    # Company name (required)
    company_name = db.Column(db.String(100), nullable=False)
    
    # Job role/title (required)
    role = db.Column(db.String(100), nullable=False)
    
    # Application status (default = Applied)
    status = db.Column(db.String(50), default="Applied")
    
    # Date applied (auto set to current time)
    date_applied = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Optional notes
    notes = db.Column(db.Text, nullable=True)

    # Convert object to dictionary (useful for JSON response)
    def to_dict(self):
     return {
        "id": self.id,
        "company_name": self.company_name,
        "role": self.role,
        "status": self.status,
        "date_applied": self.date_applied.isoformat() if self.date_applied else None,
        "notes": self.notes
     }

