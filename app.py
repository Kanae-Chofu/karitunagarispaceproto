import streamlit as st
import sqlite3
import random
from datetime import datetime

# 仮ID生成（色＋動物）
def generate_kari_id():
    colors = ["青い", "赤い", "白い", "黒い", "緑の"]
    animals = ["風", "猫", "鳥", "月", "狐"]
    return random.choice(colors) + random.choice(animals)

# DB初期化
def init_db():
    conn = sqlite3.connect("chat.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kari_id TEXT,
                    partner_id TEXT,
                    message TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
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

# メッセージ保存
def save_message(kari_id, partner_id, message):
    conn = sqlite3.connect("chat.db")
    c = conn.cursor()
    c.execute("INSERT INTO messages (kari_id, partner_id, message) VALUES (?, ?, ?)",
              (kari_id, partner_id, message))
    conn.commit()
    conn.close()

# メッセージ取得
def get_messages(kari_id, partner_id):
    conn = sqlite3.connect("chat.db")
    c = conn.cursor()
    c.execute('''SELECT kari_id, message, timestamp FROM messages 
                 WHERE (kari_id=? AND partner_id=?) OR (kari_id=? AND partner_id=?) 
                 ORDER BY timestamp''',
              (kari_id, partner_id, partner_id, kari_id))
    messages = c.fetchall()
    conn.close()
    return messages

# 友達申請送信
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

# 申請受信一覧
def get_received_requests(my_id):
    conn = sqlite3.connect("chat.db")
    c = conn.cursor()
    c.execute("SELECT from_id FROM friend_requests WHERE to_id=? AND status='pending'", (my_id,))
    requests = c.fetchall()
    conn.close()
    return [r[0] for r in requests]

# 申請承認処理
def approve_friend_request(my_id, from_id):
    conn = sqlite3.connect("chat.db")
    c = conn.cursor()
    c.execute("UPDATE friend_requests SET status='approved' WHERE from_id=? AND to_id=?", (from_id, my_id))
    c.execute("INSERT OR IGNORE INTO friends (user, friend) VALUES (?, ?)", (my_id, from_id))
    c.execute("INSERT OR IGNORE INTO friends (user, friend) VALUES (?, ?)", (from_id, my_id))
    conn.commit()
    conn.close()

# 友達一覧取得
def get_friends(my_id):
    conn = sqlite3.connect("chat.db")
    c = conn.cursor()
    c.execute("SELECT friend FROM friends WHERE user=?", (my_id,))
    friends = c.fetchall()
    conn.close()
    return [f[0] for f in friends]

# セッション管理
if "kari_id" not in st.session_state:
    st.session_state.kari_id = generate_kari_id()
if "partner_id" not in st.session_state:
    st.session_state.partner_id = ""

# UI
st.set_page_config(page_title="仮つながりスペース", layout="centered")
st.title("🫧 仮つながりスペース（プロトタイプ）")
st.write(f"あなたの仮ID: `{st.session_state.kari_id}`")

# パートナー入力
partner = st.text_input("話したい相手の仮IDを入力", st.session_state.partner_id)
if partner:
    st.session_state.partner_id = partner
    st.write(f"相手: `{partner}`")

    # 話題カード（仮）
    st.markdown("💬 話題カード: **羽生くんの好きな演技は？**")

    # メッセージ表示
    messages = get_messages(st.session_state.kari_id, partner)
    for sender, msg, _ in messages:
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

    # メッセージ送信（エンター対応）
    new_message = st.chat_input("メッセージを入力してください")
    if new_message:
        save_message(st.session_state.kari_id, partner, new_message)
        st.rerun()

    # 3往復以上で申請可能
    if len(messages) >= 6:
        st.success("🌱 この人と友達申請できます（3往復以上）")
        if st.button("友達申請する", use_container_width=True):
            if send_friend_request(st.session_state.kari_id, partner):
                st.success("申請を送信しました！")
            else:
                st.info("すでに申請済みです")

# 申請受信一覧
st.divider()
st.subheader("📬 受信した友達申請")
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
st.subheader("👥 あなたの友達一覧")
friends = get_friends(st.session_state.kari_id)
if friends:
    for f in friends:
        st.write(f"・仮ID `{f}`")
else:
    st.write("まだ友達はいません。")