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

# セッション管理
if "kari_id" not in st.session_state:
    st.session_state.kari_id = generate_kari_id()
if "partner_id" not in st.session_state:
    st.session_state.partner_id = ""

# UI
st.set_page_config(page_title="仮つながりスペース", layout="centered")
st.title("仮つながりスペース（プロトタイプ）")
st.write(f"あなたの仮ID: `{st.session_state.kari_id}`")

# パートナー入力
partner = st.text_input("話したい相手の仮IDを入力", st.session_state.partner_id)
if partner:
    st.session_state.partner_id = partner
    st.write(f"相手: `{partner}`")

    # テンプレート表示（仮）
    st.markdown("話題カード: **羽生くんの好きな演技は？**")

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

    # 3コメント以上で申請可能
    if len(messages) >= 6:
        st.success(" この人と友達申請できます（3往復以上）")