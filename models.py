from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    full_name = db.Column(db.String(120), nullable=True)
    role = db.Column(db.String(20), default='staff')  # admin, staff, doctor
    department = db.Column(db.String(50), nullable=True)

class Equipment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    serial_number = db.Column(db.String(50), unique=True, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='Available') # Available, Borrowed, Maintenance, Decommissioned
    location = db.Column(db.String(100), nullable=False)
    purchase_date = db.Column(db.Date, nullable=True)
    last_maintenance = db.Column(db.Date, nullable=True)

class BorrowRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=False)
    borrower_name = db.Column(db.String(100), nullable=False)
    borrower_id = db.Column(db.String(50), nullable=True)
    borrow_date = db.Column(db.DateTime, default=datetime.utcnow)
    expected_return = db.Column(db.DateTime, nullable=True)
    return_date = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='Active') # Active, Returned, Overdue
    
    equipment = db.relationship('Equipment', backref=db.backref('borrow_records', lazy=True))

class MaintenanceRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=False)
    issue_description = db.Column(db.Text, nullable=False)
    cost = db.Column(db.Float, default=0.0)
    reported_date = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_date = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='Pending') # Pending, In Progress, Resolved
    
    equipment = db.relationship('Equipment', backref=db.backref('maintenance_records', lazy=True))
