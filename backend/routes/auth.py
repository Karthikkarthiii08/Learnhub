from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from database import db
from models import User
import os

auth_bp = Blueprint('auth', __name__)

ADMIN_SECRET = os.environ.get('ADMIN_SECRET', 'admin123')

@auth_bp.route('/api/signup/student', methods=['POST'])
def signup_student():
    data = request.get_json()
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 400
    user = User(
        name=data['name'],
        email=data['email'],
        password=generate_password_hash(data['password']),
        role='student'
    )
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'Student registered'}), 201

@auth_bp.route('/api/signup/admin', methods=['POST'])
def signup_admin():
    data = request.get_json()
    if data.get('secret') != ADMIN_SECRET:
        return jsonify({'error': 'Invalid admin secret'}), 403
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 400
    user = User(
        name=data['name'],
        email=data['email'],
        password=generate_password_hash(data['password']),
        role='admin'
    )
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'Admin registered'}), 201

@auth_bp.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    if not user or not check_password_hash(user.password, data['password']):
        return jsonify({'error': 'Invalid credentials'}), 401
    token = create_access_token(
        identity=str(user.id),
        additional_claims={'role': user.role, 'name': user.name}
    )
    return jsonify({'token': token, 'role': user.role, 'name': user.name})

@auth_bp.route('/api/logout', methods=['POST'])
def logout():
    return jsonify({'message': 'Logged out'})
