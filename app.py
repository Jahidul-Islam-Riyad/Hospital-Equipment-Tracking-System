import os
import random
from flask import Flask, render_template, request, jsonify, redirect, url_for, make_response, flash
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, set_access_cookies, unset_jwt_cookies, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Equipment, BorrowRecord, MaintenanceRecord
from datetime import timedelta, datetime, date

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'super-secret-ict503-enhanced'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hospital_system_pro.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# JWT Configuration
app.config['JWT_SECRET_KEY'] = 'jwt-enhanced-secret'
app.config['JWT_TOKEN_LOCATION'] = ['cookies']
app.config['JWT_COOKIE_CSRF_PROTECT'] = False
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=8)

db.init_app(app)
jwt = JWTManager(app)

def seed_database():
    if User.query.first():
        return # Already seeded
        
    # Users
    users = [
        User(username='admin', password_hash=generate_password_hash('admin123'), full_name='System Administrator', role='admin', department='IT'),
        User(username='doctor_sarah', password_hash=generate_password_hash('pass123'), full_name='Dr. Sarah Jenkins', role='doctor', department='Cardiology'),
        User(username='nurse_john', password_hash=generate_password_hash('pass123'), full_name='John Smith', role='staff', department='Emergency')
    ]
    db.session.add_all(users)
    
    # Equipment
    equipments = [
        Equipment(name='MRI Scanner T-3000', serial_number='MRI-10023', category='Imaging', status='Available', location='Radiology Room A', purchase_date=date(2022, 5, 10), last_maintenance=date(2023, 8, 15)),
        Equipment(name='CT Scanner Pro', serial_number='CTS-9921', category='Imaging', status='Maintenance', location='Radiology Room B', purchase_date=date(2021, 3, 22), last_maintenance=date(2023, 9, 10)),
        Equipment(name='Portable Ventilator V1', serial_number='VEN-101', category='Life Support', status='Available', location='ICU Ward 1', purchase_date=date(2023, 1, 15)),
        Equipment(name='Portable Ventilator V2', serial_number='VEN-102', category='Life Support', status='Borrowed', location='ER Ward', purchase_date=date(2023, 1, 15)),
        Equipment(name='Defibrillator X', serial_number='DEF-301', category='Emergency', status='Available', location='ER Trauma 1', purchase_date=date(2020, 11, 5), last_maintenance=date(2023, 1, 20)),
        Equipment(name='Defibrillator Y', serial_number='DEF-302', category='Emergency', status='Available', location='ER Trauma 2', purchase_date=date(2020, 11, 5)),
        Equipment(name='Surgical Microscope', serial_number='MIC-776', category='Surgical', status='Available', location='OR 3', purchase_date=date(2019, 4, 18), last_maintenance=date(2022, 12, 12)),
        Equipment(name='Anesthesia Machine', serial_number='ANE-445', category='Surgical', status='Maintenance', location='OR 1', purchase_date=date(2021, 7, 30)),
        Equipment(name='ECG Monitor', serial_number='ECG-882', category='Monitoring', status='Borrowed', location='Cardiology Ward', purchase_date=date(2022, 9, 9)),
        Equipment(name='Ultrasound Machine', serial_number='ULT-554', category='Imaging', status='Available', location='Maternity Ward', purchase_date=date(2023, 3, 2)),
        Equipment(name='Infusion Pump A', serial_number='INF-112', category='General', status='Available', location='ICU Ward 2', purchase_date=date(2022, 2, 14)),
        Equipment(name='Infusion Pump B', serial_number='INF-113', category='General', status='Available', location='ICU Ward 2', purchase_date=date(2022, 2, 14)),
        Equipment(name='Dialysis Machine', serial_number='DIA-221', category='Life Support', status='Available', location='Dialysis Unit 1', purchase_date=date(2023, 5, 20)),
        Equipment(name='Surgical Operating Light', serial_number='SOL-099', category='Surgical', status='Available', location='OR 2', purchase_date=date(2020, 8, 12)),
        Equipment(name='Autoclave Sterilizer', serial_number='AUT-343', category='General', status='Maintenance', location='CSSD Room', purchase_date=date(2018, 1, 15)),
        Equipment(name='Infant Incubator', serial_number='INC-881', category='Life Support', status='Borrowed', location='NICU', purchase_date=date(2023, 6, 10)),
        Equipment(name='Endoscopy Tower', serial_number='END-902', category='Imaging', status='Available', location='Gastroenterology', purchase_date=date(2021, 10, 5)),
        Equipment(name='Blood Gas Analyzer', serial_number='BGA-111', category='Monitoring', status='Available', location='Core Lab', purchase_date=date(2022, 11, 20))
    ]
    db.session.add_all(equipments)
    db.session.commit()
    
    # Borrow Records
    br1 = BorrowRecord(equipment_id=4, borrower_name='Nurse John', borrower_id='STF-001', borrow_date=datetime.utcnow() - timedelta(days=2), expected_return=datetime.utcnow() + timedelta(days=1), status='Active')
    br2 = BorrowRecord(equipment_id=9, borrower_name='Dr. Sarah Jenkins', borrower_id='DOC-002', borrow_date=datetime.utcnow() - timedelta(hours=5), expected_return=datetime.utcnow() + timedelta(hours=12), status='Active')
    br3 = BorrowRecord(equipment_id=10, borrower_name='Dr. Smith', borrower_id='DOC-005', borrow_date=datetime.utcnow() - timedelta(days=5), return_date=datetime.utcnow() - timedelta(days=4), status='Returned')
    
    db.session.add_all([br1, br2, br3])
    
    # Maintenance Records
    mr1 = MaintenanceRecord(equipment_id=2, issue_description='Scanner calibration failing', reported_date=datetime.utcnow() - timedelta(days=3), status='In Progress')
    mr2 = MaintenanceRecord(equipment_id=8, issue_description='Valve pressure leak', reported_date=datetime.utcnow() - timedelta(days=1), status='Pending')
    mr3 = MaintenanceRecord(equipment_id=5, issue_description='Battery replacement', reported_date=datetime.utcnow() - timedelta(days=30), resolved_date=datetime.utcnow() - timedelta(days=28), status='Resolved', cost=150.00)
    
    db.session.add_all([mr1, mr2, mr3])
    db.session.commit()

