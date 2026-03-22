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

@courses_bp.route('/api/seed', methods=['POST'])
def seed_db():
    import os
    secret = request.get_json(silent=True) or {}
    if secret.get('secret') != os.environ.get('ADMIN_SECRET', 'admin123'):
        return jsonify({'error': 'Unauthorized'}), 403

    from models import Lesson as LessonModel
    LESSON_VIDS = ["kqtD5dpn9C8", "DZwmZ8Usvnk", "9Os0o3wzS_I", "JeznW_7DlB0"]
    LESSON_TITLES = ["Introduction & Overview", "Core Concepts", "Hands-on Practice", "Advanced Topics", "Project & Review"]

    def make_lessons(course_id, main_vid):
        vids = [main_vid] + LESSON_VIDS
        return [LessonModel(course_id=course_id, title=LESSON_TITLES[i],
                       video_url=f"https://www.youtube.com/watch?v={vids[i]}",
                       lesson_order=i+1) for i in range(5)]

    COURSES = [
      dict(title="Complete Python by Shradha Khapra", instructor="Shradha Khapra", thumbnail="https://img.youtube.com/vi/_uQrJ0TkZlc/maxresdefault.jpg", duration_weeks=12, rating=4.8, is_premium=False, category="Python", level="Beginner", description="Complete Python from scratch covering variables, loops, functions and OOP.", main_vid="_uQrJ0TkZlc"),
      dict(title="Python by Engineering in Kannada", instructor="Engineering in Kannada", thumbnail="https://img.youtube.com/vi/UrsmFxEIp5k/maxresdefault.jpg", duration_weeks=6, rating=4.6, is_premium=False, category="Python", level="Beginner", description="Python programming explained in Kannada for regional learners.", main_vid="UrsmFxEIp5k"),
      dict(title="Python Full Course by freeCodeCamp", instructor="freeCodeCamp", thumbnail="https://img.youtube.com/vi/eWRfhZUzrAc/maxresdefault.jpg", duration_weeks=14, rating=4.9, is_premium=False, category="Python", level="Beginner", description="Comprehensive Python course from freeCodeCamp covering everything.", main_vid="eWRfhZUzrAc"),
      dict(title="Python OOP by Corey Schafer", instructor="Corey Schafer", thumbnail="https://img.youtube.com/vi/ZDa-Z5JzLYM/maxresdefault.jpg", duration_weeks=6, rating=4.9, is_premium=False, category="Python", level="Intermediate", description="Master object-oriented programming in Python.", main_vid="ZDa-Z5JzLYM"),
      dict(title="Advanced Python by Telusko", instructor="Telusko", thumbnail="https://img.youtube.com/vi/p15xzjzR9j0/maxresdefault.jpg", duration_weeks=10, rating=4.8, is_premium=True, category="Python", level="Advanced", description="Advanced Python: decorators, generators, async, metaclasses.", main_vid="p15xzjzR9j0"),
      dict(title="Web Development by Apna College", instructor="Apna College", thumbnail="https://img.youtube.com/vi/tVzUXW6siu0/maxresdefault.jpg", duration_weeks=12, rating=4.8, is_premium=False, category="Web Development", level="Beginner", description="Full web development course covering HTML, CSS, JavaScript and more.", main_vid="tVzUXW6siu0"),
      dict(title="CSS Flexbox & Grid by Kevin Powell", instructor="Kevin Powell", thumbnail="https://img.youtube.com/vi/phWxA89Dy94/maxresdefault.jpg", duration_weeks=4, rating=4.9, is_premium=False, category="Web Development", level="Intermediate", description="Master CSS Flexbox and Grid layout systems.", main_vid="phWxA89Dy94"),
      dict(title="Tailwind CSS Full Course", instructor="Dave Gray", thumbnail="https://img.youtube.com/vi/lCxcTsOHrjo/maxresdefault.jpg", duration_weeks=4, rating=4.8, is_premium=False, category="Web Development", level="Beginner", description="Complete Tailwind CSS course covering utility-first CSS framework.", main_vid="lCxcTsOHrjo"),
      dict(title="Full Stack Web Dev by Traversy", instructor="Traversy Media", thumbnail="https://img.youtube.com/vi/ysEN5RaKOlA/maxresdefault.jpg", duration_weeks=16, rating=4.9, is_premium=True, category="Web Development", level="Intermediate", description="Full stack web development covering frontend and backend.", main_vid="ysEN5RaKOlA"),
      dict(title="JavaScript Full Course by Bro Code", instructor="Bro Code", thumbnail="https://img.youtube.com/vi/lfmg-EJ8gm4/maxresdefault.jpg", duration_weeks=10, rating=4.7, is_premium=False, category="JavaScript", level="Beginner", description="Complete JavaScript course from beginner to advanced.", main_vid="lfmg-EJ8gm4"),
      dict(title="JavaScript by Akshay Saini", instructor="Akshay Saini", thumbnail="https://img.youtube.com/vi/pN6jk0uUrD8/maxresdefault.jpg", duration_weeks=8, rating=4.9, is_premium=False, category="JavaScript", level="Intermediate", description="Namaste JavaScript - deep dive into JS internals.", main_vid="pN6jk0uUrD8"),
      dict(title="React JS Full Course by Dave Gray", instructor="Dave Gray", thumbnail="https://img.youtube.com/vi/RVFAyFWO4go/maxresdefault.jpg", duration_weeks=8, rating=4.9, is_premium=True, category="JavaScript", level="Intermediate", description="Complete React JS course covering hooks, context, and modern patterns.", main_vid="RVFAyFWO4go"),
      dict(title="Next.js Full Course", instructor="Traversy Media", thumbnail="https://img.youtube.com/vi/mTz0GXj8NN0/maxresdefault.jpg", duration_weeks=8, rating=4.9, is_premium=True, category="JavaScript", level="Intermediate", description="Next.js full course covering SSR, SSG, API routes and deployment.", main_vid="mTz0GXj8NN0"),
      dict(title="TypeScript Full Course", instructor="Academind", thumbnail="https://img.youtube.com/vi/BwuLxPH8IDs/maxresdefault.jpg", duration_weeks=6, rating=4.8, is_premium=False, category="JavaScript", level="Intermediate", description="TypeScript from scratch - types, interfaces, generics and more.", main_vid="BwuLxPH8IDs"),
      dict(title="Node.js & Express by Traversy", instructor="Traversy Media", thumbnail="https://img.youtube.com/vi/Oe421EPjeBE/maxresdefault.jpg", duration_weeks=8, rating=4.7, is_premium=False, category="JavaScript", level="Intermediate", description="Node.js and Express.js crash course for building REST APIs.", main_vid="Oe421EPjeBE"),
      dict(title="Machine Learning by Sentdex", instructor="Sentdex", thumbnail="https://img.youtube.com/vi/OGxgnH8y2NM/maxresdefault.jpg", duration_weeks=16, rating=4.8, is_premium=True, category="Data Science", level="Intermediate", description="Practical machine learning with Python and scikit-learn.", main_vid="OGxgnH8y2NM"),
      dict(title="Deep Learning with TensorFlow", instructor="freeCodeCamp", thumbnail="https://img.youtube.com/vi/tPYj3fFJGjk/maxresdefault.jpg", duration_weeks=14, rating=4.8, is_premium=True, category="Data Science", level="Advanced", description="Deep learning with TensorFlow and Keras from scratch.", main_vid="tPYj3fFJGjk"),
      dict(title="Data Science Full Course", instructor="Simplilearn", thumbnail="https://img.youtube.com/vi/ua-CiDNNj30/maxresdefault.jpg", duration_weeks=12, rating=4.6, is_premium=False, category="Data Science", level="Beginner", description="Complete data science course covering statistics, Python, and ML.", main_vid="ua-CiDNNj30"),
      dict(title="Pandas & NumPy Tutorial", instructor="Corey Schafer", thumbnail="https://img.youtube.com/vi/vmEHCJofslg/maxresdefault.jpg", duration_weeks=6, rating=4.8, is_premium=False, category="Data Science", level="Intermediate", description="Master Pandas and NumPy for data manipulation and analysis.", main_vid="vmEHCJofslg"),
      dict(title="Power BI Full Course", instructor="freeCodeCamp", thumbnail="https://img.youtube.com/vi/NNSHu0rkew8/maxresdefault.jpg", duration_weeks=8, rating=4.7, is_premium=False, category="Data Science", level="Beginner", description="Power BI complete course for data visualization.", main_vid="NNSHu0rkew8"),
      dict(title="Docker Tutorial by TechWorld", instructor="TechWorld with Nana", thumbnail="https://img.youtube.com/vi/3c-iBn73dDE/maxresdefault.jpg", duration_weeks=10, rating=4.8, is_premium=True, category="DevOps", level="Intermediate", description="Docker complete tutorial from basics to production deployment.", main_vid="3c-iBn73dDE"),
      dict(title="Kubernetes Crash Course", instructor="TechWorld with Nana", thumbnail="https://img.youtube.com/vi/s_o8dwzRlu4/maxresdefault.jpg", duration_weeks=8, rating=4.8, is_premium=True, category="DevOps", level="Advanced", description="Kubernetes complete course for container orchestration.", main_vid="s_o8dwzRlu4"),
      dict(title="Git & GitHub by Traversy", instructor="Traversy Media", thumbnail="https://img.youtube.com/vi/SWYqp7iY_Tc/maxresdefault.jpg", duration_weeks=4, rating=4.9, is_premium=False, category="DevOps", level="Beginner", description="Git and GitHub crash course for version control.", main_vid="SWYqp7iY_Tc"),
      dict(title="Linux Command Line", instructor="NetworkChuck", thumbnail="https://img.youtube.com/vi/ZtqBQ68cfJc/maxresdefault.jpg", duration_weeks=4, rating=4.8, is_premium=False, category="DevOps", level="Beginner", description="Linux command line fundamentals for developers.", main_vid="ZtqBQ68cfJc"),
      dict(title="AWS Cloud Practitioner", instructor="freeCodeCamp", thumbnail="https://img.youtube.com/vi/SOTamWNgDKc/maxresdefault.jpg", duration_weeks=12, rating=4.7, is_premium=True, category="DevOps", level="Intermediate", description="AWS Cloud Practitioner certification prep course.", main_vid="SOTamWNgDKc"),
      dict(title="SQL Full Course by freeCodeCamp", instructor="freeCodeCamp", thumbnail="https://img.youtube.com/vi/HXV3zeQKqGY/maxresdefault.jpg", duration_weeks=8, rating=4.7, is_premium=False, category="Database", level="Beginner", description="Complete SQL course covering queries, joins, and database design.", main_vid="HXV3zeQKqGY"),
      dict(title="MySQL Full Course", instructor="Bro Code", thumbnail="https://img.youtube.com/vi/5OdVJbNCSso/maxresdefault.jpg", duration_weeks=6, rating=4.7, is_premium=False, category="Database", level="Beginner", description="MySQL complete course from installation to advanced queries.", main_vid="5OdVJbNCSso"),
      dict(title="MongoDB Full Course", instructor="freeCodeCamp", thumbnail="https://img.youtube.com/vi/ExcRbA7fy_A/maxresdefault.jpg", duration_weeks=6, rating=4.6, is_premium=False, category="Database", level="Beginner", description="MongoDB NoSQL database complete course.", main_vid="ExcRbA7fy_A"),
      dict(title="PostgreSQL Full Course", instructor="freeCodeCamp", thumbnail="https://img.youtube.com/vi/qw--VYLpxG4/maxresdefault.jpg", duration_weeks=8, rating=4.7, is_premium=False, category="Database", level="Intermediate", description="PostgreSQL complete course covering advanced SQL.", main_vid="qw--VYLpxG4"),
      dict(title="DSA by freeCodeCamp", instructor="freeCodeCamp", thumbnail="https://img.youtube.com/vi/pkYVOmU3MgA/maxresdefault.jpg", duration_weeks=14, rating=4.9, is_premium=False, category="DSA", level="Intermediate", description="Data structures and algorithms complete course with Python.", main_vid="pkYVOmU3MgA"),
      dict(title="DSA by Abdul Bari", instructor="Abdul Bari", thumbnail="https://img.youtube.com/vi/0IAPZzGSbME/maxresdefault.jpg", duration_weeks=16, rating=4.9, is_premium=False, category="DSA", level="Intermediate", description="Data structures and algorithms with visual explanations.", main_vid="0IAPZzGSbME"),
      dict(title="LeetCode Patterns by NeetCode", instructor="NeetCode", thumbnail="https://img.youtube.com/vi/KLlXCFG5TnA/maxresdefault.jpg", duration_weeks=10, rating=4.9, is_premium=True, category="DSA", level="Advanced", description="Master LeetCode patterns and ace coding interviews.", main_vid="KLlXCFG5TnA"),
      dict(title="Java Full Course by Amigoscode", instructor="Amigoscode", thumbnail="https://img.youtube.com/vi/Qgl81fPcLc8/maxresdefault.jpg", duration_weeks=12, rating=4.7, is_premium=False, category="Java", level="Beginner", description="Java complete course from basics to OOP.", main_vid="Qgl81fPcLc8"),
      dict(title="Spring Boot Full Course", instructor="Amigoscode", thumbnail="https://img.youtube.com/vi/9SGDpanrc8U/maxresdefault.jpg", duration_weeks=10, rating=4.8, is_premium=True, category="Java", level="Intermediate", description="Spring Boot complete course for production-ready Java apps.", main_vid="9SGDpanrc8U"),
      dict(title="Java DSA by Kunal Kushwaha", instructor="Kunal Kushwaha", thumbnail="https://img.youtube.com/vi/rZ41y93P2Qo/maxresdefault.jpg", duration_weeks=16, rating=4.9, is_premium=False, category="Java", level="Beginner", description="Data structures and algorithms in Java.", main_vid="rZ41y93P2Qo"),
      dict(title="Flutter & Dart Full Course", instructor="Net Ninja", thumbnail="https://img.youtube.com/vi/1ukSR1GRtMU/maxresdefault.jpg", duration_weeks=12, rating=4.8, is_premium=True, category="Mobile", level="Intermediate", description="Flutter and Dart complete course for cross-platform mobile development.", main_vid="1ukSR1GRtMU"),
      dict(title="C++ Full Course by Bro Code", instructor="Bro Code", thumbnail="https://img.youtube.com/vi/-TkoO8Z07hI/maxresdefault.jpg", duration_weeks=10, rating=4.6, is_premium=False, category="Other", level="Beginner", description="C++ complete course from basics to OOP.", main_vid="-TkoO8Z07hI"),
    ]

    # Only seed if empty
    if Course.query.count() > 0:
        return jsonify({'message': f'Already seeded: {Course.query.count()} courses'}), 200

    for data in COURSES:
        main_vid = data.pop("main_vid")
        course = Course(**{k: v for k, v in data.items()})
        db.session.add(course)
        db.session.flush()
        for lesson in make_lessons(course.id, main_vid):
            db.session.add(lesson)
    db.session.commit()
    return jsonify({'message': f'Seeded {Course.query.count()} courses successfully'}), 201

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
