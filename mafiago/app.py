from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from datetime import datetime
import sqlite3
import hashlib
import os

app = Flask(__name__)
app.secret_key = 'mafia_go_secret_key_2024'

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

# ===== 사이트 이름 설정 =====
SITE_NAME = "Universe Go!"   # 네비게이션, 푸터 로고에 표시되는 이름

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

@app.route('/store')
def store():
    points = 0
    purchase_history = []
    if session.get('user'):
        db = get_db()
        total = db.execute(
            'SELECT SUM(amount) FROM rewards WHERE username = ?', (session['user'],)
        ).fetchone()[0] or 0
        spent = db.execute(
            'SELECT SUM(amount) FROM purchases WHERE username = ? AND method = ?', (session['user'], '포인트')
        ).fetchone()[0] or 0
        points = total - spent
        purchase_history = db.execute(
            'SELECT * FROM purchases WHERE username = ? ORDER BY id DESC LIMIT 20', (session['user'],)
        ).fetchall()
        db.close()
    return render_template('store.html', items=STORE_ITEMS, points=points, purchase_history=purchase_history)

@app.route('/store/buy/points/<int:item_id>', methods=['POST'])
def buy_with_points(item_id):
    flash('🔒 현재 포인트 구매 기능은 준비 중입니다.', 'error')
    return redirect(url_for('store'))

@app.route('/store/buy/cash/<int:item_id>', methods=['POST'])
def buy_with_cash(item_id):
    flash('💳 현재 결제 시스템(PG사) 연동 준비 중입니다.', 'error')
    return redirect(url_for('store'))

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
        {'category': '스토어', 'links': [
            {'name': '스토어', 'url': '/store'},
        ]},
        {'category': '개인정보', 'links': [
            {'name': '개인정보 처리방침', 'url': '/privacy'},
        ]},
        {'category': '계정', 'links': [
            {'name': '로그인', 'url': '/login'},
            {'name': '회원가입', 'url': '/register'},
            {'name': '마이 페이지', 'url': '/account'},
            {'name': '회원 관리 (관리자)', 'url': '/admin/members'},
        ]},
    ]
    return render_template('sitemap.html', pages=pages)

@app.route('/advertisement')
def advertisement():
    reward_history = []
    if session.get('user'):
        db = get_db()
        reward_history = db.execute(
            'SELECT * FROM rewards WHERE username = ? ORDER BY id DESC LIMIT 10',
            (session['user'],)
        ).fetchall()
        db.close()
    return render_template('advertisement.html', reward_history=reward_history)

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
    code = data.get("code"); ip = session.get("user") or request.remote_addr
    msg  = data.get("msg","").strip()[:200]
    if not code or not msg: return
    socketio.emit("chat_message",{"ip":ip,"msg":msg},room=code)

@socketio.on("heartbeat")
def on_heartbeat(data):
    code = data.get("code"); ip = session.get("user") or request.remote_addr
    if not code: return
    if code not in heartbeats: heartbeats[code] = {}
    heartbeats[code][ip] = time.time()
    if code in invite_ips and invite_ips[code]:
        if night_phase.get(code) == "done": return
        now = time.time()
        all_online = [p for p in invite_ips[code] if (now-heartbeats.get(code,{}).get(p,0)) < HEARTBEAT_TIMEOUT]
        if len(all_online) < 4:
            reset_online_game(code); socketio.emit("game_abort",{},room=code)

@socketio.on("confirm_result")
def on_confirm_result(data):
    code = data.get("code"); ip = session.get("user") or request.remote_addr
    if not code: return
    if code not in result_confirmed: result_confirmed[code] = set()
    result_confirmed[code].add(ip)
    survivors = [p for p in invite_ips.get(code,[]) if p not in dead_players.get(code,[])]
    confirmed = result_confirmed.get(code,set())
    all_confirmed = all(p in confirmed for p in survivors)
    socketio.emit("confirm_update",{"confirmed":len(confirmed),"total":len(survivors),"all_confirmed":all_confirmed},room=code)

@socketio.on("cast_vote")
def on_cast_vote(data):
    code=data.get("code"); target=data.get("target"); ip=session.get("user") or request.remote_addr
    if not code or not target: return
    if code not in day_votes: day_votes[code] = {}
    day_votes[code][ip] = target
    survivors = [p for p in invite_ips.get(code,[]) if p not in dead_players.get(code,[])]
    voted     = [p for p in survivors if p in day_votes.get(code,{})]
    socketio.emit("vote_update",{"voted":len(voted),"total":len(survivors)},room=code)
    if len(voted) == len(survivors):
        tally     = Counter(day_votes[code][p] for p in survivors)
        max_votes = max(tally.values()); top = [p for p,v in tally.items() if v==max_votes]
        exiled    = top[0] if len(top)==1 else None
        if exiled:
            if code not in dead_players: dead_players[code]=[]
            dead_players[code].append(exiled)
            msg = f"{exiled}이(가) 추방되었습니다! ({max_votes}표)"
        else:
            msg = "동률로 아무도 추방되지 않았습니다."
        day_votes.pop(code,None)
        v = check_victory(code)
        if v=="citizen_win":   socketio.emit("vote_result",{"msg":msg,"exiled":exiled,"victory":"citizen"},room=code)
        elif v=="mafia_win":   socketio.emit("vote_result",{"msg":msg,"exiled":exiled,"victory":"mafia"},room=code)
        else:
            night_phase[code]="mafia"
            socketio.emit("vote_result",{"msg":msg,"exiled":exiled,"victory":None},room=code)

