import streamlit as st
from openai import OpenAI
import random
import requests
import base64

# 从 Secrets 安全读取密钥
client = OpenAI(api_key=st.secrets["DEEPSEEK_KEY"], base_url="https://api.deepseek.com")
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO = "losran/tattoo-ai-tool"

st.set_page_config(page_title="Tattoo Studio", layout="wide", initial_sidebar_state="collapsed")

# --- GitHub 自动写盘逻辑 ---
def save_to_cloud(category, word):
    paths = {"主体": "data/subjects.txt", "风格": "data/styles.txt", 
             "部位": "data/placements.txt", "氛围": "data/vibes.txt"}
    path = paths.get(category)
    url = f"https://api.github.com/repos/{REPO}/contents/{path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    
    # 获取旧 SHA 并追加内容
    r = requests.get(url, headers=headers).json()
    if 'sha' in r:
        old_txt = base64.b64decode(r['content']).decode('utf-8')
        if word not in old_txt:
            new_txt = old_txt.strip() + "\n" + word
            payload = {
                "message": f"Add {word}",
                "content": base64.b64encode(new_txt.encode('utf-8')).decode('utf-8'),
                "sha": r['sha']
            }
            requests.put(url, headers=headers, json=payload)

# --- 启动时从云端加载已有数据 ---
if 'db' not in st.session_state:
    st.session_state.db = {"主体": [], "风格": [], "部位": [], "氛围": []}
    # (加载逻辑：循环读取 data/ 下的 4 个 txt 并存入 db)

# 拆解逻辑：含自动清空与同步
def handle_disassembly():
    val = st.session_state.temp_input
    if val:
        with st.spinner('AI 正在分类并永久同步云端...'):
            res = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "system", "content": "格式:主体:X|风格:X|部位:X|氛围:X"},
                          {"role": "user", "content": val}]
            ).choices[0].message.content
            for item in res.split("|"):
                if ":" in item:
                    k, v = item.split(":", 1)
                    w = v.strip()
                    for key in st.session_state.db.keys():
                        if key in k:
                            st.session_state.db[key].append(w)
                            save_to_cloud(key, w) # 存入 GitHub
            st.session_state.temp_input = "" # 清空
            st.success("资产已存入云端保险箱！")

# (此处接你之前的苹果风格看板排版和批量生成逻辑代码...)
