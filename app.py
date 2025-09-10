import streamlit as st
import sqlite3
import random
import time

# ⏱ 自動更新（3秒ごと）
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()
elif time.time() - st.session_state.last_refresh > 3:
    st.session_state.last_refresh = time.time()
    st.rerun()

# 🌙 ダークモード固定
st.markdown("""
<style>
body, .stApp { background-color: #000000; color: #FFFFFF; }
div[data-testid="stHeader"] { background-color: #000000; }
div[data-testid="stToolbar"] { display: none; }
input, textarea { background-color: #1F2F54 !important; color:#FFFFFF !important; }
button { background-color: #426AB3 !important; color:#FFFFFF !important; border: none !important; }
</style>
""", unsafe_allow_html=True)

# 話題カードテンプレート
topics = {
    "猫": ["猫派？犬派？", "飼ってる猫の名前は？", "猫の仕草で好きなものは？"],
    "言葉": ["好きな言葉ある？", "座右の銘ってある？", "言葉に救われたことある？"]
}

# DB初期化
def init_db():
    conn = sqlite3.connect("chat.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    kari_id TEXT PRIMARY KEY,
                    password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kari_id TEXT,
                    partner_id TEXT,
                    message TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    try:
        c.execute("ALTER TABLE messages ADD COLUMN topic_theme TEXT")
    except sqlite3.OperationalError:
        pass
    c.execute('''CREATE TABLE IF NOT EXISTS friend_requests (
                    from_id TEXT,
                    to_id TEXT,
                    status TEXT DEFAULT 'pending',
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS friends (
                    user TEXT,
                    friend TEXT,
                    UNIQUE(user, friend))''')
    conn.commit()
    conn.close()

init_db()

# DB操作関数
def register_user(kari_id, password):
    conn = sqlite3.connect("chat.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE kari_id=?", (kari_id,))
    if c.fetchone():
        conn.close()
        return False
    c.execute("INSERT INTO users (kari_id, password) VALUES (?, ?)", (kari_id, password))
    conn.commit()
    conn.close()
    return True

def login_user(kari_id, password):
    conn = sqlite3.connect("chat.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE kari_id=? AND password=?", (kari_id, password))
    result = c.fetchone()
    conn.close()
    return result is not None

def save_message(kari_id, partner_id, message, theme=None):
    conn = sqlite3.connect("chat.db")
    c = conn.cursor()
    if theme:
        c.execute("INSERT INTO messages (kari_id, partner_id, message, topic_theme) VALUES (?, ?, ?, ?)",
                  (kari_id, partner_id, message, theme))
    else:
        c.execute("INSERT INTO messages (kari_id, partner_id, message) VALUES (?, ?, ?)",
                  (kari_id, partner_id, message))
    conn.commit()
    conn.close()

def get_messages(kari_id, partner_id):
    conn = sqlite3.connect("chat.db")
    c = conn.cursor()
    c.execute('''SELECT kari_id, message FROM messages 
                 WHERE (kari_id=? AND partner_id=?) OR (kari_id=? AND partner_id=?) 
                 ORDER BY timestamp''',
              (kari_id, partner_id, partner_id, kari_id))
    messages = c.fetchall()
    conn.close()
    return messages

def get_shared_theme(kari_id, partner_id):
    conn = sqlite3.connect("chat.db")
    c = conn.cursor()
    c.execute('''SELECT topic_theme FROM messages 
                 WHERE ((kari_id=? AND partner_id=?) OR (kari_id=? AND partner_id=?)) 
                 AND topic_theme IS NOT NULL 
                 ORDER BY timestamp LIMIT 1''',
              (kari_id, partner_id, partner_id, kari_id))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def send_friend_request(from_id, to_id):
    conn = sqlite3.connect("chat.db")
    c = conn.cursor()
    c.execute("SELECT * FROM friend_requests WHERE from_id=? AND to_id=?", (from_id, to_id))
    if c.fetchone():
        conn.close()
        return False
    c.execute("INSERT INTO friend_requests (from_id, to_id) VALUES (?, ?)", (from_id, to_id))
    conn.commit()
    conn.close()
    return True

def get_received_requests(my_id):
    conn = sqlite3.connect("chat.db")
    c = conn.cursor()
    c.execute("SELECT from_id FROM friend_requests WHERE to_id=? AND status='pending'", (my_id,))
    requests = c.fetchall()
    conn.close()
    return [r[0] for r in requests]

def approve_friend_request(my_id, from_id):
    conn = sqlite3.connect("chat.db")
    c = conn.cursor()
    c.execute("UPDATE friend_requests SET status='approved' WHERE from_id=? AND to_id=?", (from_id, my_id))
    c.execute("INSERT OR IGNORE INTO friends (user, friend) VALUES (?, ?)", (my_id, from_id))
    c.execute("INSERT OR IGNORE INTO friends (user, friend) VALUES (?, ?)", (from_id, my_id))
    conn.commit()
    conn.close()

def get_friends(my_id):
    conn = sqlite3.connect("chat.db")
    c = conn.cursor()
    c.execute("SELECT friend FROM friends WHERE user=?", (my_id,))
    friends = c.fetchall()
    conn.close()
    return [f[0] for f in friends]

# UI開始
st.set_page_config(page_title="仮つながりスペース", layout="centered")
st.title("仮つながりスペース")

# ログイン状態確認
if "kari_id" in st.session_state:
    st.write(f"現在ログイン中： `{st.session_state.kari_id}`")

    partner_input = st.text_input("話したい相手の仮IDを入力", st.session_state.get("partner_id", ""))
    if partner_input != "":
        st.session_state.partner_id = partner_input

    partner = st.session_state.get("partner_id", "")
    if partner != "":
        st.write(f"相手: `{partner}`")

        shared_theme = get_shared_theme(st.session_state.kari_id, partner)
        if shared_theme:
            theme = shared_theme
        else:
            if "selected_theme" not in st.session_state:
                st.session_state.theme_choices = random.sample(list(topics.keys()), 2)
                chosen = st.radio("話したいテーマを選んでください", st.session_state.theme_choices)
                if st.button("このテーマで話す"):
                    st.session_state.selected_theme = chosen
                    st.session_state.card_index = 0
                    st.rerun()
                st.stop()
            theme = st.session_state.selected_theme

        card_index = st.session_state.get("card_index", 0)
        st.markdown(f" 話題カード: **{topics[theme][card_index]}**")
        if st.button("次の話題カード"):
            st.session_state.card_index = (card_index + 1) % len(topics[theme])
            st.rerun()

        messages = get_messages(st.session_state.kari_id, partner)
        for sender, msg in messages:
            align = "right" if sender == st.session_state.kari_id else "left"
            bg = "#1F2F54" if align == "right" else "#426AB3"
            st.markdown(
                f"""
                <div style='text-align: {align}; margin: 5px 0;'>
                    <span style='background-color:{bg}; color:#FFFFFF; padding:8px 12px; border-radius:10px; display:inline-block; max-width:80%;'>
                        {msg}
                    </span>
                </div>
                """,
                unsafe_allow_html=True
            )

        new_message = st.chat_input("メッセージを入力")
        if new_message:
            theme_to_save = get_shared_theme(st.session_state.kari_id, partner)
            if not theme_to_save and "selected_theme" in st.session_state:
                theme_to_save = st.session_state.selected_theme
            save_message(st.session_state.kari_id, partner, new_message, theme_to_save)
            st.rerun()

        # 3往復以上で友達申請可能
        if len(messages) >= 6:
            st.success("この人と友達申請できます（3往復以上）")
            if st.button("友達申請する", use_container_width=True):
                if send_friend_request(st.session_state.kari_id, partner):
                    st.success("申請を送信しました！")
                else:
                    st.info("すでに申請済みです")

    # 申請受信一覧
    st.divider()
    st.subheader("受信した友達申請")
    requests = get_received_requests(st.session_state.kari_id)
    if requests:
        for req in requests:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"仮ID `{req}` から申請があります")
            with col2:
                if st.button(f"承認する（{req}）", key=f"approve_{req}"):
                    approve_friend_request(st.session_state.kari_id, req)
                    st.success(f"{req} を友達に追加しました！")
                    st.rerun()
    else:
        st.write("現在、受信した申請はありません。")

    # 友達一覧表示
    st.subheader("あなたの友達一覧")
    friends = get_friends(st.session_state.kari_id)
    if friends:
        for f in friends:
            st.write(f"・仮ID `{f}`")
    else:
        st.write("まだ友達はいません。")

# ログインしていない場合
else:
    st.subheader("ログイン")
    login_id = st.text_input("仮IDでログイン")
    login_pw = st.text_input("パスワード", type="password")
    if st.button("ログインする"):
        if login_user(login_id, login_pw):
            st.session_state.kari_id = login_id
            st.success(f"ようこそ、{login_id} さん！")
            st.rerun()
        else:
            st.error("ログインに失敗しました。仮IDまたはパスワードが違います")

    st.subheader("新規登録")
    new_id = st.text_input("仮IDを入力（例：赤い猫）")
    new_pw = st.text_input("パスワードを入力", type="password")
    if st.button("登録する"):
        if register_user(new_id, new_pw):
            st.success("登録が完了しました！ログインしました")
            st.session_state.kari_id = new_id
            st.rerun()
        else:
            st.error("その仮IDはすでに使われています")
            