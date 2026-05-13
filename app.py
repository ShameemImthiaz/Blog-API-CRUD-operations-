from flask import Flask, request, jsonify, g
import sqlite3
from datetime import datetime

app = Flask(__name__)
DATABASE = "blog.db"

# -------------------------------
# Database Helper Functions
# -------------------------------

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    db.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    db.commit()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# -------------------------------
# Routes
# -------------------------------
from flask import render_template

@app.route('/')
def home():
    return render_template('index.html')

# CREATE POST
@app.route('/posts', methods=['POST'])
def create_post():
    data = request.get_json()

    if not data or not data.get('title') or not data.get('content'):
        return jsonify({"error": "Title and content required"}), 400

    now = datetime.utcnow().isoformat()

    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        INSERT INTO posts (title, content, created_at, updated_at)
        VALUES (?, ?, ?, ?)
    ''', (data['title'], data['content'], now, now))

    db.commit()

    return jsonify({
        "message": "Post created",
        "post_id": cursor.lastrowid
    }), 201

# READ ALL POSTS
@app.route('/posts', methods=['GET'])
def get_posts():
    db = get_db()
    posts = db.execute('SELECT * FROM posts').fetchall()

    result = []
    for post in posts:
        result.append(dict(post))

    return jsonify(result)

# READ SINGLE POST
@app.route('/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    db = get_db()
    post = db.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()

    if post is None:
        return jsonify({"error": "Post not found"}), 404

    return jsonify(dict(post))

# UPDATE POST
@app.route('/posts/<int:post_id>', methods=['PUT'])
def update_post(post_id):
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    db = get_db()
    post = db.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()

    if post is None:
        return jsonify({"error": "Post not found"}), 404

    title = data.get('title', post['title'])
    content = data.get('content', post['content'])
    updated_at = datetime.utcnow().isoformat()

    db.execute('''
        UPDATE posts
        SET title = ?, content = ?, updated_at = ?
        WHERE id = ?
    ''', (title, content, updated_at, post_id))

    db.commit()

    return jsonify({"message": "Post updated"})

# DELETE POST
@app.route('/posts/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    db = get_db()
    post = db.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()

    if post is None:
        return jsonify({"error": "Post not found"}), 404

    db.execute('DELETE FROM posts WHERE id = ?', (post_id,))
    db.commit()

    return jsonify({"message": "Post deleted"})

# -------------------------------
# Run App
# -------------------------------

if __name__ == '__main__':
    with app.app_context():
        init_db()

    app.run(host='0.0.0.0', port=5000))
