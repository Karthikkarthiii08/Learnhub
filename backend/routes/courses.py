from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from database import db
from models import Course, Lesson, Enrollment, Progress
from datetime import datetime

courses_bp = Blueprint('courses', __name__)

def admin_required():
    claims = get_jwt()
    if claims.get('role') != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    return None

# ── COURSES ──

@courses_bp.route('/api/courses', methods=['GET'])
def get_courses():
    premium = request.args.get('premium')
    category = request.args.get('category')
    q = Course.query
    if premium == '1':
        q = q.filter_by(is_premium=True)
    elif premium == '0':
        q = q.filter_by(is_premium=False)
    if category:
        q = q.filter_by(category=category)
    courses = q.all()
    return jsonify([_course_dict(c) for c in courses])

@courses_bp.route('/api/course/<int:id>', methods=['GET'])
def get_course(id):
    c = Course.query.get_or_404(id)
    d = _course_dict(c)
    d['lessons'] = [_lesson_dict(l) for l in c.lessons]
    return jsonify(d)

@courses_bp.route('/api/course', methods=['POST'])
@jwt_required()
def create_course():
    err = admin_required()
    if err: return err
    data = request.get_json()
    course = Course(
        title=data['title'], description=data.get('description'),
        instructor=data.get('instructor'), thumbnail=data.get('thumbnail'),
        duration_weeks=data.get('duration_weeks', 4),
        rating=data.get('rating', 4.5),
        is_premium=data.get('is_premium', False),
        category=data.get('category', 'General'),
        level=data.get('level', 'Beginner')
    )
    db.session.add(course)
    db.session.commit()
    return jsonify({'message': 'Course created', 'id': course.id}), 201

@courses_bp.route('/api/course/<int:id>', methods=['PUT'])
@jwt_required()
def update_course(id):
    err = admin_required()
    if err: return err
    course = Course.query.get_or_404(id)
    data = request.get_json()
    for field in ['title', 'description', 'instructor', 'thumbnail', 'duration_weeks', 'rating', 'is_premium', 'category', 'level']:
        if field in data:
            setattr(course, field, data[field])
    db.session.commit()
    return jsonify({'message': 'Course updated'})

@courses_bp.route('/api/course/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_course(id):
    err = admin_required()
    if err: return err
    course = Course.query.get_or_404(id)
    db.session.delete(course)
    db.session.commit()
    return jsonify({'message': 'Course deleted'})

# ── LESSONS ──

@courses_bp.route('/api/course/<int:id>/lessons', methods=['GET'])
def get_lessons(id):
    lessons = Lesson.query.filter_by(course_id=id).order_by(Lesson.lesson_order).all()
    return jsonify([_lesson_dict(l) for l in lessons])

@courses_bp.route('/api/lesson', methods=['POST'])
@jwt_required()
def create_lesson():
    err = admin_required()
    if err: return err
    data = request.get_json()
    lesson = Lesson(
        course_id=data['course_id'], title=data['title'],
        video_url=data.get('video_url'), lesson_order=data.get('lesson_order', 1)
    )
    db.session.add(lesson)
    db.session.commit()
    return jsonify({'message': 'Lesson created', 'id': lesson.id}), 201

@courses_bp.route('/api/lesson/<int:id>', methods=['PUT'])
@jwt_required()
def update_lesson(id):
    err = admin_required()
    if err: return err
    lesson = Lesson.query.get_or_404(id)
    data = request.get_json()
    for field in ['title', 'video_url', 'lesson_order']:
        if field in data:
            setattr(lesson, field, data[field])
    db.session.commit()
    return jsonify({'message': 'Lesson updated'})

@courses_bp.route('/api/lesson/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_lesson(id):
    err = admin_required()
    if err: return err
    lesson = Lesson.query.get_or_404(id)
    db.session.delete(lesson)
    db.session.commit()
    return jsonify({'message': 'Lesson deleted'})

# ── ENROLLMENT ──

@courses_bp.route('/api/enroll', methods=['POST'])
@jwt_required()
def enroll():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    existing = Enrollment.query.filter_by(user_id=user_id, course_id=data['course_id']).first()
    if existing:
        return jsonify({'message': 'Already enrolled'})
    enrollment = Enrollment(user_id=user_id, course_id=data['course_id'])
    db.session.add(enrollment)
    db.session.commit()
    return jsonify({'message': 'Enrolled successfully'}), 201

@courses_bp.route('/api/my-courses', methods=['GET'])
@jwt_required()
def my_courses():
    user_id = int(get_jwt_identity())
    enrollments = Enrollment.query.filter_by(user_id=user_id).all()
    result = []
    for e in enrollments:
        c = Course.query.get(e.course_id)
        if not c: continue
        total = len(c.lessons)
        completed = _completed_count(user_id, c.id)
        pct = round(completed / total * 100) if total else 0
        d = _course_dict(c)
        d['completed'] = completed
        d['percent'] = pct
        result.append(d)
    return jsonify(result)

# ── PROGRESS ──

@courses_bp.route('/api/progress', methods=['POST'])
@jwt_required()
def save_progress():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    lesson_id = data['lesson_id']
    watch_percent = float(data.get('watch_percent', 0))

    lesson = Lesson.query.get_or_404(lesson_id)

    # Strict ordering check
    if lesson.lesson_order > 1:
        prev = Lesson.query.filter_by(course_id=lesson.course_id, lesson_order=lesson.lesson_order - 1).first()
        if prev:
            prev_prog = Progress.query.filter_by(user_id=user_id, lesson_id=prev.id, completed=True).first()
            if not prev_prog:
                return jsonify({'error': 'Complete previous lesson first'}), 400

    prog = Progress.query.filter_by(user_id=user_id, lesson_id=lesson_id).first()
    if not prog:
        prog = Progress(user_id=user_id, lesson_id=lesson_id)
        db.session.add(prog)

    prog.watch_percent = max(prog.watch_percent or 0.0, watch_percent)
    prog.last_watched_at = datetime.utcnow()

    # Auto-complete at 90%
    if watch_percent >= 90 and not prog.completed:
        prog.completed = True
        prog.completed_at = datetime.utcnow()

    db.session.commit()
    return jsonify({'message': 'Progress saved', 'completed': prog.completed, 'watch_percent': prog.watch_percent})

@courses_bp.route('/api/lesson/complete', methods=['POST'])
@jwt_required()
def complete_lesson():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    lesson_id = data['lesson_id']
    lesson = Lesson.query.get_or_404(lesson_id)

    if lesson.lesson_order > 1:
        prev = Lesson.query.filter_by(course_id=lesson.course_id, lesson_order=lesson.lesson_order - 1).first()
        if prev:
            prev_prog = Progress.query.filter_by(user_id=user_id, lesson_id=prev.id, completed=True).first()
            if not prev_prog:
                return jsonify({'error': 'Complete previous lesson first'}), 400

    prog = Progress.query.filter_by(user_id=user_id, lesson_id=lesson_id).first()
    if not prog:
        prog = Progress(user_id=user_id, lesson_id=lesson_id)
        db.session.add(prog)
    if not prog.completed:
        prog.completed = True
        prog.watch_percent = 100
        prog.completed_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'message': 'Lesson marked complete'})

