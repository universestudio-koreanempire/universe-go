from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from datetime import datetime, date
from openai import OpenAI
import sqlite3
import hashlib
import os
import uuid
invite_ips = {}
heartbeats = {}
server_names = {}

app = Flask(__name__)
app.secret_key = 'mafia_go_secret_key_2024'

def render_online_shell(title, subtitle, inner_html):
    return f'''
    <!DOCTYPE html>
    <html>
    <body>
        <h1>{title}</h1>
        <p>{subtitle}</p>
        {inner_html}
    </body>
    </html>
    '''

app = Flask(__name__)
app.secret_key = 'mafia_go_secret_key_2024'

def render_online_shell(title, subtitle, inner_html):
    return f'''
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
        <style>
            body {{
                margin: 0;
                font-family: "Noto Sans KR", sans-serif;
                background:
                    radial-gradient(circle at top, rgba(59,130,246,0.35), transparent 40%),
                    radial-gradient(circle at bottom right, rgba(168,85,247,0.25), transparent 35%),
                    linear-gradient(135deg, #050816 0%, #0b1220 50%, #111827 100%);
                color: #fff;
                min-height: 100vh;
            }}
            .page {{
                max-width: 980px;
                margin: 0 auto;
                padding: 28px 18px 40px;
            }}
            .hero {{
                text-align: center;
                padding: 28px 18px 10px;
            }}
            .hero h1 {{
                margin: 0;
                font-size: 42px;
                font-weight: 900;
                letter-spacing: -0.04em;
                text-shadow: 0 0 22px rgba(96,165,250,0.35);
            }}
            .hero p {{
                margin: 12px auto 0;
                max-width: 620px;
                color: rgba(255,255,255,0.78);
                font-size: 16px;
                line-height: 1.7;
            }}
            .panel {{
                margin-top: 26px;
                background: rgba(15, 23, 42, 0.72);
                border: 1px solid rgba(148, 163, 184, 0.18);
                border-radius: 28px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.45);
                backdrop-filter: blur(14px);
                -webkit-backdrop-filter: blur(14px);
                padding: 28px;
            }}
            .section-title {{
                margin: 0 0 14px;
                font-size: 14px;
                letter-spacing: 0.12em;
                text-transform: uppercase;
                color: rgba(226,232,240,0.72);
            }}
            .card-grid {{
                display: grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 16px;
            }}
            .action-btn {{
                width: 100%;
                border: none;
                border-radius: 18px;
                padding: 18px 16px;
                font-size: 17px;
                font-weight: 800;
                color: #fff;
                cursor: pointer;
                transition: transform .18s ease, box-shadow .18s ease, filter .18s ease;
                box-shadow: 0 10px 28px rgba(0,0,0,0.25);
            }}
            .action-btn:hover {{
                transform: translateY(-2px);
                filter: brightness(1.05);
            }}
            .btn-blue {{ background: linear-gradient(135deg, #2563eb, #3b82f6); }}
            .btn-purple {{ background: linear-gradient(135deg, #7c3aed, #a855f7); }}
            .btn-green {{ background: linear-gradient(135deg, #059669, #10b981); }}
            .btn-orange {{ background: linear-gradient(135deg, #ea580c, #f97316); }}
            .btn-red {{ background: linear-gradient(135deg, #b91c1c, #ef4444); }}
            .form-box {{
                display: grid;
                gap: 14px;
                max-width: 540px;
                margin: 0 auto;
            }}
            .input {{
                width: 100%;
                box-sizing: border-box;
                padding: 14px 16px;
                border-radius: 14px;
                border: 1px solid rgba(255,255,255,0.12);
                background: rgba(255,255,255,0.06);
                color: #fff;
                outline: none;
                font-size: 16px;
            }}
            .input::placeholder {{
                color: rgba(226,232,240,0.6);
            }}
            .note {{
                text-align: center;
                margin-top: 18px;
                color: rgba(226,232,240,0.68);
                font-size: 13px;
                line-height: 1.6;
            }}
            .flash {{
                max-width: 540px;
                margin: 0 auto 16px;
                padding: 12px 14px;
                border-radius: 14px;
                background: rgba(255,255,255,0.08);
                border: 1px solid rgba(255,255,255,0.12);
            }}
            @media (max-width: 700px) {{
                .hero h1 {{ font-size: 32px; }}
                .panel {{ padding: 18px; border-radius: 22px; }}
                .card-grid {{ grid-template-columns: 1fr; }}
            }}
        </style>
    </head>
    <body>
        <div class="page">
            <div class="hero">
                <h1>{title}</h1>
                <p>{subtitle}</p>
            </div>
            <div class="panel">
                {inner_html}
            </div>
        </div>
    </body>
    </html>
    '''

usage = {}

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = "모르는 건 모른다고 말하고, 필요하면 문의 기능을 이용하라고 안내해줘."

# ===== 관리자 계정 설정 =====
# 관리자 아이디를 여기에 추가하세요. 여러 명 지정 가능.
ADMIN_USERS = ['admin']

# ===== 광고 설정 =====
# 모든 광고는 여기서 관리하세요.

# 파노라마 광고 (980x120) — 메인 히어로 아래 가로 배너
# Google Ads 삽입 시 아래 내용을 AdSense 코드로 교체하세요.
AD_PANORAMA = """
<div style="
    width: 980px; height: 120px; max-width: 100%; margin: 0 auto;
    background: #1e7e8a; display: flex; align-items: center; justify-content: center;
    border-radius: 0px; color: white; font-size: 1.1rem; font-weight: 700;
    letter-spacing: 1px; box-shadow: 0 2px 10px rgba(0,0,0,0.15);
">광고 공간 (980 × 120 · 파노라마)</div>
"""

DB_PATH = os.path.join(os.path.dirname(__file__), 'mafia_go.db')

