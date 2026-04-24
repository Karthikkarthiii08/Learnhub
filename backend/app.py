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

LESSON_VIDS = ["kqtD5dpn9C8", "DZwmZ8Usvnk", "9Os0o3wzS_I", "JeznW_7DlB0"]
LESSON_TITLES = ["Introduction & Overview", "Core Concepts", "Hands-on Practice", "Advanced Topics", "Project & Review"]

SEED_COURSES = [
  # PYTHON
  dict(title="Complete Python by Shradha Khapra", instructor="Shradha Khapra", thumbnail="https://img.youtube.com/vi/_uQrJ0TkZlc/maxresdefault.jpg", duration_weeks=12, rating=4.8, is_premium=False, category="Python", level="Beginner", description="Complete Python from scratch covering variables, loops, functions and OOP.", main_vid="_uQrJ0TkZlc"),
  dict(title="Python Full Course - freeCodeCamp", instructor="freeCodeCamp", thumbnail="https://img.youtube.com/vi/eWRfhZUzrAc/maxresdefault.jpg", duration_weeks=14, rating=4.9, is_premium=False, category="Python", level="Beginner", description="Comprehensive Python course from freeCodeCamp covering everything.", main_vid="eWRfhZUzrAc"),
  dict(title="Python OOP by Corey Schafer", instructor="Corey Schafer", thumbnail="https://img.youtube.com/vi/ZDa-Z5JzLYM/maxresdefault.jpg", duration_weeks=6, rating=4.9, is_premium=False, category="Python", level="Intermediate", description="Master object-oriented programming in Python.", main_vid="ZDa-Z5JzLYM"),
  dict(title="Python by Telusko", instructor="Telusko", thumbnail="https://img.youtube.com/vi/PkZNo7MFNFg/maxresdefault.jpg", duration_weeks=10, rating=4.7, is_premium=False, category="Python", level="Beginner", description="Learn Python from basics to advanced with Telusko.", main_vid="PkZNo7MFNFg"),
  dict(title="Advanced Python by Telusko", instructor="Telusko", thumbnail="https://img.youtube.com/vi/p15xzjzR9j0/maxresdefault.jpg", duration_weeks=10, rating=4.8, is_premium=True, category="Python", level="Advanced", description="Advanced Python: decorators, generators, async, metaclasses.", main_vid="p15xzjzR9j0"),
  dict(title="Python for Data Science", instructor="Data with Baraa", thumbnail="https://img.youtube.com/vi/nLRL_NcnK-4/maxresdefault.jpg", duration_weeks=8, rating=4.7, is_premium=False, category="Python", level="Intermediate", description="Python for data science including pandas, numpy and visualization.", main_vid="nLRL_NcnK-4"),
  # WEB DEVELOPMENT
  dict(title="Web Development by Apna College", instructor="Apna College", thumbnail="https://img.youtube.com/vi/tVzUXW6siu0/maxresdefault.jpg", duration_weeks=12, rating=4.8, is_premium=False, category="Web Development", level="Beginner", description="Full web development course covering HTML, CSS, JavaScript and more.", main_vid="tVzUXW6siu0"),
  dict(title="HTML & CSS Full Course", instructor="SuperSimpleDev", thumbnail="https://img.youtube.com/vi/G3e-cpL7ofc/maxresdefault.jpg", duration_weeks=6, rating=4.8, is_premium=False, category="Web Development", level="Beginner", description="Learn HTML and CSS from scratch with simple clear explanations.", main_vid="G3e-cpL7ofc"),
  dict(title="CSS Flexbox & Grid by Kevin Powell", instructor="Kevin Powell", thumbnail="https://img.youtube.com/vi/phWxA89Dy94/maxresdefault.jpg", duration_weeks=4, rating=4.9, is_premium=False, category="Web Development", level="Intermediate", description="Master CSS Flexbox and Grid layout systems.", main_vid="phWxA89Dy94"),
  dict(title="Tailwind CSS Full Course", instructor="Dave Gray", thumbnail="https://img.youtube.com/vi/lCxcTsOHrjo/maxresdefault.jpg", duration_weeks=4, rating=4.8, is_premium=False, category="Web Development", level="Beginner", description="Complete Tailwind CSS utility-first framework course.", main_vid="lCxcTsOHrjo"),
  dict(title="Full Stack Web Dev by Traversy", instructor="Traversy Media", thumbnail="https://img.youtube.com/vi/ysEN5RaKOlA/maxresdefault.jpg", duration_weeks=16, rating=4.9, is_premium=True, category="Web Development", level="Intermediate", description="Full stack web development covering frontend and backend.", main_vid="ysEN5RaKOlA"),
  dict(title="Bootstrap 5 Full Course", instructor="Academind", thumbnail="https://img.youtube.com/vi/4sosXZsdy-s/maxresdefault.jpg", duration_weeks=5, rating=4.6, is_premium=False, category="Web Development", level="Beginner", description="Bootstrap 5 complete guide for responsive websites.", main_vid="4sosXZsdy-s"),
  # JAVASCRIPT
  dict(title="JavaScript Full Course by Bro Code", instructor="Bro Code", thumbnail="https://img.youtube.com/vi/lfmg-EJ8gm4/maxresdefault.jpg", duration_weeks=10, rating=4.7, is_premium=False, category="JavaScript", level="Beginner", description="Complete JavaScript course from beginner to advanced.", main_vid="lfmg-EJ8gm4"),
  dict(title="Namaste JavaScript by Akshay Saini", instructor="Akshay Saini", thumbnail="https://img.youtube.com/vi/pN6jk0uUrD8/maxresdefault.jpg", duration_weeks=8, rating=4.9, is_premium=False, category="JavaScript", level="Intermediate", description="Deep dive into JS internals and advanced concepts.", main_vid="pN6jk0uUrD8"),
  dict(title="React JS Full Course by Dave Gray", instructor="Dave Gray", thumbnail="https://img.youtube.com/vi/RVFAyFWO4go/maxresdefault.jpg", duration_weeks=8, rating=4.9, is_premium=True, category="JavaScript", level="Intermediate", description="Complete React JS course covering hooks, context, and modern patterns.", main_vid="RVFAyFWO4go"),
  dict(title="Next.js Full Course by Traversy", instructor="Traversy Media", thumbnail="https://img.youtube.com/vi/mTz0GXj8NN0/maxresdefault.jpg", duration_weeks=8, rating=4.9, is_premium=True, category="JavaScript", level="Intermediate", description="Next.js full course covering SSR, SSG, API routes and deployment.", main_vid="mTz0GXj8NN0"),
  dict(title="TypeScript Full Course", instructor="Academind", thumbnail="https://img.youtube.com/vi/BwuLxPH8IDs/maxresdefault.jpg", duration_weeks=6, rating=4.8, is_premium=False, category="JavaScript", level="Intermediate", description="TypeScript from scratch - types, interfaces, generics and more.", main_vid="BwuLxPH8IDs"),
  dict(title="Node.js & Express by Traversy", instructor="Traversy Media", thumbnail="https://img.youtube.com/vi/Oe421EPjeBE/maxresdefault.jpg", duration_weeks=8, rating=4.7, is_premium=False, category="JavaScript", level="Intermediate", description="Node.js and Express.js for building REST APIs.", main_vid="Oe421EPjeBE"),
  # DATA SCIENCE
  dict(title="Machine Learning by Sentdex", instructor="Sentdex", thumbnail="https://img.youtube.com/vi/OGxgnH8y2NM/maxresdefault.jpg", duration_weeks=16, rating=4.8, is_premium=True, category="Data Science", level="Intermediate", description="Practical machine learning with Python and scikit-learn.", main_vid="OGxgnH8y2NM"),
  dict(title="Deep Learning with TensorFlow", instructor="freeCodeCamp", thumbnail="https://img.youtube.com/vi/tPYj3fFJGjk/maxresdefault.jpg", duration_weeks=14, rating=4.8, is_premium=True, category="Data Science", level="Advanced", description="Deep learning with TensorFlow and Keras from scratch.", main_vid="tPYj3fFJGjk"),
  dict(title="Data Science Full Course", instructor="Simplilearn", thumbnail="https://img.youtube.com/vi/ua-CiDNNj30/maxresdefault.jpg", duration_weeks=12, rating=4.6, is_premium=False, category="Data Science", level="Beginner", description="Complete data science covering statistics, Python, and ML.", main_vid="ua-CiDNNj30"),
  dict(title="Pandas & NumPy by Corey Schafer", instructor="Corey Schafer", thumbnail="https://img.youtube.com/vi/vmEHCJofslg/maxresdefault.jpg", duration_weeks=6, rating=4.8, is_premium=False, category="Data Science", level="Intermediate", description="Master Pandas and NumPy for data manipulation.", main_vid="vmEHCJofslg"),
  dict(title="Power BI Full Course", instructor="freeCodeCamp", thumbnail="https://img.youtube.com/vi/NNSHu0rkew8/maxresdefault.jpg", duration_weeks=8, rating=4.7, is_premium=False, category="Data Science", level="Beginner", description="Power BI complete course for data visualization.", main_vid="NNSHu0rkew8"),
  dict(title="Statistics for Data Science", instructor="StatQuest", thumbnail="https://img.youtube.com/vi/qBigTkBLU6g/maxresdefault.jpg", duration_weeks=10, rating=4.9, is_premium=False, category="Data Science", level="Beginner", description="Statistics fundamentals for data science explained clearly.", main_vid="qBigTkBLU6g"),
  # DEVOPS
  dict(title="Docker Tutorial by TechWorld with Nana", instructor="TechWorld with Nana", thumbnail="https://img.youtube.com/vi/3c-iBn73dDE/maxresdefault.jpg", duration_weeks=10, rating=4.8, is_premium=True, category="DevOps", level="Intermediate", description="Docker complete tutorial from basics to production.", main_vid="3c-iBn73dDE"),
  dict(title="Kubernetes Crash Course", instructor="TechWorld with Nana", thumbnail="https://img.youtube.com/vi/s_o8dwzRlu4/maxresdefault.jpg", duration_weeks=8, rating=4.8, is_premium=True, category="DevOps", level="Advanced", description="Kubernetes complete course for container orchestration.", main_vid="s_o8dwzRlu4"),
  dict(title="Git & GitHub by Traversy Media", instructor="Traversy Media", thumbnail="https://img.youtube.com/vi/SWYqp7iY_Tc/maxresdefault.jpg", duration_weeks=4, rating=4.9, is_premium=False, category="DevOps", level="Beginner", description="Git and GitHub crash course for version control.", main_vid="SWYqp7iY_Tc"),
  dict(title="Linux Command Line by NetworkChuck", instructor="NetworkChuck", thumbnail="https://img.youtube.com/vi/ZtqBQ68cfJc/maxresdefault.jpg", duration_weeks=4, rating=4.8, is_premium=False, category="DevOps", level="Beginner", description="Linux command line fundamentals for developers.", main_vid="ZtqBQ68cfJc"),
  dict(title="AWS Cloud Practitioner", instructor="freeCodeCamp", thumbnail="https://img.youtube.com/vi/SOTamWNgDKc/maxresdefault.jpg", duration_weeks=12, rating=4.7, is_premium=True, category="DevOps", level="Intermediate", description="AWS Cloud Practitioner certification prep course.", main_vid="SOTamWNgDKc"),
  # DATABASE
  dict(title="SQL Full Course by freeCodeCamp", instructor="freeCodeCamp", thumbnail="https://img.youtube.com/vi/HXV3zeQKqGY/maxresdefault.jpg", duration_weeks=8, rating=4.7, is_premium=False, category="Database", level="Beginner", description="Complete SQL course covering queries, joins, and database design.", main_vid="HXV3zeQKqGY"),
  dict(title="MySQL Full Course by Bro Code", instructor="Bro Code", thumbnail="https://img.youtube.com/vi/5OdVJbNCSso/maxresdefault.jpg", duration_weeks=6, rating=4.7, is_premium=False, category="Database", level="Beginner", description="MySQL complete course from installation to advanced queries.", main_vid="5OdVJbNCSso"),
  dict(title="MongoDB Full Course", instructor="freeCodeCamp", thumbnail="https://img.youtube.com/vi/ExcRbA7fy_A/maxresdefault.jpg", duration_weeks=6, rating=4.6, is_premium=False, category="Database", level="Beginner", description="MongoDB NoSQL database complete course.", main_vid="ExcRbA7fy_A"),
  dict(title="PostgreSQL Full Course", instructor="freeCodeCamp", thumbnail="https://img.youtube.com/vi/qw--VYLpxG4/maxresdefault.jpg", duration_weeks=8, rating=4.7, is_premium=False, category="Database", level="Intermediate", description="PostgreSQL complete course covering advanced SQL.", main_vid="qw--VYLpxG4"),
  # DSA
  dict(title="DSA Full Course by freeCodeCamp", instructor="freeCodeCamp", thumbnail="https://img.youtube.com/vi/pkYVOmU3MgA/maxresdefault.jpg", duration_weeks=14, rating=4.9, is_premium=False, category="DSA", level="Intermediate", description="Data structures and algorithms complete course with Python.", main_vid="pkYVOmU3MgA"),
  dict(title="DSA by Abdul Bari", instructor="Abdul Bari", thumbnail="https://img.youtube.com/vi/0IAPZzGSbME/maxresdefault.jpg", duration_weeks=16, rating=4.9, is_premium=False, category="DSA", level="Intermediate", description="Data structures and algorithms with visual explanations.", main_vid="0IAPZzGSbME"),
  dict(title="LeetCode Patterns by NeetCode", instructor="NeetCode", thumbnail="https://img.youtube.com/vi/KLlXCFG5TnA/maxresdefault.jpg", duration_weeks=10, rating=4.9, is_premium=True, category="DSA", level="Advanced", description="Master LeetCode patterns and ace coding interviews.", main_vid="KLlXCFG5TnA"),
  dict(title="Java DSA by Kunal Kushwaha", instructor="Kunal Kushwaha", thumbnail="https://img.youtube.com/vi/rZ41y93P2Qo/maxresdefault.jpg", duration_weeks=16, rating=4.9, is_premium=False, category="DSA", level="Beginner", description="Data structures and algorithms in Java.", main_vid="rZ41y93P2Qo"),
  # JAVA
  dict(title="Java Full Course by Amigoscode", instructor="Amigoscode", thumbnail="https://img.youtube.com/vi/Qgl81fPcLc8/maxresdefault.jpg", duration_weeks=12, rating=4.7, is_premium=False, category="Java", level="Beginner", description="Java complete course from basics to OOP.", main_vid="Qgl81fPcLc8"),
  dict(title="Spring Boot Full Course", instructor="Amigoscode", thumbnail="https://img.youtube.com/vi/9SGDpanrc8U/maxresdefault.jpg", duration_weeks=10, rating=4.8, is_premium=True, category="Java", level="Intermediate", description="Spring Boot complete course for production-ready Java apps.", main_vid="9SGDpanrc8U"),
  dict(title="Java by Telusko", instructor="Telusko", thumbnail="https://img.youtube.com/vi/BGTx91t8q50/maxresdefault.jpg", duration_weeks=12, rating=4.7, is_premium=False, category="Java", level="Beginner", description="Java programming complete course by Telusko.", main_vid="BGTx91t8q50"),
  # MOBILE
  dict(title="Flutter & Dart Full Course", instructor="Net Ninja", thumbnail="https://img.youtube.com/vi/1ukSR1GRtMU/maxresdefault.jpg", duration_weeks=12, rating=4.8, is_premium=True, category="Mobile", level="Intermediate", description="Flutter and Dart for cross-platform mobile development.", main_vid="1ukSR1GRtMU"),
  dict(title="Android Development Java", instructor="freeCodeCamp", thumbnail="https://img.youtube.com/vi/fis26HvvDII/maxresdefault.jpg", duration_weeks=14, rating=4.6, is_premium=False, category="Mobile", level="Intermediate", description="Android app development with Java from scratch.", main_vid="fis26HvvDII"),
  dict(title="React Native Full Course", instructor="Academind", thumbnail="https://img.youtube.com/vi/qSRrxpdMpVc/maxresdefault.jpg", duration_weeks=10, rating=4.7, is_premium=True, category="Mobile", level="Intermediate", description="React Native complete course for iOS and Android apps.", main_vid="qSRrxpdMpVc"),
]

def _auto_seed():
    from models import Course, Lesson
    if Course.query.count() > 0:
        return
    try:
        for data in SEED_COURSES:
            main_vid = data.pop("main_vid")
            course = Course(**{k: v for k, v in data.items()})
            db.session.add(course)
            db.session.flush()
            vids = [main_vid] + LESSON_VIDS
            for i in range(5):
                db.session.add(Lesson(
                    course_id=course.id,
                    title=LESSON_TITLES[i],
                    video_url=f"https://www.youtube.com/watch?v={vids[i]}",
                    lesson_order=i + 1
                ))
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Seed error: {e}")

# Auto-create tables + seed if empty (works on Vercel Postgres)
with app.app_context():
    db.create_all()
    _auto_seed()

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
