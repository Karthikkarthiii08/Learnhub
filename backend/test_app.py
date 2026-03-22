"""
Run: python backend/test_app.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

# Prevent .env from polluting test config
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['JWT_SECRET'] = 'test-secret-key-32-bytes-long-ok!!'
os.environ['ADMIN_SECRET'] = 'admin123'

from flask import Flask
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from database import db
from routes.auth import auth_bp
from routes.courses import courses_bp

def create_test_app():
    app = Flask(__name__, static_folder='../static', template_folder='../frontend')
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = 'test-secret-key-32-bytes-long-ok!!'
    CORS(app)
    db.init_app(app)
    JWTManager(app)
    app.register_blueprint(auth_bp)
    app.register_blueprint(courses_bp)
    return app

passed = 0
failed = 0

def check(label, condition, got):
    global passed, failed
    if condition:
        print(f'  PASS  {label}')
        passed += 1
    else:
        print(f'  FAIL  {label} => {got}')
        failed += 1

app = create_test_app()

with app.app_context():
    db.create_all()
    client = app.test_client()

    # Auth tests
    r = client.post('/api/signup/student', json={'name': 'Alice', 'email': 'alice@test.com', 'password': 'pass123'})
    check('T01 student signup 201', r.status_code == 201, r.get_json())

    r = client.post('/api/signup/student', json={'name': 'Alice', 'email': 'alice@test.com', 'password': 'pass123'})
    check('T02 duplicate email 400', r.status_code == 400, r.get_json())

    r = client.post('/api/login', json={'email': 'alice@test.com', 'password': 'pass123'})
    check('T03 login 200 with token', r.status_code == 200 and 'token' in r.get_json(), r.get_json())
    token = r.get_json().get('token')
    headers = {'Authorization': f'Bearer {token}'}

    r = client.post('/api/login', json={'email': 'alice@test.com', 'password': 'wrong'})
    check('T04 wrong password 401', r.status_code == 401, r.get_json())

    r = client.post('/api/signup/admin', json={'name': 'Admin', 'email': 'admin@test.com', 'password': 'adminpass', 'secret': 'wrongsecret'})
    check('T05 admin wrong secret 403', r.status_code == 403, r.get_json())

    r = client.post('/api/signup/admin', json={'name': 'Admin', 'email': 'admin@test.com', 'password': 'adminpass', 'secret': 'admin123'})
    check('T06 admin signup 201', r.status_code == 201, r.get_json())

    r = client.post('/api/logout')
    check('T07 logout 200', r.status_code == 200, r.get_json())

    # Course tests
    r = client.get('/api/courses')
    check('T08 get courses 200', r.status_code == 200 and isinstance(r.get_json(), list), r.get_json())

    r = client.post('/api/course', json={'title': 'Hacked'}, headers=headers)
    check('T09 student cannot create course 403', r.status_code == 403, r.get_json())

    r = client.post('/api/login', json={'email': 'admin@test.com', 'password': 'adminpass'})
    admin_token = r.get_json().get('token')
    admin_h = {'Authorization': f'Bearer {admin_token}'}

    r = client.post('/api/course', json={'title': 'Python 101', 'description': 'Intro', 'instructor': 'John'}, headers=admin_h)
    check('T10 admin create course 201', r.status_code == 201, r.get_json())
    course_id = r.get_json().get('id')

    r = client.get(f'/api/course/{course_id}')
    check('T11 get course by id 200', r.status_code == 200 and r.get_json()['title'] == 'Python 101', r.get_json())

    r = client.get('/api/course/9999')
    check('T12 get nonexistent course 404', r.status_code == 404, r.status_code)

    r = client.put(f'/api/course/{course_id}', json={'title': 'Python 102'}, headers=admin_h)
    check('T13 update course 200', r.status_code == 200, r.get_json())

    r = client.get(f'/api/course/{course_id}')
    check('T14 course title updated', r.get_json()['title'] == 'Python 102', r.get_json())

    # Lesson tests
    r = client.post('/api/lesson', json={'course_id': course_id, 'title': 'Lesson 1', 'video_url': 'https://yt.com/1', 'lesson_order': 1}, headers=admin_h)
    check('T15 create lesson 201', r.status_code == 201, r.get_json())
    lesson1_id = r.get_json().get('id')

    r = client.post('/api/lesson', json={'course_id': course_id, 'title': 'Lesson 2', 'video_url': 'https://yt.com/2', 'lesson_order': 2}, headers=admin_h)
    check('T16 create lesson 2 201', r.status_code == 201, r.get_json())
    lesson2_id = r.get_json().get('id')

    r = client.get(f'/api/course/{course_id}/lessons')
    check('T17 get lessons for course', r.status_code == 200 and len(r.get_json()) == 2, r.get_json())

    r = client.put(f'/api/lesson/{lesson1_id}', json={'title': 'Lesson 1 Updated'}, headers=admin_h)
    check('T18 update lesson 200', r.status_code == 200, r.get_json())

    # Enrollment tests
    r = client.post('/api/enroll', json={'course_id': course_id}, headers=headers)
    check('T19 enroll student 201', r.status_code == 201, r.get_json())

    r = client.post('/api/enroll', json={'course_id': course_id}, headers=headers)
    check('T20 duplicate enroll 200', r.status_code == 200, r.get_json())

    r = client.get('/api/my-courses', headers=headers)
    check('T21 my courses returns 1', r.status_code == 200 and len(r.get_json()) == 1, r.get_json())

    # Progress tests
    r = client.post('/api/progress', json={'lesson_id': lesson1_id, 'watch_percent': 50}, headers=headers)
    check('T22 progress 50pct not completed', r.status_code == 200 and r.get_json()['completed'] == False, r.get_json())

    r = client.post('/api/progress', json={'lesson_id': lesson1_id, 'watch_percent': 90}, headers=headers)
    check('T23 progress 90pct auto-complete', r.status_code == 200 and r.get_json()['completed'] == True, r.get_json())

    # Lesson 2 requires lesson 1 to be done first — should pass since lesson 1 is complete
    r = client.post('/api/progress', json={'lesson_id': lesson2_id, 'watch_percent': 50}, headers=headers)
    check('T24 lesson 2 progress after lesson 1 done', r.status_code == 200, r.get_json())

    r = client.post('/api/lesson/complete', json={'lesson_id': lesson2_id}, headers=headers)
    check('T25 complete lesson 2 200', r.status_code == 200, r.get_json())

    r = client.get(f'/api/course-progress/{course_id}', headers=headers)
    data = r.get_json()
    check('T26 course progress 100pct', r.status_code == 200 and data['percent'] == 100, data)

    r = client.get(f'/api/course/{course_id}/lessons-with-progress', headers=headers)
    data = r.get_json()
    check('T27 lessons-with-progress both completed', r.status_code == 200 and all(l['completed'] for l in data), data)

    # Ordering enforcement: new student tries lesson 2 without completing lesson 1
    r = client.post('/api/signup/student', json={'name': 'Bob', 'email': 'bob@test.com', 'password': 'pass'})
    r = client.post('/api/login', json={'email': 'bob@test.com', 'password': 'pass'})
    bob_h = {'Authorization': f'Bearer {r.get_json()["token"]}'}
    r = client.post('/api/progress', json={'lesson_id': lesson2_id, 'watch_percent': 50}, headers=bob_h)
    check('T28 ordering enforced - lesson 2 blocked 400', r.status_code == 400, r.get_json())

    # Admin tests
    r = client.get('/api/students', headers=admin_h)
    data = r.get_json()
    check('T29 admin get students', r.status_code == 200 and len(data) == 2, data)

    r = client.get('/api/students', headers=headers)
    check('T30 student cannot get students 403', r.status_code == 403, r.get_json())

    # Delete tests
    r = client.delete(f'/api/lesson/{lesson1_id}', headers=admin_h)
    check('T31 delete lesson 200', r.status_code == 200, r.get_json())

    r = client.delete(f'/api/course/{course_id}', headers=admin_h)
    check('T32 delete course 200', r.status_code == 200, r.get_json())

    r = client.get(f'/api/course/{course_id}')
    check('T33 deleted course returns 404', r.status_code == 404, r.status_code)

    print()
    print(f'Results: {passed} passed, {failed} failed out of {passed+failed} tests')
    if failed > 0:
        sys.exit(1)