# ── 온라인 HTTP ──
@app.route('/game/online')
def game_online_home():
    user = request.args.get("user")
    if user: session["user"] = user
    return render_template('game_online_home.html', top_bar=game_top_bar())

@app.route('/game/heartbeat/<code>', methods=['POST'])
def game_heartbeat(code):
    ip = get_player_id()
    if code not in heartbeats: heartbeats[code] = {}
    heartbeats[code][ip] = time.time()
    return jsonify({"ok":True})

@app.route('/game/player_count/<code>')
def game_player_count(code):
    return jsonify({"count":len(get_active_players(code))})

@app.route('/game/my_result/<code>')
def game_my_result(code):
    ip = get_player_id()
    return jsonify({"dead":ip in dead_players.get(code,[])})

@app.route('/game/create_code')
def game_create_code():
    code = generate_code()
    invite_ips[code]=[]; heartbeats[code]={}; g_roles[code]={}
    return f"""<h2 style="text-align:center">초대코드: <b>{code}</b></h2>
    <div style="text-align:center">
        <button onclick="location.href='/game/join/{code}'" style="padding:20px;font-size:20px">바로 들어가기</button>
    </div>{back_button_g('/game/online','온라인 메뉴로')}"""

@app.route('/game/join_code')
def game_join_code():
    return """<h2 style="text-align:center">초대코드 입력</h2>
    <div style="text-align:center">
        <form action="/game/join_code_go" method="post">
            <input name="code" placeholder="초대코드" style="padding:10px;font-size:16px"><br><br>
            <button type="submit" style="padding:10px;font-size:16px">참여</button>
        </form>
    </div>"""

@app.route('/game/join_code_go', methods=['POST'])
def game_join_code_go():
    code = request.form["code"]
    if code not in invite_ips:
        return f"<h2 style='text-align:center'>코드를 다시 확인해주십시오.</h2>{back_button_g('/game/online')}"
    return f"<script>location.href='/game/join/{code}'</script>"

@app.route('/game/join/<code>')
def game_join(code):
    ip = get_player_id()
    if code not in heartbeats: heartbeats[code] = {}
    heartbeats[code][ip] = time.time()
    return waiting_room_html("서버 참여 완료", code, f"/game/start/{code}")

@app.route('/game/create_server')
def game_create_server():
    return """<h2 style="text-align:center">서버 이름 입력</h2>
    <div style="text-align:center">
        <form action="/game/server_created" method="post">
            <input name="name" placeholder="서버 이름" style="padding:10px;font-size:16px"><br><br>
            <button type="submit" style="padding:10px;font-size:16px">생성</button>
        </form>
    </div>"""

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
    html = "<h2 style='text-align:center'>서버 목록</h2><div style='text-align:center'>"
    for s in servers:
        html += f"<button onclick=\"location.href='/game/online_server/{s}'\" style='padding:10px;font-size:16px;margin:5px'>{s}</button><br><br>"
    html += f"</div>{back_button_g('/game/online','온라인 메뉴로')}"
    return html

@app.route('/game/online_server/<n>')
def game_online_server(n):
    ip = get_player_id()
    if n not in heartbeats: heartbeats[n] = {}
    heartbeats[n][ip] = time.time()
    return waiting_room_html(f"{n} 서버 참여 완료", n, f"/game/start/{n}")

@app.route('/game/start/<code>')
def game_start(code):
    active = get_active_players(code)
    invite_ips[code] = active
    if len(active) < 4:
        return f"""<h2 style="text-align:center">인원이 부족합니다 (현재 {len(active)}명 / 최소 4명)</h2>
        {back_button_g(f'/game/join/{code}','대기실로 돌아가기')}"""
    job_list = ["마피아","경찰","의사"]
    g_roles[code] = {}; random.shuffle(active)
    for i, p in enumerate(active):
        g_roles[code][p] = job_list[i] if i < 3 else "시민"
    night_phase[code] = "mafia"
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
            div.innerHTML="<b>"+(isMe?"나":data.ip)+"</b>: "+data.msg;
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


if __name__ == '__main__':
    init_db()
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
