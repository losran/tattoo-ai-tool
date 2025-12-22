import streamlit as st
from openai import OpenAI
import random, requests, base64, time

# --- 1. 基础配置 ---
client = OpenAI(api_key=st.secrets["DEEPSEEK_KEY"], base_url="https://api.deepseek.com")
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO = "losran/tattoo-ai-tool"

st.set_page_config(page_title="Tattoo Pro Station", layout="wide", initial_sidebar_state="collapsed")

# --- 2. 核心 CSS 布局 (强制隔离三栏 + 碎片卡片化) ---
st.markdown("""
    <style>
    /* 基础清理：隐藏页眉页脚，让空间更大 */
    #MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;}
    .main { background-color: #0d0d0d; color: #fff; }
    .block-container { padding: 0 !important; max-width: 100% !important; }

    /* [左] 固定看板：宽度锁死在 120px */
    [data-testid="stColumn"]:nth-child(1) {
        position: fixed; left: 0; top: 0; bottom: 0; width: 120px !important;
        background: #161b22; border-right: 1px solid #333; z-index: 1001; padding-top: 20px !important;
    }
    .sticky-stats { position: fixed; left: 10px; bottom: 20px; width: 100px; z-index: 1002; }
    .nav-item { background: rgba(255,255,255,0.05); border: 1px solid #333; border-radius: 8px; padding: 8px; margin-top: 8px; text-align: center; }
    .nav-val { color: #58a6ff; font-weight: bold; font-size: 16px; }

    /* [中] 生产区：自适应宽度，左右留出物理边距 */
    [data-testid="stColumn"]:nth-child(2) {
        margin-left: 140px !important; margin-right: 380px !important;
        width: auto !important; padding: 40px !important; min-height: 100vh;
    }

    /* [右] 仓库区：宽度锁死在 360px，独立滚动 */
    [data-testid="stColumn"]:nth-child(3) {
        position: fixed; right: 0; top: 0; bottom: 0; width: 360px !important;
        background: #0d1117; border-left: 1px solid #333; padding: 30px 20px !important;
        z-index: 1000; overflow-y: auto !important;
    }

    /* 💥 碎片卡片样式 (带边框的大爆炸方块) */
    [data-testid="stCheckbox"] {
        background: #1f2428 !important; border: 1px solid #333 !important;
        padding: 5px 10px !important; border-radius: 6px !important; margin-bottom: 5px !important;
    }
    /* 勾选后的高亮红色效果 */
    [data-testid="stCheckbox"]:has(input:checked) {
        border-color: #ff4b4b !important; background: #2d1b1b !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. 数据读写函数 (带清理逻辑) ---
def sync_git(fn, data):
    url = f"https://api.github.com/repos/{REPO}/contents/data/{fn}"
    hd = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        r = requests.get(url, headers=hd).json()
        clean_data = [d.strip() for d in data if d and d.strip()] # 去除空行
        content = base64.b64encode("\n".join(list(set(clean_data))).encode()).decode()
        requests.put(url, headers=hd, json={"message": "sync", "content": content, "sha": r.get('sha')})
    except: pass

def get_git(fn):
    url = f"https://api.github.com/repos/{REPO}/contents/data/{fn}"
    r = requests.get(url, headers={"Authorization": f"token {GITHUB_TOKEN}"})
    if r.status_code == 200:
        return [l.strip() for l in base64.b64decode(r.json()['content']).decode('utf-8').splitlines() if l.strip()]
    return []

# 初始化 session_state
if 'db' not in st.session_state:
    st.session_state.db = {k: get_git(v) for k, v in {
        "Subject":"subjects.txt", "Action":"actions.txt", 
        "Style":"styles.txt", "Mood":"moods.txt", "Usage":"usage.txt"
    }.items()}
if 'pre_tags' not in st.session_state: st.session_state.pre_tags = []
if 'input_id' not in st.session_state: st.session_state.input_id = 0# --- 4. 物理分栏布局渲染 ---
# 这里的比例 [12, 53, 35] 对应了 CSS 中定义的固定宽度比例
col_nav, col_mid, col_lib = st.columns([12, 53, 35])

# 👉 [左侧栏] 资产统计看板
with col_nav:
    # 顶部小图标，增加呼吸感
    st.markdown("### 🌀") 
    
    # 构造看板 HTML
    # 注意：这里展示你最关心的 4 个核心维度统计
    stats_html = '<div class="sticky-stats">'
    for k in ["Subject", "Style", "Action", "Mood"]:
        num = len(st.session_state.db.get(k, []))
        stats_html += f'''
            <div class="nav-item">
                <div style="font-size:10px;color:#888">{k}</div>
                <div class="nav-val">{num}</div>
            </div>
        '''
    st.markdown(stats_html + '</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# 下面开始进入中间生产区，我们先打个招呼，确认位置正确
with col_mid:
    st.title("✨ 灵感大爆炸拆解")
    st.caption("基于五维模型：Subject | Action | Style | Mood | Usage")