with app.app_context():
    db.create_all()
    seed_database()

@jwt.unauthorized_loader
def unauthorized_callback(callback):
    return redirect(url_for('login'))

@jwt.invalid_token_loader
def invalid_token_callback(callback):
    resp = make_response(redirect(url_for('login')))
    unset_jwt_cookies(resp)
    return resp

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    resp = make_response(redirect(url_for('login')))
    unset_jwt_cookies(resp)
    return resp

@app.context_processor
def inject_user():
    try:
        current_user = get_jwt_identity()
        user = User.query.filter_by(username=current_user).first()
        return dict(current_user=user)
    except:
        return dict(current_user=None)

@app.route('/')
def index():
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            access_token = create_access_token(identity=user.username)
            resp = make_response(redirect(url_for('dashboard')))
            set_access_cookies(resp, access_token)
            return resp
        else:
            return render_template('login.html', error='Invalid credentials. Try admin / admin123')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    resp = make_response(redirect(url_for('login')))
    unset_jwt_cookies(resp)
    return resp

@app.route('/dashboard')
@jwt_required()
def dashboard():
    stats = {
        'total': Equipment.query.count(),
        'available': Equipment.query.filter_by(status='Available').count(),
        'borrowed': Equipment.query.filter_by(status='Borrowed').count(),
        'maintenance': Equipment.query.filter_by(status='Maintenance').count()
    }
    recent_borrows = BorrowRecord.query.order_by(BorrowRecord.borrow_date.desc()).limit(6).all()
    recent_maintenance = MaintenanceRecord.query.filter(MaintenanceRecord.status != 'Resolved').order_by(MaintenanceRecord.reported_date.desc()).limit(4).all()
    
    return render_template('dashboard.html', stats=stats, recent_borrows=recent_borrows, recent_maintenance=recent_maintenance)

@app.route('/equipment', methods=['GET'])
@jwt_required()
def equipment_list():
    query = request.args.get('q', '')
    status_filter = request.args.get('status', 'All')
    
    eq_query = Equipment.query
    if query:
        eq_query = eq_query.filter(Equipment.name.ilike(f'%{query}%') | Equipment.serial_number.ilike(f'%{query}%'))
    if status_filter != 'All':
        eq_query = eq_query.filter_by(status=status_filter)
        
    equipments = eq_query.all()
    return render_template('equipment.html', equipments=equipments, query=query, status_filter=status_filter)

@app.route('/equipment/add', methods=['POST'])
@jwt_required()
def add_equipment():
    name = (request.form.get('name') or '').strip()
    serial = (request.form.get('serial_number') or '').strip()
    category = (request.form.get('category') or '').strip() or 'General'
    location = (request.form.get('location') or '').strip() or 'Unassigned'
    
    if not name or not serial:
        return redirect(url_for('equipment_list'))
    
    try:
        new_eq = Equipment(name=name, serial_number=serial, category=category, location=location, purchase_date=datetime.utcnow().date())
        db.session.add(new_eq)
        db.session.commit()
    except Exception:
        db.session.rollback()
    return redirect(url_for('equipment_list'))

@app.route('/borrow', methods=['GET', 'POST'])
@jwt_required()
def borrow_equipment():
    if request.method == 'POST':
        eq_id = request.form.get('equipment_id')
        borrower = request.form.get('borrower_name')
        b_id = request.form.get('borrower_id')
        try:
            days = int(request.form.get('days', 1))
        except (ValueError, TypeError):
            days = 1
        if days < 1:
            days = 1
        
        eq = Equipment.query.get(eq_id)
        if eq and eq.status == 'Available':
            eq.status = 'Borrowed'
            record = BorrowRecord(equipment_id=eq.id, borrower_name=borrower, borrower_id=b_id, expected_return=datetime.utcnow() + timedelta(days=days))
            db.session.add(record)
            db.session.commit()
            return redirect(url_for('borrow_equipment'))
            
    active_records = BorrowRecord.query.filter_by(status='Active').order_by(BorrowRecord.borrow_date.desc()).all()
    available_eq = Equipment.query.filter_by(status='Available').all()
    return render_template('borrow.html', records=active_records, available=available_eq)

@app.route('/return/<int:record_id>', methods=['POST'])
@jwt_required()
def return_equipment(record_id):
    record = BorrowRecord.query.get(record_id)
    if record and record.status == 'Active':
        record.status = 'Returned'
        record.return_date = datetime.utcnow()
        record.equipment.status = 'Available'
        db.session.commit()
    return redirect(url_for('borrow_equipment'))

@app.route('/reports')
@jwt_required()
def reports():
    # Category Distribution
    categories = db.session.query(Equipment.category, db.func.count(Equipment.id)).group_by(Equipment.category).all()
    cat_labels = [c[0] for c in categories]
    cat_data = [c[1] for c in categories]
    
    # Status Distribution
    statuses = db.session.query(Equipment.status, db.func.count(Equipment.id)).group_by(Equipment.status).all()
    stat_labels = [s[0] for s in statuses]
    stat_data = [s[1] for s in statuses]
    
    return render_template('reports.html', cat_labels=cat_labels, cat_data=cat_data, stat_labels=stat_labels, stat_data=stat_data)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