# ===== DB 초기화 =====
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT    UNIQUE NOT NULL,
            email    TEXT    UNIQUE,
            password TEXT    NOT NULL,
            created  TEXT    NOT NULL
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS complaints (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            category TEXT NOT NULL,
            title    TEXT NOT NULL,
            content  TEXT NOT NULL,
            status   TEXT NOT NULL DEFAULT '접수 완료',
            created  TEXT NOT NULL
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS notices (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            title   TEXT NOT NULL,
            content TEXT NOT NULL,
            created TEXT NOT NULL
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS purchases (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            username   TEXT NOT NULL,
            item_id    INTEGER NOT NULL,
            item_name  TEXT NOT NULL,
            method     TEXT NOT NULL,
            amount     TEXT NOT NULL,
            status     TEXT NOT NULL DEFAULT '완료',
            created    TEXT NOT NULL
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS rewards (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            amount   INTEGER NOT NULL DEFAULT 10,
            created  TEXT NOT NULL
        )
    ''')

    cur.execute('''
    CREATE TABLE IF NOT EXISTS online_nicknames (
        player_id  TEXT PRIMARY KEY,
        nickname   TEXT NOT NULL,
        is_active  INTEGER NOT NULL DEFAULT 1,
        updated_at TEXT NOT NULL
    )
''')

    cur.execute('SELECT COUNT(*) FROM notices')
    if cur.fetchone()[0] == 0:
        default_notices = [
            ('유니버스 서비스 오픈 안내',   '안녕하세요. 유니버스 Mafia GO! 서비스가 정식 오픈하였습니다. 많은 이용 부탁드립니다.', '2024-01-15'),
            ('개인정보 처리방침 개정 안내', '개인정보 처리방침이 일부 개정되었습니다. 자세한 내용을 확인해 주세요.',               '2024-01-10'),
            ('시스템 점검 안내 (1월 20일)', '1월 20일 오전 2시~4시 시스템 점검이 진행될 예정입니다. 이용에 참고 부탁드립니다.',   '2024-01-08'),
        ]
        cur.executemany('INSERT INTO notices (title, content, created) VALUES (?, ?, ?)', default_notices)

    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_active_nickname(player_id):
    db = get_db()
    row = db.execute(
        'SELECT nickname FROM online_nicknames WHERE player_id = ? AND is_active = 1',
        (player_id,)
    ).fetchone()
    db.close()
    return row['nickname'] if row else None

def is_nickname_in_use(nickname, exclude_player_id=None):
    db = get_db()

    if exclude_player_id:
        row = db.execute(
            '''
            SELECT 1
            FROM online_nicknames
            WHERE nickname = ? AND is_active = 1 AND player_id != ?
            LIMIT 1
            ''',
            (nickname, exclude_player_id)
        ).fetchone()
    else:
        row = db.execute(
            '''
            SELECT 1
            FROM online_nicknames
            WHERE nickname = ? AND is_active = 1
            LIMIT 1
            ''',
            (nickname,)
        ).fetchone()

    db.close()
    return row is not None

def save_or_activate_nickname(player_id, nickname):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    db = get_db()
    db.execute(
        '''
        INSERT INTO online_nicknames (player_id, nickname, is_active, updated_at)
        VALUES (?, ?, 1, ?)
        ON CONFLICT(player_id) DO UPDATE SET
            nickname = excluded.nickname,
            is_active = 1,
            updated_at = excluded.updated_at
        ''',
        (player_id, nickname, now)
    )
    db.commit()
    db.close()

def deactivate_nickname(player_id):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    db = get_db()
    db.execute(
        '''
        UPDATE online_nicknames
        SET is_active = 0, updated_at = ?
        WHERE player_id = ?
        ''',
        (now, player_id)
    )
    db.commit()
    db.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@app.context_processor
def inject_site_name():
    is_admin = session.get('user') in ADMIN_USERS
    return dict(site_name=SITE_NAME, is_admin=is_admin)

# ===== 라우트 =====

@app.route('/')
def index():
    db = get_db()
    notices = db.execute('SELECT * FROM notices ORDER BY id DESC LIMIT 3').fetchall()
    db.close()
    return render_template('index.html', notices=notices,
                           ad_panorama=AD_PANORAMA,
                           hero_animation=HERO_ANIMATION, hero_title=HERO_TITLE)

@app.route('/ai-chat')
def ai_chat():
    return render_template('ai_chat.html')

@app.route('/ai-chat/chat', methods=['POST'])
def ai_chat_api():
    user_ip = request.remote_addr
    today = str(date.today())

    if user_ip not in usage:
        usage[user_ip] = {}

    if today not in usage[user_ip]:
        usage[user_ip][today] = 0

    if usage[user_ip][today] >= 20:
        return jsonify({
            "reply": "⚠️ 하루 사용량 20회를 초과했어요. 내일 다시 시도해주세요."
        })

    if not OPENAI_API_KEY:
        return jsonify({
            "reply": "서비스 점검중입니다. 나중에 다시 시도해주십시오."
        }), 500

    data = request.get_json(silent=True) or {}
    messages = data.get("messages", [])

    if not isinstance(messages, list):
        return jsonify({
            "reply": "⚠️ messages 형식이 올바르지 않아요."
        }), 400

    if not messages or messages[0].get("role") != "system":
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages

    usage[user_ip][today] += 1

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
        )

        reply = completion.choices[0].message.content or ""
        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({
            "reply": f"⚠️ OpenAI 호출 실패: {str(e)}"
        }), 500

# ===== 사이트 이름 설정 =====
SITE_NAME = "Universe Studio"   # 네비게이션, 푸터 로고에 표시되는 이름

# ===== 히어로 타이틀 설정 =====
HERO_TITLE = "Mafia GO!"     # 회색 박스 안에 표시되는 이름

# ===== 스토어 아이템 설정 =====
# 아이템 추가/수정은 여기서만 하세요.
# payment: 'points'=포인트 전용 / 'cash'=현금 전용 / 'both'=둘 다
# original_price: 정가 (줄긋기 표시용, None이면 미표시)
# badge: 상품 뱃지 텍스트 (None이면 미표시)
STORE_ITEMS = [
    {
        'id': 1,
        'name': '초보자 패키지',
        'icon': '🌱',
        'original_price': 6900,
        'cash_price': 4900,
        'points_price': None,
        'payment': 'cash',
        'category': '패키지',
        'badge': '할인',
        'benefits': [
            '영웅 캐릭터 1종 무료 (선택)',
            '광고 1주일 동안 없음',
            '골드 5,000',
            '유니버스 포인트 +5,000',
            '"영광" 칭호 획득',
            '파란색 프로필 테두리 획득',
        ],
    },
    {
        'id': 2,
        'name': '고수 패키지',
        'icon': '⚔️',
        'original_price': 12900,
        'cash_price': 10900,
        'points_price': None,
        'payment': 'cash',
        'category': '패키지',
        'badge': '인기',
        'benefits': [
            '전설 캐릭터 1종 무료 (선택)',
            '광고 1달 동안 없음',
            '골드 30,000',
            '유니버스 포인트 +30,000',
            '"초월" 칭호 획득',
            '빛나는 프로필 테두리 획득',
        ],
    },
    {
        'id': 3,
        'name': 'VIP 패키지',
        'icon': '👑',
        'original_price': None,
        'cash_price': 10900,
        'points_price': None,
        'payment': 'cash',
        'category': '패키지',
        'badge': '월정액',
        'benefits': [
            '골드 +50,000 (결제마다)',
            '유니버스 포인트+ 가입 자격',
            '광고 없음',
            '"VIP" 칭호 획득',
            '골드 스킨 획득 (첫 결제 시)',
            '금색 VIP 프로필 테두리 획득 (첫 결제 시)',
        ],
    },
    {
        'id': 4,
        'name': '계정 초성장 패키지',
        'icon': '🚀',
        'original_price': None,
        'cash_price': 15900,
        'points_price': None,
        'payment': 'cash',
        'category': '패키지',
        'badge': 'BEST',
        'benefits': [
            '희귀·영웅 캐릭터 모두 잠금 해제',
            '골드 +40,000',
            '유니버스 포인트+ 가입 자격',
            '광고 없음',
            '"성장" 칭호 획득',
            '식물 프로필 테두리 획득',
        ],
    },
]
# 1사이클 = 위에서 날아오기(0.5초) + 머무기(2.5초) + 왼쪽으로 사라지기(0.5초) = 총 3.5초
# 반복 사이에 잠깐 숨어있는 시간 0.5초 포함 → 총 주기 4초
HERO_ANIMATION = """
<style>
@keyframes heroLoop {
    0%                         { transform: translateX(160px);  opacity: 0; }  /* 시작: 오른쪽에서 */
    12.5%                      { transform: translateX(0);      opacity: 1; }  /* 0.5초: 제자리 도착 */
    75%                        { transform: translateX(0);      opacity: 1; }  /* 3.0초: 머무는 중 */
    87.5%                      { transform: translateX(-160px); opacity: 0; }  /* 3.5초: 왼쪽으로 사라짐 */
    87.6%, 100%                { transform: translateX(160px);  opacity: 0; }  /* 대기 후 다시 오른쪽으로 */
}
.hero-inner-box {
    animation: heroLoop 4s ease infinite;
}
</style>
"""

@app.route('/company')
def company():
    return render_template('company.html')

@app.route('/company/greeting')
def greeting():
    return render_template('greeting.html')

@app.route('/company/principles')
def principles():
    return render_template('principles.html')

@app.route('/company/info')
def company_info():
    return render_template('company_info.html')

@app.route('/notices/write', methods=['GET', 'POST'])
def notice_write():
    if session.get('user') not in ADMIN_USERS:
        flash('관리자만 접근할 수 있습니다.', 'error')
        return redirect(url_for('notices_list'))
    if request.method == 'POST':
        title   = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        if not title or not content:
            flash('제목과 내용을 모두 입력해주세요.', 'error')
            return render_template('notice_write.html')
        db = get_db()
        db.execute(
            'INSERT INTO notices (title, content, created) VALUES (?, ?, ?)',
            (title, content, datetime.now().strftime('%Y-%m-%d'))
        )
        db.commit()
        db.close()
        flash('공지사항이 등록되었습니다.', 'success')
        return redirect(url_for('notices_list'))
    return render_template('notice_write.html')

@app.route('/notices/delete/<int:notice_id>', methods=['POST'])
def notice_delete(notice_id):
    if session.get('user') not in ADMIN_USERS:
        flash('관리자만 삭제할 수 있습니다.', 'error')
        return redirect(url_for('notices_list'))
    db = get_db()
    db.execute('DELETE FROM notices WHERE id = ?', (notice_id,))
    db.commit()
    db.close()
    flash('공지사항이 삭제되었습니다.', 'success')
    return redirect(url_for('notices_list'))

@app.route('/notices')
def notices_list():
    db = get_db()
    notices = db.execute('SELECT * FROM notices ORDER BY id DESC').fetchall()
    db.close()
    return render_template('notices.html', notices=notices)

@app.route('/notices/<int:notice_id>')
def notice_detail(notice_id):
    db = get_db()
    notice = db.execute('SELECT * FROM notices WHERE id = ?', (notice_id,)).fetchone()
    db.close()
    if not notice:
        return redirect(url_for('notices_list'))
    return render_template('notice_detail.html', notice=notice)

@app.route('/complaint')
def complaint():
    return render_template('complaint.html')

@app.route('/complaint/intro')
def complaint_intro():
    return render_template('complaint_intro.html')

@app.route('/complaint/purpose')
def complaint_purpose():
    return render_template('complaint_purpose.html')

@app.route('/complaint/process')
def complaint_process():
    return render_template('complaint_process.html')

@app.route('/complaint/write', methods=['GET', 'POST'])
def complaint_write():
    if request.method == 'POST':
        username = session.get('user', '비회원')
        category = request.form.get('category', '')
        title    = request.form.get('title', '')
        content  = request.form.get('content', '')
        created  = datetime.now().strftime('%Y-%m-%d')

        if not category or not title or not content:
            flash('모든 항목을 입력해주세요.', 'error')
            return render_template('complaint_write.html')

        db = get_db()
        db.execute(
            'INSERT INTO complaints (username, category, title, content, created) VALUES (?, ?, ?, ?, ?)',
            (username, category, title, content, created)
        )
        db.commit()
        db.close()

        flash('민원이 성공적으로 접수되었습니다.', 'success')
        return redirect(url_for('complaint'))
    return render_template('complaint_write.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/sitemap')
def sitemap():
    pages = [
        {'category': '메인', 'links': [
            {'name': '홈', 'url': '/'},
        ]},
        {'category': '회사 소개', 'links': [
            {'name': '회사 소개', 'url': '/company'},
            {'name': '경영진 인사말', 'url': '/company/greeting'},
            {'name': '운영 원칙', 'url': '/company/principles'},
            {'name': '회사 정보', 'url': '/company/info'},
        ]},
        {'category': '공지사항', 'links': [
            {'name': '공지사항 목록', 'url': '/notices'},
        ]},
        {'category': '민원 신청', 'links': [
            {'name': '민원 안내', 'url': '/complaint'},
            {'name': '민원 소개', 'url': '/complaint/intro'},
            {'name': '민원의 목적', 'url': '/complaint/purpose'},
            {'name': '민원의 처리과정', 'url': '/complaint/process'},
            {'name': '민원 작성', 'url': '/complaint/write'},
        ]},
        {'category': '개인정보', 'links': [
            {'name': '개인정보 처리방침', 'url': '/privacy'},
        ]},
        {'category': '계정', 'links': [
            {'name': '개발자 모드', 'url': '/developer'},
        ]},
    ]
    return render_template('sitemap.html', pages=pages)

@app.route('/developer', methods=['GET', 'POST'])
def developer_mode():
    if request.method == 'POST':
        password = request.form.get('password')

        if password == "DevMafia!2026#X7Q9":
            session['user'] = 'admin'
            return redirect(url_for('admin_users'))  # ← 여기 중요
        else:
            flash('비밀번호가 올바르지 않습니다.', 'error')

    return render_template('developer.html')

@app.route('/admin/members/delete/<int:user_id>', methods=['POST'])

def admin_delete_member(user_id):
    if session.get('user') not in ADMIN_USERS:
        flash('관리자만 접근할 수 있습니다.', 'error')
        return redirect(url_for('index'))
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        flash('존재하지 않는 계정입니다.', 'error')
        db.close()
        return redirect(url_for('admin_members'))
    if user['username'] == 'admin':
        flash('admin 계정은 삭제할 수 없습니다.', 'error')
        db.close()
        return redirect(url_for('admin_members'))
    db.execute('DELETE FROM users WHERE id = ?', (user_id,))
    db.execute('DELETE FROM rewards WHERE username = ?', (user['username'],))
    db.execute('DELETE FROM purchases WHERE username = ?', (user['username'],))
    db.commit()
    db.close()
    flash(f'[{user["username"]}] 계정이 삭제되었습니다.', 'success')
    return redirect(url_for('admin_members'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('developer_mode', None)
    flash('로그아웃 되었습니다.', 'success')
    return redirect(url_for('index'))

# ================================================================
# ★ 게임 엔진 통합 (모든 경로는 /game 하위)
# ================================================================
from flask_socketio import SocketIO, join_room
import random, string, time, uuid
from collections import Counter

socketio = SocketIO(app, cors_allowed_origins="*")

# ── 온라인 상태 ──
servers          = {}
invite_ips       = {}
heartbeats       = {}
g_roles          = {}
g_killed         = {}
g_saved          = {}
g_arrested       = {}
dead_players     = {}
night_phase      = {}
night_results    = {}
result_confirmed = {}
day_votes        = {}
ready_players    = {}
HEARTBEAT_TIMEOUT = 3

# ── 오프라인 상태 ──
offline_games = {}

def get_player_id():
    if 'player_id' not in session:
        session['player_id'] = str(uuid.uuid4())
    return session['player_id']

def game_online_home():
    player_id = get_player_id()

    if request.method == 'POST':
        nickname = request.form.get('nickname', '').strip()

        # 빈 닉네임 방지
        if not nickname:
            return render_online_shell(
                "오류",
                "닉네임을 입력해주세요.",
                '''
                <div class="note">닉네임이 비어 있습니다.</div>
                <div style="text-align:center; margin-top:20px;">
                    <button class="action-btn btn-red" onclick="location.href='/game/online'">
                        다시 입력
                    </button>
                </div>
                '''
            )

        # 이미 내가 닉네임을 가지고 있으면 새로 생성 불가
        if player_id in active_nicknames:
            current_nickname = active_nicknames[player_id]
            return render_online_shell(
                "오류",
                "이미 닉네임이 등록되어 있습니다.",
                f'''
                <div class="note">현재 닉네임: <b>{current_nickname}</b></div>
                <div style="text-align:center; margin-top:20px;">
                    <button class="action-btn btn-red" onclick="location.href='/game/online'">
                        돌아가기
                    </button>
                </div>
                '''
            )

        # 다른 사람이 같은 닉네임을 쓰고 있는지 확인
        if nickname in active_nicknames.values():
            return render_online_shell(
                "오류",
                "이미 사용 중인 닉네임입니다.",
                f'''
                <div class="note">[{nickname}] 은(는) 이미 다른 플레이어가 사용 중입니다.</div>
                <div style="text-align:center; margin-top:20px;">
                    <button class="action-btn btn-red" onclick="location.href='/game/online'">
                        다시 입력
                    </button>
                </div>
                '''
            )

        # 닉네임 등록
        session['game_nickname'] = nickname
        session['use_ip_mode'] = False

        return redirect('/game/online')

    current_name = (session.get('game_nickname') or '').strip()

    status = (
        f'<div style="text-align:center; margin-top:14px; color:#dbeafe; font-size:18px;">'
        f'현재 닉네임: <b style="color:#fff">{current_name}</b>'
        f'</div>'
        if current_name
        else '<div style="text-align:center; margin-top:14px; color:#dbeafe; font-size:18px;">현재 닉네임 없음</div>'
    )

    inner_html = f'''
        <div class="status-box">
            {status}
        </div>

        <div class="section-title">Nickname</div>
        <div class="form-box">
            <form method="POST" style="display:grid; gap:14px;">
                <input class="input" name="nickname" placeholder="닉네임 입력" maxlength="20">
                <button class="action-btn btn-blue" type="submit">닉네임 저장</button>
            </form>
        </div>

        <div class="section-title" style="margin-top:24px;">Game Mode</div>
        <div class="card-grid">
            <button class="action-btn btn-blue" onclick="location.href='/game/create_code'">초대코드 만들기</button>
            <button class="action-btn btn-purple" onclick="location.href='/game/join_code'">초대코드로 참여</button>
            <button class="action-btn btn-green" onclick="location.href='/game/create_server'">서버 만들기</button>
            <button class="action-btn btn-orange" onclick="location.href='/game/online_join'">서버 목록</button>
        </div>
    '''

    return render_online_shell(
        "온라인 게임 입장",
        "닉네임을 정한 뒤, 초대코드나 서버 목록으로 들어갈 수 있어요.",
        inner_html
    )

def generate_code():
    while True:
        length = random.randint(6, 8)
        chars = string.ascii_uppercase + string.digits
        code = ''.join(random.choice(chars) for _ in range(length))
        if code not in invite_ips:
            return code

import time

def get_active_players(code):
    now = time.time()
    active = []

    if code not in heartbeats:
        return active

    for player_id, last_seen in list(heartbeats[code].items()):
        if now - last_seen < HEARTBEAT_TIMEOUT:
            active.append(player_id)
        else:
            del heartbeats[code][player_id]

            if code in invite_ips and player_id in invite_ips[code]:
                invite_ips[code].remove(player_id)

            # 닉네임은 메모리 삭제가 아니라 DB 비활성화
            deactivate_nickname(player_id)

    return active

def reset_online_game(code):
    invite_ips[code]   = []
    g_roles[code]      = {}
    dead_players[code] = []
    g_killed.pop(code, None)
    g_saved.pop(code, None)
    g_arrested.pop(code, None)
    night_phase.pop(code, None)
    night_results.pop(code, None)
    result_confirmed.pop(code, None)
    day_votes.pop(code, None)
    heartbeats[code]   = {}
    ready_players[code] = set()

def check_victory(code):
    all_players   = invite_ips.get(code, [])
    dead          = dead_players.get(code, [])
    survivors     = [p for p in all_players if p not in dead]
    mafia_alive   = [p for p in survivors if g_roles.get(code, {}).get(p) == "마피아"]
    citizen_alive = [p for p in survivors if g_roles.get(code, {}).get(p) != "마피아"]
    if len(mafia_alive) == 0:                 return "citizen_win"
    if len(mafia_alive) >= len(citizen_alive): return "mafia_win"
    return None

SOCKETIO_SCRIPT = '<script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>'

def ingame_socket_js(code):
    return f"""{SOCKETIO_SCRIPT}
    <script>
        var socket = io();
        socket.emit("join_room", {{code: "{code}"}});

        function sendHeartbeat() {{
            socket.emit("heartbeat", {{code: "{code}"}});
        }}

        sendHeartbeat();
        setInterval(sendHeartbeat, 3000);

        socket.on("game_abort", function() {{
            alert("참여 인원이 부족하여 게임이 중단되었습니다.");
            window.location.href = "/game/join/{code}";
        }});
    </script>
    """

def game_top_bar():
    player = (session.get('game_nickname') or session.get('user') or '').strip()
    if player:
        return f'<div style="position:absolute;top:10px;right:10px;font-size:18px">{player}</div>'
    return ""

def back_button_g(href="/game", label="게임 메인으로"):
    return f'<div style="text-align:center;margin-top:30px"><button onclick="location.href=\'{href}\'" style="padding:20px;font-size:20px">{label}</button></div>'

def waiting_room_html(title, code, start_url):
    print("WAITING_ROOM_HTML USED")
    print("title =", title)

    count = len(get_active_players(code))
    my_id = (session.get('game_nickname') or get_player_id())
    disabled_attr = "disabled" if count < 4 else ""
    status_txt = "4명 이상이면 게임을 시작할 수 있습니다." if count < 4 else "게임 시작 준비를 할 수 있습니다!"

    return f"""
    <h1 style="text-align:center; color:#4CAF50; font-size:36px; margin-top:20px;">
        {title}
    </h1>

    <h3 style="text-align:center; color:#888;">서버 코드: {code}</h3>

    <p style="text-align:center;color:#0066cc;font-size:16px">
        나는 <b>{my_id}</b> 으로 표시됩니다
    </p>

    <h3 id="count" style="text-align:center">현재 접속 인원: {count}명</h3>
    <h4 id="status" style="text-align:center;color:gray">{status_txt}</h4>

    <div style="text-align:center">
        <button id="start_btn" onclick="readyStart()"
            style="padding:20px;font-size:20px;cursor:pointer" {disabled_attr}>
            게임 시작
        </button>
    </div>

    <script>
        function sendHeartbeat() {{
            fetch("/game/heartbeat/{code}", {{method:"POST"}});
        }}

        function updateCount() {{
            fetch("/game/player_count/{code}")
            .then(r => r.json())
            .then(data => {{
                var c = data.count;
                document.getElementById("count").innerText = "현재 접속 인원: " + c + "명";

                var btn = document.getElementById("start_btn");

                if (c >= 4) {{
                    btn.disabled = false;
                    btn.style.opacity = "1";
                    document.getElementById("status").innerText = "게임 시작 준비를 할 수 있습니다!";
                    document.getElementById("status").style.color = "green";
                }} else {{
                    btn.disabled = true;
                    btn.style.opacity = "0.4";
                    document.getElementById("status").innerText = "4명 이상이면 게임을 시작할 수 있습니다. (" + c + "/4)";
                    document.getElementById("status").style.color = "gray";
                }}
            }});
        }}

        function readyStart() {{
            fetch("/game/ready_start/{code}", {{method:"POST"}})
            .then(r => r.json())
            .then(data => {{
                if (data.started) {{
                    location.href = "/game/start/{code}";
                }} else {{
                    document.getElementById("status").innerText =
                        "시작 준비 중... (" + data.ready + "/" + data.total + ")";
                    document.getElementById("status").style.color = "orange";
                }}
            }});
        }}

        function checkStartState() {{
            fetch("/game/start_state/{code}")
            .then(r => r.json())
            .then(data => {{
                if (data.started) {{
                    location.href = "/game/start/{code}";
                }} else if (data.total >= 4) {{
                    document.getElementById("status").innerText =
                        "게임 시작 준비: " + data.ready + "/" + data.total;
                    document.getElementById("status").style.color = "orange";
                }}
            }});
        }}

        sendHeartbeat();
        setInterval(sendHeartbeat, 1000);

        updateCount();
        setInterval(updateCount, 1000);

        checkStartState();
        setInterval(checkStartState, 1000);
    </script>
    """

# ── 오프라인 ──
def init_offline_game(player_count):
    role_list = ["🔫 마피아","👮 경찰","🧑‍⚕️ 의사"] + ["👨 시민"]*(player_count-3)
    random.shuffle(role_list)
    return {"players":player_count,"roles":role_list,"alive":[True]*player_count,"dead":[],
            "night_step":"mafia","mafia_target":None,"doctor_target":None,"police_target":None,
            "votes":[0]*player_count,"night_deaths":[],"night_saves":[],"role_index":0}

@app.route('/game')
def game_home():
    return render_template('game_home.html', top_bar=game_top_bar())

@app.route('/game/offline')
def game_offline():
    return render_template('game_offline.html')

@app.route('/api/offline/start', methods=['POST'])
def offline_start():
    data  = request.get_json()
    count = int(data.get("player_count", 6))
    if not (4 <= count <= 20):
        return jsonify({"error":"플레이어 수는 4~20명이어야 합니다."}), 400
    gid = str(uuid.uuid4())
    offline_games[gid] = init_offline_game(count)
    session["offline_game_id"] = gid
    return jsonify({"status":"ok","game_id":gid,"players":count})

@app.route('/api/offline/role/<int:index>')
def offline_role(index):
    gid  = session.get("offline_game_id")
    game = offline_games.get(gid)
    if not game: return jsonify({"error":"게임 없음"}), 404
    if index < 0 or index >= game["players"]: return jsonify({"error":"범위 초과"}), 400
    return jsonify({"role":game["roles"][index],"player":index+1})

@app.route('/api/offline/night/select', methods=['POST'])
def offline_night_select():
    gid  = session.get("offline_game_id")
    game = offline_games.get(gid)
    if not game: return jsonify({"error":"게임 없음"}), 404
    data   = request.get_json()
    target = int(data.get("target"))
    step   = game["night_step"]
    if step == "mafia":
        game["mafia_target"]  = target; game["night_step"] = "doctor"
        return jsonify({"status":"ok","next_step":"doctor"})
    elif step == "doctor":
        game["doctor_target"] = target; game["night_step"] = "police"
        return jsonify({"status":"ok","next_step":"police"})
    elif step == "police":
        game["police_target"] = target; game["night_step"] = "done"
        mt=game["mafia_target"]; dt=game["doctor_target"]; pt=game["police_target"]
        game["night_deaths"]=[]; game["night_saves"]=[]
        if mt != dt:
            game["alive"][mt]=False
            if (mt+1) not in game["dead"]: game["dead"].append(mt+1)
            game["night_deaths"].append(mt+1)
        else:
            game["night_saves"].append(dt+1)
        pr = "성공" if "마피아" in game["roles"][pt] else "실패"
        ma = sum(1 for i in range(game["players"]) if game["alive"][i] and "마피아" in game["roles"][i])
        ci = sum(1 for i in range(game["players"]) if game["alive"][i] and "마피아" not in game["roles"][i])
        win = "citizen" if ma==0 else ("mafia" if ma>=ci else None)
        return jsonify({"deaths":game["night_deaths"],"saves":game["night_saves"],"police":pr,"win":win})
    return jsonify({"error":"잘못된 단계"}), 400

@app.route('/api/offline/vote/start', methods=['POST'])
def offline_vote_start():
    gid  = session.get("offline_game_id")
    game = offline_games.get(gid)
    if not game: return jsonify({"error":"게임 없음"}), 404
    game["votes"] = [0]*game["players"]
    vi = 0
    while vi < game["players"] and not game["alive"][vi]: vi += 1
    game["vote_index"] = vi
    return jsonify({"status":"ok","current_voter": vi+1 if vi < game["players"] else None})

@app.route('/api/offline/vote/cast', methods=['POST'])
def offline_vote_cast():
    gid  = session.get("offline_game_id")
    game = offline_games.get(gid)
    if not game: return jsonify({"error":"게임 없음"}), 404
    data   = request.get_json()
    target = int(data.get("target"))
    game["votes"][target] += 1
    vi = game["vote_index"]+1
    while vi < game["players"] and not game["alive"][vi]: vi += 1
    game["vote_index"] = vi
    if vi >= game["players"]:
        max_v = max(game["votes"])
        targets = [i for i,v in enumerate(game["votes"]) if v==max_v]
        if len(targets) > 1:
            result = {"tie":True,"eliminated":None}
        else:
            t = targets[0]; game["alive"][t]=False
            if (t+1) not in game["dead"]: game["dead"].append(t+1)
            result = {"tie":False,"eliminated":t+1}
        ma = sum(1 for i in range(game["players"]) if game["alive"][i] and "마피아" in game["roles"][i])
        ci = sum(1 for i in range(game["players"]) if game["alive"][i] and "마피아" not in game["roles"][i])
        result["win"] = "citizen" if ma==0 else ("mafia" if ma>=ci else None)
        game["night_step"]="mafia"; game["mafia_target"]=None; game["doctor_target"]=None; game["police_target"]=None
        return jsonify(result)
    return jsonify({"status":"ok","current_voter":vi+1})

@app.route('/api/offline/state')
def offline_state():
    gid  = session.get("offline_game_id")
    game = offline_games.get(gid)
    if not game: return jsonify({"error":"게임 없음"}), 404
    return jsonify({"players":game["players"],"alive":game["alive"],"dead":game["dead"],"night_step":game["night_step"]})

# ── Socket.IO ──
@socketio.on("join_room")
def on_join(data):
    code = data.get("code")
    if code: join_room(code)

@socketio.on("chat_message")
def on_chat(data):
    code = data.get("code")
    player_id = get_player_id()
    sender = (session.get("game_nickname") or player_id)
    msg  = data.get("msg","").strip()[:200]
    if not code or not msg:
        return
    socketio.emit("chat_message", {"ip": player_id, "name": sender, "msg": msg}, room=code)

@socketio.on("heartbeat")
def on_heartbeat(data):
    code = data.get("code")
    player_id = get_player_id()
    if not code:
        return
    if code not in heartbeats:
        heartbeats[code] = {}
    heartbeats[code][player_id] = time.time()
    if code in invite_ips and invite_ips[code]:
        if night_phase.get(code) == "done":
            return
        now = time.time()
        all_online = [p for p in invite_ips[code] if (now - heartbeats.get(code, {}).get(p, 0)) < HEARTBEAT_TIMEOUT]
        if len(all_online) < 4:
            reset_online_game(code)
            socketio.emit("game_abort", {}, room=code)

@socketio.on("confirm_result")
def on_confirm_result(data):
    code = data.get("code")
    player_id = get_player_id()
    if not code:
        return
    if code not in result_confirmed:
        result_confirmed[code] = set()
    result_confirmed[code].add(player_id)
    survivors = [p for p in invite_ips.get(code, []) if p not in dead_players.get(code, [])]
    confirmed = result_confirmed.get(code, set())
    all_confirmed = all(p in confirmed for p in survivors)
    socketio.emit("confirm_update", {"confirmed": len(confirmed), "total": len(survivors), "all_confirmed": all_confirmed}, room=code)

@socketio.on("cast_vote")
def on_cast_vote(data):
    code = data.get("code")
    target = data.get("target")
    player_id = get_player_id()
    if not code or not target:
        return
    if code not in day_votes:
        day_votes[code] = {}
    day_votes[code][player_id] = target
    survivors = [p for p in invite_ips.get(code, []) if p not in dead_players.get(code, [])]
    voted = [p for p in survivors if p in day_votes.get(code, {})]
    socketio.emit("vote_update", {"voted": len(voted), "total": len(survivors)}, room=code)
    if len(voted) == len(survivors):
        tally = Counter(day_votes[code][p] for p in survivors)
        max_votes = max(tally.values())
        top = [p for p, v in tally.items() if v == max_votes]
        exiled = top[0] if len(top) == 1 else None
        if exiled:
            if code not in dead_players:
                dead_players[code] = []
            dead_players[code].append(exiled)
            msg = f"{exiled}이(가) 추방되었습니다! ({max_votes}표)"
        else:
            msg = "동률로 아무도 추방되지 않았습니다."
        day_votes.pop(code, None)
        v = check_victory(code)
        if v == "citizen_win":
            socketio.emit("vote_result", {"msg": msg, "exiled": exiled, "victory": "citizen"}, room=code)
        elif v == "mafia_win":
            socketio.emit("vote_result", {"msg": msg, "exiled": exiled, "victory": "mafia"}, room=code)
        else:
            night_phase[code] = "mafia"
            socketio.emit("vote_result", {"msg": msg, "exiled": exiled, "victory": None}, room=code)

# ── 온라인 HTTP ──
# ── 온라인 HTTP ──
@app.route('/game/ad-gate')
def game_ad_gate():
    next_url = request.args.get('next', '/game/online')
    return render_template('game_ad_gate.html', next_url=next_url)

@app.route('/game/online', methods=['GET'])
def game_online_home():
    player_id = get_player_id()
    use_ip_mode = session.get('use_ip_mode', False)

    current_name = (session.get('game_nickname') or '').strip()

    # 🔥 핵심: 닉네임도 없고 IP 모드도 아니면 닉네임 페이지로
    if not current_name and not use_ip_mode:
        return redirect('/game/nickname')

    # 🔥 상태 표시
    if current_name:
        status = f'''
        <div style="text-align:center; margin-top:14px; color:#dbeafe; font-size:18px;">
            현재 닉네임: <b style="color:#fff">{current_name}</b>
        </div>
        '''
    elif use_ip_mode:
        status = '''
        <div style="text-align:center; margin-top:14px; color:#dbeafe; font-size:18px;">
            현재 방식: <b style="color:#fff">IP로 플레이</b>
        </div>
        '''
    else:
        status = '''
        <div style="text-align:center; margin-top:14px; color:#dbeafe; font-size:18px;">
            현재 닉네임 없음
        </div>
        '''

    # 🔥 UI 구성
    inner_html = f'''
        <div class="status-box">
            {status}
        </div>

        <div class="section-title">Game Mode</div>
        <div class="card-grid">

            <button class="action-btn btn-blue"
                onclick="location.href='/game/create_code'">
                초대코드 만들기
            </button>

            <button class="action-btn btn-purple"
                onclick="location.href='/game/join_code'">
                초대코드로 참여
            </button>

            <button class="action-btn btn-green"
                onclick="location.href='/game/create_server'">
                서버 만들기
            </button>

            <button class="action-btn btn-orange"
                onclick="location.href='/game/online_join'">
                서버 목록
            </button>

        </div>

        <div class="section-title" style="margin-top:24px;">Player</div>
        <div class="form-box">

            <button class="action-btn btn-blue"
                onclick="location.href='/game/nickname'">
                닉네임 설정 / 변경
            </button>

        </div>
    '''

    return render_online_shell(
        "온라인 게임 입장",
        "환상적인 플레이를 즐겨보세요!",
        inner_html
    )
@app.route('/game/create_server', methods=['GET', 'POST'])
def game_create_server():
    if request.method == 'POST':
        code = generate_code()
        name = request.form.get('server_name', '서버').strip()

        if not name:
            name = f"서버 {code}"

        reset_online_game(code)
        server_names[code] = name
        session['current_code'] = code

        return redirect(f'/game/join/{code}')

    inner_html = '''
        <form method="POST" class="form-box">
            <input class="input" name="server_name" placeholder="서버 이름">
            <button class="action-btn btn-green" type="submit">서버 만들기</button>
        </form>
    '''

    return render_online_shell(
        "서버 만들기",
        "새 서버를 생성합니다.",
        inner_html
    )

@app.route('/game/heartbeat/<code>', methods=['POST'])

def game_heartbeat(code):
    ip = get_player_id()
    if code not in heartbeats: heartbeats[code] = {}
    heartbeats[code][ip] = time.time()
    return jsonify({"ok":True})

@app.route('/game/player_count/<code>')
def player_count(code):
    count = len(get_active_players(code))
    return jsonify({"count": count})

@app.route('/game/ready_start/<code>', methods=['POST'])
def game_ready_start(code):
    ip = get_player_id()

    if code not in invite_ips:
        return jsonify({"error": "no room"}), 404

    active = get_active_players(code)

    if len(active) < 4:
        return jsonify({
            "started": False,
            "ready": 0,
            "total": len(active)
        })

    if code not in ready_players:
        ready_players[code] = set()

    ready_players[code].add(ip)

    ready_count = len([p for p in active if p in ready_players[code]])
    started = all(p in ready_players[code] for p in active)

    return jsonify({
        "started": started,
        "ready": ready_count,
        "total": len(active)
    })


@app.route('/game/start_state/<code>')
def game_start_state(code):
    active = get_active_players(code)

    if code not in ready_players:
        ready_players[code] = set()

    ready_count = len([p for p in active if p in ready_players[code]])
    started = len(active) >= 4 and all(p in ready_players[code] for p in active)

    return jsonify({
        "started": started,
        "ready": ready_count,
        "total": len(active)
    })

@app.route('/game/my_result/<code>')
def game_my_result(code):
    ip = get_player_id()
    return jsonify({"dead":ip in dead_players.get(code,[])})

@app.route('/game/create_code')
def game_create_code():
    code = generate_code()

    reset_online_game(code)

    server_names[code] = f"방 {code}"

    return render_online_shell(
        "초대코드 생성",
        "코드를 공유하세요",
        f'''
        <div class="note">코드: <b>{code}</b></div>
        <button onclick="location.href='/game/join/{code}'"
            class="action-btn btn-blue">입장</button>
        '''
    )

@app.route('/game/join_code', methods=['GET'])
def game_join_code():
    inner_html = '''
        <form method="POST" action="/game/join_code_go" class="form-box">
            <input class="input" type="text" name="code" placeholder="초대코드 입력">
            <button class="action-btn btn-purple" type="submit">입장하기</button>
        </form>
        <div class="note">초대코드를 입력하면 해당 방으로 들어갑니다.</div>
    '''
    return render_online_shell(
        "초대코드로 참여",
        "받은 초대코드를 입력해서 방에 참여하세요.",
        inner_html
    )

@app.route('/game/join_code_go', methods=['POST'])
def game_join_code_go():
    code = request.form.get('code', '').strip().upper()

    if code not in invite_ips:
        return render_online_shell(
            "오류",
            "코드를 다시 확인해주십시오.",
            f'''
            <div class="note">입력한 초대코드가 올바르지 않습니다.</div>
            <div style="text-align:center; margin-top:20px;">
                <button class="action-btn btn-red" onclick="location.href='/game/join_code'">
                    다시 입력하기
                </button>
            </div>
            '''
        )

    return redirect(f'/game/join/{code}')

@app.route('/game/join/<code>')
def game_join(code):
    session['current_code'] = code
    ip = get_player_id()

    nickname = (session.get('game_nickname') or '').strip()
    use_ip_mode = session.get('use_ip_mode', False)

    if code not in invite_ips:
        return render_online_shell(
            "오류",
            "존재하지 않는 서버입니다.",
            "<div class='note'>코드를 확인해주세요.</div>"
        )

    # 닉네임도 없고 IP 모드도 아니면 nickname 페이지로
    if not nickname and not use_ip_mode:
        return render_online_shell(
            "오류",
            "플레이 방식이 설정되지 않았습니다.",
            '''
            <div class="note">닉네임을 설정하거나 IP로 플레이를 선택해주세요.</div>
            <div style="text-align:center; margin-top:20px;">
                <button class="action-btn btn-blue" onclick="location.href='/game/nickname'">
                    닉네임 설정으로 이동
                </button>
            </div>
            '''
        )

    # 닉네임 플레이라면 DB 활성화 유지
    if nickname:
        if is_nickname_in_use(nickname, exclude_player_id=ip):
            return render_online_shell(
                "오류",
                "이미 사용 중인 닉네임입니다.",
                f'''
                <div class="note">[{nickname}] 은(는) 이미 다른 플레이어가 사용 중입니다.</div>
                <div style="text-align:center; margin-top:20px;">
                    <button class="action-btn btn-red" onclick="location.href='/game/nickname'">
                        닉네임 다시 설정
                    </button>
                </div>
                '''
            )

        save_or_activate_nickname(ip, nickname)

    if ip not in invite_ips[code]:
        invite_ips[code].append(ip)

    if code not in heartbeats:
        heartbeats[code] = {}

    heartbeats[code][ip] = time.time()

    return redirect(f'/game/wait/{code}')

@app.route('/game/server_created', methods=['POST'])
def game_server_created():
    name = request.form["name"]
    servers[name]=[]; invite_ips[name]=[]; heartbeats[name]={}; g_roles[name]={}
    return f"""<h2 style="text-align:center">{name} 서버 생성됨</h2>
    <div style="text-align:center">
        <button onclick="location.href='/game/online_server/{name}'" style="padding:20px;font-size:20px">입장</button>
    </div>{back_button_g('/game/online','온라인 메뉴로')}"""

@app.route('/game/online_join')
def game_online_join():
    if not invite_ips:
        inner_html = '<div class="note">현재 서버가 없습니다.</div>'
    else:
        buttons = ""
        for code in invite_ips.keys():
            name = server_names.get(code, f"서버 {code}")
            buttons += f'''
            <button class="action-btn btn-blue"
                onclick="location.href='/game/join/{code}'">
                {name} ({code})
            </button>
            '''

        inner_html = f'<div class="card-grid">{buttons}</div>'

    return render_online_shell(
        "서버 목록",
        "현재 생성된 서버입니다.",
        inner_html
    )

@app.route('/game/online_server/<n>')
def game_online_server(n):
    ip = get_player_id()
    if n not in heartbeats: heartbeats[n] = {}
    heartbeats[n][ip] = time.time()
    return waiting_room_html(f"{n} 서버 참여 완료", n, f"/game/start/{n}")

@app.route('/game/wait/<code>')
def game_wait(code):
    real_code = session.get('current_code', code)

    print("URL code:", code)
    print("session code:", real_code)
    print("server_names:", server_names)

    name = server_names.get(real_code, f"서버 {real_code}")

    return waiting_room_html(
        name,
        real_code,
        f"/game/start/{real_code}"
    )

@app.route('/game/start/<code>')
def game_start(code):
    active = get_active_players(code)
    invite_ips[code] = active

    if code not in ready_players:
        ready_players[code] = set()

    if len(active) < 4:
        return f"""<h2 style="text-align:center">인원이 부족합니다 (현재 {len(active)}명 / 최소 4명)</h2>
        {back_button_g(f'/game/join/{code}','대기실로 돌아가기')}"""

    if not all(p in ready_players[code] for p in active):
        return f"""<h2 style="text-align:center">아직 모든 플레이어가 게임 시작을 누르지 않았습니다.</h2>
        {back_button_g(f'/game/wait/{code}','대기실로 돌아가기')}"""

    job_list = ["마피아", "경찰", "의사"]
    g_roles[code] = {}
    random.shuffle(active)

    for i, p in enumerate(active):
        g_roles[code][p] = job_list[i] if i < 3 else "시민"

    night_phase[code] = "mafia"
    ready_players[code] = set()

    role = g_roles[code].get(get_player_id(), "시민")

    return f"""<h1 id="role" style="text-align:center">직업</h1>
    <script>
        document.getElementById("role").innerText="{role}";
        setTimeout(function(){{document.getElementById("role").innerText="3"}},1000);
        setTimeout(function(){{document.getElementById("role").innerText="2"}},2000);
        setTimeout(function(){{document.getElementById("role").innerText="1"}},3000);
        setTimeout(function(){{document.getElementById("role").innerText="밤"}},4000);
        setTimeout(function(){{window.location.href="/game/night/{code}"}},5000);
    </script>"""

@app.route('/game/night/<code>')
def game_night(code):
    ip    = get_player_id()
    role  = g_roles.get(code,{}).get(ip,"시민")
    alive = [p for p in invite_ips.get(code,[]) if p not in dead_players.get(code,[])]
    phase = night_phase.get(code,"mafia")
    if phase == "done":
        return f"<script>location.href='/game/night_result/{code}'</script>"
    if phase == "mafia":
        if role == "마피아":
            html = f"<h1 style='text-align:center'>죽일 사람 선택</h1><div style='text-align:center'>"
            for p in alive:
                if p != ip: html += f"<br><a href='/game/kill/{code}/{p}'>{p}</a>"
            return html + f"</div>{ingame_socket_js(code)}"
        return f"<h1 style='text-align:center'>마피아 행동중...</h1>{ingame_socket_js(code)}"
    if phase == "doctor":
        if role == "의사":
            html = f"<h1 style='text-align:center'>살릴 사람 선택</h1><div style='text-align:center'>"
            for p in alive: html += f"<br><a href='/game/heal/{code}/{p}'>{p}</a>"
            return html + f"</div>{ingame_socket_js(code)}"
        return f"<h1 style='text-align:center'>의사 행동중...</h1>{ingame_socket_js(code)}"
    if phase == "police":
        if role == "경찰":
            html = f"<h1 style='text-align:center'>체포할 사람 선택</h1><div style='text-align:center'>"
            for p in alive:
                if p != ip: html += f"<br><a href='/game/arrest/{code}/{p}'>{p}</a>"
            return html + f"</div>{ingame_socket_js(code)}"
        return f"<h1 style='text-align:center'>경찰 행동중...</h1>{ingame_socket_js(code)}"
    return "<h1 style='text-align:center'>밤 종료</h1>"

@app.route('/game/kill/<code>/<target>')
def game_kill(code, target):
    g_killed[code]=target; night_phase[code]="doctor"
    return f"<script>location.href='/game/night/{code}'</script>"

@app.route('/game/heal/<code>/<target>')
def game_heal(code, target):
    g_saved[code]=target; night_phase[code]="police"
    return f"<script>location.href='/game/night/{code}'</script>"

@app.route('/game/arrest/<code>/<target>')
def game_arrest(code, target):
    g_arrested[code] = target
    dead_p = g_killed.get(code); healed = g_saved.get(code)
    if dead_p == healed:
        result = "의사가 살렸습니다."; dead_player = None
    else:
        result = f"{dead_p}이 공격당했습니다."; dead_player = dead_p
    if g_roles.get(code,{}).get(target) == "마피아":
        result += f" 경찰 수사 성공! {target}은(는) 마피아였습니다."
    else:
        result += f" 경찰 수사 실패. {target}은(는) 마피아가 아닙니다."
    if dead_player:
        if code not in dead_players: dead_players[code]=[]
        dead_players[code].append(dead_player)
    night_results[code]=result; night_phase[code]="done"
    socketio.emit("night_done",{},room=code)
    return f"<script>location.href='/game/night_result/{code}'</script>"

@app.route('/game/night_result/<code>')
def game_night_result(code):
    result    = night_results.get(code,"")
    survivors = [p for p in invite_ips.get(code,[]) if p not in dead_players.get(code,[])]
    total     = len(survivors)
    return f"""{SOCKETIO_SCRIPT}
    <h1 style="text-align:center">🌅 아침이 밝았습니다</h1>
    <h2 style="text-align:center">{result}</h2>
    <div style="text-align:center;margin-top:40px">
        <button id="confirm_btn" onclick="confirm_read()" style="padding:20px;font-size:20px">확인</button>
        <p id="wait_msg" style="margin-top:20px;font-size:16px;color:gray">0 / {total} 명 확인</p>
    </div>
    <script>
        var socket=io(); socket.emit("join_room",{{code:"{code}"}});
        var myConfirmed=false;
        socket.on("confirm_update",function(data){{
            document.getElementById("wait_msg").innerText=data.confirmed+" / "+data.total+" 명 확인";
            if(data.all_confirmed) goNext();
        }});
        socket.on("game_abort",function(){{
            alert("참여 인원이 부족하여 게임이 중단되었습니다. 대기실로 돌아갑니다.");
            window.location.href="/game/join/{code}";
        }});
        function confirm_read(){{
            if(myConfirmed)return; myConfirmed=true;
            document.getElementById("confirm_btn").disabled=true;
            document.getElementById("confirm_btn").innerText="확인 완료";
            socket.emit("confirm_result",{{code:"{code}"}});
        }}
        function goNext(){{
            fetch("/game/my_result/{code}").then(r=>r.json()).then(data=>{{
                if(data.dead){{window.location.href="/game/lose";}}
                else{{window.location.href="/game/discussion/{code}";}}
            }});
        }}
    </script>"""

@app.route('/game/discussion/<code>')
def game_discussion(code):
    ip = get_player_id()
    if ip in dead_players.get(code,[]):
        return "<script>location.href='/game/lose'</script>"
    v = check_victory(code)
    if v == "citizen_win": return f"<script>location.href='/game/victory/{code}/citizen'</script>"
    if v == "mafia_win":   return f"<script>location.href='/game/victory/{code}/mafia'</script>"
    survivors = [p for p in invite_ips.get(code,[]) if p not in dead_players.get(code,[])]
    my_role   = g_roles.get(code,{}).get(ip,"시민")
    html = f"""{SOCKETIO_SCRIPT}
    <h1 style="text-align:center">낮 토론</h1>
    <h3 style="text-align:center">마피아를 찾아 투표하세요</h3>
    <div style="text-align:center">현재 생존자<br><br>"""
    for p in survivors:
        if p == ip: html += f"<span style='color:gray'>{p} (나)</span><br>"
        else:       html += f"<a href='/game/vote/{code}' style='display:block;margin:6px;font-size:18px'>투표하러 가기 →</a>"
    html += f"""<br><small style="color:gray">내 역할: {my_role}</small></div>
    <hr style="margin:30px auto;width:60%">
    <div style="max-width:500px;margin:0 auto;padding:0 20px">
        <div id="chat_box" style="height:250px;overflow-y:auto;border:1px solid #ccc;padding:10px;font-size:15px;background:#f9f9f9;border-radius:8px"></div>
        <div style="display:flex;margin-top:10px;gap:8px">
            <input id="chat_input" placeholder="메시지 입력..." style="flex:1;padding:10px;font-size:15px;border:1px solid #ccc;border-radius:6px" onkeypress="if(event.key==='Enter')sendChat()">
            <button onclick="sendChat()" style="padding:10px 20px;font-size:15px;border-radius:6px">전송</button>
        </div>
    </div>
    <script>
        var socket=io(); socket.emit("join_room",{{code:"{code}"}});
        var myIp="{get_player_id()}";
        function sendHeartbeat(){{socket.emit("heartbeat",{{code:"{code}"}});}}
        sendHeartbeat(); setInterval(sendHeartbeat,3000);
        socket.on("game_abort",function(){{alert("참여 인원 부족으로 게임이 중단되었습니다.");window.location.href="/game/join/{code}";}});
        socket.on("chat_message",function(data){{
            var box=document.getElementById("chat_box");
            var div=document.createElement("div"); div.style.marginBottom="6px";
            var isMe=data.ip===myIp; div.style.textAlign=isMe?"right":"left"; div.style.color=isMe?"#0066cc":"#333";
            div.innerHTML="<b>"+(isMe?"나":(data.name || data.ip))+"</b>: "+data.msg;
            box.appendChild(div); box.scrollTop=box.scrollHeight;
        }});
        function sendChat(){{
            var input=document.getElementById("chat_input"); var msg=input.value.trim();
            if(!msg)return; socket.emit("chat_message",{{code:"{code}",msg:msg}}); input.value="";
        }}
    </script>"""
    return html

@app.route('/game/vote/<code>')
def game_vote(code):
    ip        = get_player_id()
    role      = g_roles.get(code,{}).get(ip,"시민")
    is_mafia  = role == "마피아"
    survivors = [p for p in invite_ips.get(code,[]) if p not in dead_players.get(code,[])]
    if is_mafia:
        return f"""{SOCKETIO_SCRIPT}
        <h1 style="text-align:center;margin-top:150px;font-size:30px">다른 사람들이 투표중이에요.</h1>
        <p id="vote_status" style="text-align:center;color:gray;font-size:18px">0 / {len(survivors)}명 투표</p>
        <script>
            var socket=io(); socket.emit("join_room",{{code:"{code}"}});
            socket.on("vote_update",function(data){{document.getElementById("vote_status").innerText=data.voted+" / "+data.total+"명 투표";}});
            socket.on("vote_result",function(data){{alert(data.msg);window.location.href="/game/night/{code}";}});
            socket.on("game_abort",function(){{alert("인원 부족");window.location.href="/game/join/{code}";}});
            function sendHeartbeat(){{socket.emit("heartbeat",{{code:"{code}"}});}} sendHeartbeat();setInterval(sendHeartbeat,3000);
        </script>"""
    html = f"""{SOCKETIO_SCRIPT}
    <h2 style="text-align:center;margin-top:30px">추방할 플레이어를 선택하세요</h2>
    <div style="text-align:center">"""
    for p in survivors:
        if p != ip: html += f'<button onclick="castVote(\'{p}\')" id="btn_{p}" style="display:block;margin:10px auto;padding:15px 40px;font-size:18px;width:300px;border-radius:8px;cursor:pointer">{p}</button>'
        else:       html += f"<p style='color:gray;font-size:16px'>{p} (나)</p>"
    html += f"""</div>
    <p id="my_vote" style="text-align:center;margin-top:20px;color:#0066cc;font-size:16px"></p>
    <p id="vote_status" style="text-align:center;color:gray;font-size:16px">0 / {len(survivors)}명 투표</p>
    <script>
        var socket=io(); socket.emit("join_room",{{code:"{code}"}});
        function castVote(target){{
            document.querySelectorAll("button[id^='btn_']").forEach(function(b){{b.style.background="";b.style.color="";}});
            document.getElementById("btn_"+target).style.background="#0066cc";
            document.getElementById("btn_"+target).style.color="white";
            document.getElementById("my_vote").innerText=target+"에게 투표했습니다.";
            socket.emit("cast_vote",{{code:"{code}",target:target}});
        }}
        socket.on("vote_update",function(data){{document.getElementById("vote_status").innerText=data.voted+" / "+data.total+"명 투표";}});
        socket.on("vote_result",function(data){{
            alert(data.msg);
            if(data.victory==="citizen"){{window.location.href="/game/victory/{code}/citizen";}}
            else if(data.victory==="mafia"){{window.location.href="/game/victory/{code}/mafia";}}
            else{{window.location.href="/game/night/{code}";}}
        }});
        socket.on("game_abort",function(){{alert("인원 부족");window.location.href="/game/join/{code}";}});
        function sendHeartbeat(){{socket.emit("heartbeat",{{code:"{code}"}});}} sendHeartbeat();setInterval(sendHeartbeat,3000);
    </script>"""
    return html

@app.route('/game/victory/<code>/<winner>')
def game_victory(code, winner):
    if winner == "citizen":
        police_id = next((p for p,r in g_roles.get(code,{}).items() if r=="경찰"),"???")
        mafia_id  = g_arrested.get(code,"???")
        return f"""<h1 style="text-align:center;margin-top:120px;font-size:70px;color:gold">오늘의 영웅</h1>
        <h2 style="text-align:center;margin-top:40px;font-size:30px">{police_id}가 {mafia_id}를 체포했습니다!</h2>
        {back_button_g('/game','게임 메인으로')}"""
    mafia_id = next((p for p,r in g_roles.get(code,{}).items() if r=="마피아"),"???")
    return f"""<h1 style="text-align:center;margin-top:120px;font-size:70px;color:red">실패</h1>
    <h2 style="text-align:center;margin-top:40px;font-size:30px">{mafia_id}는 마피아였습니다.<br>세상은 마피아에게 점령됐습니다.</h2>
    {back_button_g('/game','게임 메인으로')}"""

@app.route('/game/lose')
def game_lose():
    return f"""<h1 style="text-align:center;color:red;font-size:80px">패배</h1>
    {back_button_g('/game','게임 메인으로')}"""

@app.route('/game/nickname', methods=['GET', 'POST'])
def game_nickname():
    player_id = get_player_id()

    if request.method == 'POST':
        nickname = request.form.get('nickname', '').strip()
        mode = request.form.get('mode', 'ad')

        if mode == 'skip':
            session.pop('game_nickname', None)
            session['use_ip_mode'] = True   # ⭐ 이거 추가
            return redirect('/game/online')

        if not nickname:
            return render_online_shell(
                "오류",
                "닉네임을 입력해주세요.",
                '''
                <div class="note">닉네임이 비어 있습니다.</div>
                <div style="text-align:center; margin-top:20px;">
                    <button class="action-btn btn-red" onclick="location.href='/game/nickname'">
                        다시 입력
                    </button>
                </div>
                '''
            )

        current_nickname = get_active_nickname(player_id)

        # 이미 내 닉네임이 있으면:
        # 같은 닉네임 재입력은 허용, 다른 닉네임 새 생성은 차단
        if current_nickname:
            if current_nickname == nickname:
                session['game_nickname'] = current_nickname
                session['use_ip_mode'] = False
                return redirect('/game/online')

            return render_online_shell(
                "오류",
                "이미 닉네임이 등록되어 있습니다.",
                f'''
                <div class="note">현재 닉네임: <b>{current_nickname}</b></div>
                <div style="text-align:center; margin-top:20px;">
                    <button class="action-btn btn-red" onclick="location.href='/game/nickname'">
                        돌아가기
                    </button>
                </div>
                '''
            )

        # 다른 활성 플레이어와 중복 검사
        if is_nickname_in_use(nickname, exclude_player_id=player_id):
            return render_online_shell(
                "오류",
                "이미 사용 중인 닉네임입니다.",
                f'''
                <div class="note">[{nickname}] 은(는) 이미 다른 플레이어가 사용 중입니다.</div>
                <div style="text-align:center; margin-top:20px;">
                    <button class="action-btn btn-red" onclick="location.href='/game/nickname'">
                        다시 입력
                    </button>
                </div>
                '''
            )

        save_or_activate_nickname(player_id, nickname)
        session['game_nickname'] = nickname
        session['use_ip_mode'] = False

        # 닉네임 저장 후 광고 게이트로 이동
        return redirect('/game/ad-gate?next=/game/online')

    current_name = (session.get('game_nickname') or '').strip()

    status = (
        f'<div style="text-align:center; margin-top: 14px; color:#dbeafe; font-size:18px;">'
        f'현재 닉네임: <b style="color:#fff">{current_name}</b>'
        f'</div>'
        if current_name
        else '<div style="text-align:center; margin-top: 14px; color:#dbeafe; font-size:18px;">현재 닉네임 없음</div>'
    )

    inner_html = f'''
        <div class="status-box">
            {status}
        </div>

        <div class="section-title">Nickname</div>
        <div class="form-box">
            <form method="POST" style="display:grid; gap:14px;">
                <input class="input" name="nickname" placeholder="닉네임 입력" maxlength="20">

                <button class="action-btn btn-blue" type="submit" name="mode" value="ad">
                    닉네임 저장 (광고 후 플레이)
                </button>

                <button class="action-btn btn-orange" type="submit" name="mode" value="skip">
                    IP로 플레이
                </button>
            </form>
        </div>

        <div class="note">
            닉네임으로 플레이하면 광고를 한 번 본 뒤 진행됩니다.<br>
            IP로 플레이는 광고 없이 바로 진행됩니다.
        </div>
    '''

    return render_online_shell(
        "닉네임 설정",
        "닉네임을 만들거나, IP로 바로 플레이할 수 있어요.",
        inner_html
    )

if __name__ == "__main__":
    init_db()

    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port)
