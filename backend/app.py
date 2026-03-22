import os
from flask import Flask, send_from_directory
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from database import db
from routes.auth import auth_bp
from routes.courses import courses_bp
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'database', 'lms.db')

# Vercel Postgres gives postgres:// but SQLAlchemy needs postgresql://
raw_db_url = os.environ.get('DATABASE_URL', f'sqlite:///{DB_PATH}')
if raw_db_url.startswith('postgres://'):
    raw_db_url = raw_db_url.replace('postgres://', 'postgresql://', 1)

app = Flask(__name__, static_folder='../static', template_folder='../frontend')
app.config['SQLALCHEMY_DATABASE_URI'] = raw_db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET', 'super-secret-key')

CORS(app)
db.init_app(app)
JWTManager(app)

app.register_blueprint(auth_bp)
app.register_blueprint(courses_bp)

# Auto-create tables + seed if empty (works on Vercel Postgres)
with app.app_context():
    db.create_all()
    from models import Course, Lesson
    if Course.query.count() == 0:
        from routes.courses import seed_db
        from flask import request as flask_request
        import json
        with app.test_request_context(
            '/api/seed', method='POST',
            data=json.dumps({'secret': os.environ.get('ADMIN_SECRET', 'admin123')}),
            content_type='application/json'
        ):
            seed_db()

# Serve frontend pages
@app.route('/')
def index():
    return send_from_directory('../frontend', 'index.html')

@app.route('/<path:filename>')
def frontend(filename):
    return send_from_directory('../frontend', filename)

if __name__ == '__main__':
    with app.app_context():
        os.makedirs(os.path.join(BASE_DIR, 'database'), exist_ok=True)
        db.create_all()
    app.run(debug=True)
