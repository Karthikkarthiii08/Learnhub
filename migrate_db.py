import sqlite3, os, sys

db_path = os.path.join('database', 'lms.db')
if not os.path.exists(db_path):
    print('DB not found at', db_path)
    sys.exit(1)

conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute('PRAGMA table_info(courses)')
cols = [r[1] for r in cur.fetchall()]
print('Existing columns:', cols)

if 'category' not in cols:
    cur.execute("ALTER TABLE courses ADD COLUMN category VARCHAR(100) DEFAULT 'General'")
    print('Added: category')
else:
    print('Already exists: category')

if 'level' not in cols:
    cur.execute("ALTER TABLE courses ADD COLUMN level VARCHAR(50) DEFAULT 'Beginner'")
    print('Added: level')
else:
    print('Already exists: level')

conn.commit()
conn.close()
print('Migration complete.')