@courses_bp.route('/api/course-progress/<int:course_id>', methods=['GET'])
@jwt_required()
def course_progress(course_id):
    user_id = int(get_jwt_identity())
    lessons = Lesson.query.filter_by(course_id=course_id).order_by(Lesson.lesson_order).all()
    total = len(lessons)
    if total == 0:
        return jsonify({'percent': 0, 'completed': 0, 'total': 0, 'lessons': []})

    lesson_progress = []
    for l in lessons:
        p = Progress.query.filter_by(user_id=user_id, lesson_id=l.id).first()
        lesson_progress.append({
            'lesson_id': l.id,
            'completed': bool(p.completed) if p else False,
            'watch_percent': float(p.watch_percent) if p else 0.0,
            'last_watched_at': str(p.last_watched_at) if p and p.last_watched_at else None
        })

    completed = sum(1 for lp in lesson_progress if lp['completed'])
    return jsonify({
        'percent': round(completed / total * 100),
        'completed': completed,
        'total': total,
        'lessons': lesson_progress
    })

@courses_bp.route('/api/course/<int:id>/lessons-with-progress', methods=['GET'])
@jwt_required()
def lessons_with_progress(id):
    user_id = int(get_jwt_identity())
    lessons = Lesson.query.filter_by(course_id=id).order_by(Lesson.lesson_order).all()
    result = []
    for l in lessons:
        p = Progress.query.filter_by(user_id=user_id, lesson_id=l.id).first()
        result.append({
            'id': l.id,
            'course_id': l.course_id,
            'title': l.title,
            'video_url': l.video_url or '',
            'lesson_order': l.lesson_order,
            'completed': bool(p.completed) if p else False,
            'watch_percent': float(p.watch_percent) if p else 0.0,
        })
    return jsonify(result)

@courses_bp.route('/api/students', methods=['GET'])
@jwt_required()
def get_students():
    err = admin_required()
    if err: return err
    from models import User
    students = User.query.filter_by(role='student').all()
    return jsonify([{'id': s.id, 'name': s.name, 'email': s.email, 'created_at': str(s.created_at)} for s in students])

# ── HELPERS ──

def _course_dict(c):
    return {
        'id': c.id, 'title': c.title, 'description': c.description,
        'instructor': c.instructor, 'thumbnail': c.thumbnail,
        'duration_weeks': c.duration_weeks, 'rating': c.rating,
        'is_premium': c.is_premium, 'lesson_count': len(c.lessons),
        'category': c.category or 'General', 'level': c.level or 'Beginner'
    }

def _lesson_dict(l):
    return {
        'id': l.id, 'course_id': l.course_id, 'title': l.title,
        'video_url': l.video_url, 'lesson_order': l.lesson_order
    }

def _completed_count(user_id, course_id):
    lessons = Lesson.query.filter_by(course_id=course_id).all()
    ids = [l.id for l in lessons]
    return Progress.query.filter(
        Progress.user_id == user_id,
        Progress.lesson_id.in_(ids),
        Progress.completed == True
    ).count()
