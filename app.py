import streamlit as st
import requests, base64, time
from openai import OpenAI
# 📍 引入样式管理器 (保持你现在的视觉架构)
from style_manager import apply_pro_style, render_unified_sidebar

# --- 1. 核心配置 (必须第一行) ---
st.set_page_config(layout="wide", page_title="Tattoo AI Workbench")

# --- 2. 初始化 API 和 数据库配置 (下午的功能逻辑) ---
try:
    client = OpenAI(api_key=st.secrets["DEEPSEEK_KEY"], base_url="https://api.deepseek.com")
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
except:
    st.error("⚠️ 请配置 secrets.toml 中的 DEEPSEEK_KEY 和 GITHUB_TOKEN")
    st.stop()

REPO = "losran/tattoo-ai-tool"
FILES = {
    "Subject": "subjects.txt", "Action": "actions.txt", 
    "Style": "styles.txt", "Mood": "moods.txt", "Usage": "usage.txt"
}

# --- 3. 核心工具函数 (复活下午的逻辑) ---
def get_data(filename):
    """GitHub 获取"""
    url = f"https://api.github.com/repos/{REPO}/contents/data/{filename}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            return [line.strip() for line in base64.b64decode(resp.json()['content']).decode().splitlines() if line.strip()]
    except: pass
    return []

def sync_data(filename, data_list):
    """GitHub 同步"""
    url = f"https://api.github.com/repos/{REPO}/contents/data/{filename}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        get_resp = requests.get(url, headers=headers).json()
        content_str = "\n".join(sorted(list(set(data_list))))
        b64_content = base64.b64encode(content_str.encode()).decode()
        requests.put(url, headers=headers, json={
            "message": "update from mirror tool",
            "content": b64_content,
            "sha": get_resp.get('sha')
        })
    except: st.error("同步失败")

# --- 4. 状态初始化 ---
if 'db' not in st.session_state:
    st.session_state.db = {k: get_data(v) for k, v in FILES.items()}
if 'input_val' not in st.session_state: st.session_state.input_val = ""
if 'ai_results' not in st.session_state: st.session_state.ai_results = [] # 存储AI拆解结果
if 'is_open' not in st.session_state: st.session_state.is_open = True

# --- 5. 注入视觉 (新版样式) ---
apply_pro_style()

# 侧边栏：使用真实数据驱动统计
real_counts = {k: len(v) for k, v in st.session_state.db.items()}
render_unified_sidebar(real_counts)

# --- 6. 顶层开关 (镜像布局核心) ---
btn_col1, btn_col2 = st.columns([12, 1])
with btn_col2:
    icon = "❯" if st.session_state.is_open else "❮ 仓库"
    if st.button(icon, help="切换仓库显示"):
        st.session_state.is_open = not st.session_state.is_open
        st.rerun()

# --- 7. 主布局结构 ---
if st.session_state.is_open:
    # 💡 增加中间宽度比例，左右
