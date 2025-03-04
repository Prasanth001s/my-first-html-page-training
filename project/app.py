from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import json
import qrcode
from io import BytesIO
import base64
from blockchain import Blockchain
from certificate import Certificate

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-for-development')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///certificates.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
blockchain = Blockchain()

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)  # In production, use proper password hashing
    role = db.Column(db.String(20), nullable=False)  # 'issuer', 'recipient', 'verifier'
    certificates = db.relationship('CertificateRecord', backref='owner', lazy=True)

class CertificateRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    certificate_id = db.Column(db.String(64), unique=True, nullable=False)
    recipient_name = db.Column(db.String(100), nullable=False)
    recipient_id = db.Column(db.String(100), nullable=False)
    issuer_name = db.Column(db.String(100), nullable=False)
    issue_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    course_name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    blockchain_hash = db.Column(db.String(64), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_valid = db.Column(db.Boolean, default=True)

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.password == password:  # In production, use proper password verification
            session['user_id'] = user.id
            session['role'] = user.role
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')
        
        existing_user = User.query.filter_by(username=username).first()
        
        if existing_user:
            flash('Username already exists', 'danger')
        else:
            new_user = User(username=username, password=password, role=role)
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('role', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please login first', 'warning')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    
    if user.role == 'issuer':
        certificates = CertificateRecord.query.filter_by(issuer_name=user.username).all()
        return render_template('issuer_dashboard.html', certificates=certificates)
    elif user.role == 'recipient':
        certificates = CertificateRecord.query.filter_by(user_id=user.id).all()
        return render_template('recipient_dashboard.html', certificates=certificates)
    else:  # verifier
        return render_template('verifier_dashboard.html')

@app.route('/create_certificate', methods=['GET', 'POST'])
def create_certificate():
    if 'user_id' not in session or session['role'] != 'issuer':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        recipient_username = request.form.get('recipient_username')
        recipient = User.query.filter_by(username=recipient_username).first()
        
        if not recipient:
            flash('Recipient not found', 'danger')
            return redirect(url_for('create_certificate'))
        
        issuer = User.query.get(session['user_id'])
        
        # Create certificate data
        certificate_data = {
            'recipient_name': recipient.username,
            'recipient_id': str(recipient.id),
            'issuer_name': issuer.username,
            'issue_date': datetime.utcnow().isoformat(),
            'course_name': request.form.get('course_name'),
            'description': request.form.get('description')
        }
        
        # Create certificate object
        certificate = Certificate(certificate_data)
        
        # Add to blockchain
        block_index = blockchain.add_certificate(certificate)
        
        # Save to database
        cert_record = CertificateRecord(
            certificate_id=certificate.certificate_id,
            recipient_name=certificate.recipient_name,
            recipient_id=certificate.recipient_id,
            issuer_name=certificate.issuer_name,
            issue_date=datetime.fromisoformat(certificate.issue_date),
            course_name=certificate.course_name,
            description=certificate.description,
            blockchain_hash=blockchain.chain[block_index]['hash'],
            user_id=recipient.id
        )
        
        db.session.add(cert_record)
        db.session.commit()
        
        flash('Certificate created successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('create_certificate.html')

@app.route('/view_certificate/<certificate_id>')
def view_certificate(certificate_id):
    if 'user_id' not in session:
        flash('Please login first', 'warning')
        return redirect(url_for('login'))
    
    certificate = CertificateRecord.query.filter_by(certificate_id=certificate_id).first()
    
    if not certificate:
        flash('Certificate not found', 'danger')
        return redirect(url_for('dashboard'))
    
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(f"{request.host_url}verify/{certificate.certificate_id}")
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered)
    qr_code = base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    return render_template('view_certificate.html', certificate=certificate, qr_code=qr_code)

@app.route('/verify/<certificate_id>')
def verify_certificate(certificate_id):
    certificate = CertificateRecord.query.filter_by(certificate_id=certificate_id).first()
    
    if not certificate:
        return render_template('verify_result.html', valid=False, message="Certificate not found")
    
    # Verify on blockchain
    is_valid = blockchain.verify_certificate(certificate_id, certificate.blockchain_hash)
    
    if is_valid and certificate.is_valid:
        return render_template('verify_result.html', valid=True, certificate=certificate)
    else:
        return render_template('verify_result.html', valid=False, message="Certificate validation failed")

@app.route('/verify', methods=['GET', 'POST'])
def verify():
    if request.method == 'POST':
        certificate_id = request.form.get('certificate_id')
        return redirect(url_for('verify_certificate', certificate_id=certificate_id))
    
    return render_template('verify.html')

@app.route('/revoke/<certificate_id>', methods=['POST'])
def revoke_certificate(certificate_id):
    if 'user_id' not in session or session['role'] != 'issuer':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('login'))
    
    certificate = CertificateRecord.query.filter_by(certificate_id=certificate_id).first()
    
    if not certificate:
        flash('Certificate not found', 'danger')
        return redirect(url_for('dashboard'))
    
    issuer = User.query.get(session['user_id'])
    
    if certificate.issuer_name != issuer.username:
        flash('You are not authorized to revoke this certificate', 'danger')
        return redirect(url_for('dashboard'))
    
    certificate.is_valid = False
    db.session.commit()
    
    flash('Certificate revoked successfully', 'success')
    return redirect(url_for('dashboard'))

@app.route('/api/certificates/<certificate_id>')
def api_get_certificate(certificate_id):
    certificate = CertificateRecord.query.filter_by(certificate_id=certificate_id).first()
    
    if not certificate:
        return jsonify({'error': 'Certificate not found'}), 404
    
    # Verify on blockchain
    is_valid = blockchain.verify_certificate(certificate_id, certificate.blockchain_hash)
    
    if is_valid and certificate.is_valid:
        return jsonify({
            'certificate_id': certificate.certificate_id,
            'recipient_name': certificate.recipient_name,
            'issuer_name': certificate.issuer_name,
            'issue_date': certificate.issue_date.isoformat(),
            'course_name': certificate.course_name,
            'description': certificate.description,
            'is_valid': True
        })
    else:
        return jsonify({
            'certificate_id': certificate.certificate_id,
            'is_valid': False
        })

@app.route('/share/<certificate_id>')
def share_certificate(certificate_id):
    certificate = CertificateRecord.query.filter_by(certificate_id=certificate_id).first()
    
    if not certificate:
        flash('Certificate not found', 'danger')
        return redirect(url_for('dashboard'))
    
    share_url = url_for('verify_certificate', certificate_id=certificate_id, _external=True)
    
    return render_template('share.html', certificate=certificate, share_url=share_url)

# Initialize database
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)