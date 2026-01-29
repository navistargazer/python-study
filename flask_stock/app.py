from flask import Flask, render_template, url_for, request, session, redirect, flash
import pymysql
from config import Config
import hashlib

app = Flask(__name__)
app.config.from_object(Config)

def get_db():
    return pymysql.connect(
         host=app.config['DB_HOST']
        ,user=app.config['DB_USER']
        ,password=app.config['DB_PASSWORD']
        ,db=app.config['DB_NAME']
        ,charset='utf8mb4'
        ,cursorclass=pymysql.cursors.DictCursor
    )

@app.route('/')
def index():
    conn = None
    users =[]
    try:
        conn = get_db()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users")
            users = cursor.fetchall()
    except Exception as e:
        print(str(e))
    finally:
        if conn:
            conn.close()

    return render_template('list.html', users=users)

def hash_pw(pw):
    return hashlib.sha256(pw.encode('utf-8')).hexdigest()

@app.route('/login', methods=['GET', 'POST'])
def login():
    # 요청 종류가 POST일 경우(GET방식도 따로 설정할 수 있음
    if request.method == "POST":
        username = request.form['username']
        password = hash_pw(request.form['password'])    # 암호화된 비번
        print(username + '   /   ' + password)
        # 데이터베이스와 비교
        try:
            conn = get_db()
            with conn.cursor() as cursor:
                cursor.execute("SELECT user_id, login_id, user_nm FROM users WHERE login_id = %s AND user_pw = %s", (username, password))
                user = cursor.fetchone()
                if user:
                    # 로그인 정보를 세션에 저장(유지)
                    session['login_id'] = user['user_id']
                    session['user_nm'] = user['user_nm']
                    flash(f'{user['user_nm']}님 환영합니다.', 'success')  # flash:알림
                    return redirect(url_for('index'))
                    # return render_template("list.html")
                else:
                    flash('아이디 또는 비밀번호가 틀렸습니다!', 'error')
        except Exception as e:
            print(str(e))
        finally:
            if conn:
                conn.close()

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear() # 세션 정보 삭제
    flash('로그아웃 되었습니다.', 'success')
    return redirect(url_for('index'))
    return redirect(url_for('login'))   # 로그인 창으로 리다이렉트

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        username = request.form['username']
        password = hash_pw(request.form['password'])  # 암호화된 비번
        print(username + '   /   ' + password)
        # 데이터베이스와 비교
        try:
            conn = get_db()
            with conn.cursor() as cursor:
                # 이미 등록되어 있으면 등록 불가
                check_sql = 'SELECT user_id FROM users WHERE login_id = %s'
                cursor.execute(check_sql, (username, ))
                user = cursor.fetchone()
                if user:
                    flash(f'{user['user_nm']}님은 이미 가입되어 있습니다.', 'success')
                    return redirect(url_for('login'))
                else:
                    insert_sql = 'INSERT INTO users (login_id, user_pw, user_nm) VALUES (%s, %s, %s)'
                    cursor.execute(insert_sql, (username, password, username))
                    conn.commit()
                    flash('회원 가입에 성공했습니다.', 'success')
                    return redirect(url_for('index'))
        except Exception as e:
            print(str(e))
        finally:
            if conn:
                conn.close()

    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True)