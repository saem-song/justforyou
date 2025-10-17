from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Flask 앱 설정
app = Flask(__name__)
# SQLite 데이터베이스 설정
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# -------------------- DB 모델 (게시글 테이블 정의) --------------------
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    # 작성자 필드 추가 (nullable=False로 필수 입력)
    author = db.Column(db.String(50), default="익명", nullable=False) 
    content = db.Column(db.Text, nullable=False)
    # 생성 시간 (최초 저장 시각)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # 최종 수정 시간 (수정될 때마다 자동으로 현재 시각으로 업데이트)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) 

    def __repr__(self):
        return f'<Post {self.id}>'

# -------------------- DB 초기화 (테이블 생성) --------------------
with app.app_context():
    # db.create_all() <-- 이 줄을 주석 처리하거나 삭제합니다.
    pass # DB 초기화는 Render에서 수동으로 처리하도록 합니다.


# -------------------- 1. READ (목록 및 검색) --------------------
@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search_query', '')
    per_page = 10 

    query = Post.query.order_by(Post.created_at.desc())
    
    if search_query:
        # 제목 또는 내용에 검색어가 포함된 게시글을 찾음
        search_filter = Post.title.like(f'%{search_query}%') | Post.content.like(f'%{search_query}%')
        query = query.filter(search_filter)

    posts_pagination = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('index.html', 
                           posts_pagination=posts_pagination, 
                           posts=posts_pagination.items,
                           search_query=search_query) 

@app.route('/post/<int:post_id>')
def post_detail(post_id):
    post = db.get_or_404(Post, post_id)
    return render_template('detail.html', post=post)

# -------------------- 2. CREATE (게시글 작성) --------------------
@app.route('/write', methods=['GET', 'POST'])
def write():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        # 작성자 필드가 비어있으면 "익명" 처리
        author = request.form['author'] or "익명" 

        new_post = Post(title=title, content=content, author=author) 
        try:
            db.session.add(new_post)
            db.session.commit()
            return redirect(url_for('index'))
        except:
            return "게시글 작성 중 에러가 발생했습니다."

    return render_template('write.html')

# -------------------- 3. UPDATE (게시글 수정) --------------------
@app.route('/edit/<int:post_id>', methods=['GET', 'POST'])
def edit(post_id):
    post = db.get_or_404(Post, post_id)
    
    if request.method == 'POST':
        post.title = request.form['title']
        post.author = request.form['author']
        post.content = request.form['content']
        # updated_at 필드는 모델에서 onupdate=datetime.utcnow로 자동 처리됨

        try:
            db.session.commit()
            return redirect(url_for('post_detail', post_id=post.id)) 
        except:
            return "게시글 수정 중 에러가 발생했습니다."
    
    # GET 요청 시 수정 폼 보여주기
    return render_template('edit.html', post=post) 

# -------------------- 4. DELETE (게시글 삭제) --------------------
@app.route('/delete/<int:post_id>', methods=['POST'])
def delete(post_id):
    post = db.get_or_404(Post, post_id)
    
    try:
        db.session.delete(post)
        db.session.commit()
        return redirect(url_for('index'))
    except:
        return "게시글 삭제 중 에러가 발생했습니다."


# 서버 실행 (디버그 모드 켜기)
if __name__ == '__main__':
    app.run(debug=True)
