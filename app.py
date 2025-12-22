import streamlit as st
from openai import OpenAI
import random, requests, base64, time

# --- 1. 配置与初始化 ---
client = OpenAI(api_key=st.secrets["DEEPSEEK_KEY"], base_url="https://api.deepseek.com")
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO = "losran/tattoo-ai-tool"

st.set_page_config(page_title="Tattoo Pro Station", layout="wide", initial_sidebar_state="collapsed")

# --- 2. 核心 CSS 修正 (彻底解决排版怪异问题) ---
st.markdown("""
    <style>
    /* 全局背景与边距重置 */
    .main { background-color: #0d0d0d; }
    .block-container { padding: 0 !important; max-width: 100% !important; }
    
    /* [1] 左侧导航栏 - 固定宽度与定位 */
    [data-testid="stColumn"]:nth-child(1) {
        position: fixed; left: 0; top: 0; bottom: 0;
        width: 100px !important;
        background: #161b22;
        border-right: 1px solid #30363d;
        padding: 40px 10px !important;
        z-index: 1001;
        text-align: center;
    }

    /* [2] 中间生产区 - 居中且宽度自适应 */
    [data-testid="stColumn"]:nth-child(2) {
        margin-left: 120px !important;
        margin-right: 380px !important;
        width: auto !important;
        padding: 60px 40px !important;
        min-height: 100vh;
    }

    /* [3] 右侧资产库 - 固定在右侧 */
    [data-testid="stColumn"]:nth-child(3) {
        position: fixed; right: 0; top: 0; bottom: 0;
        width: 360px !important;
        background: #0d1117;
        border-left: 1px solid #30363d;
        padding: 40px 20px !important;
        z-index: 1000;
        overflow-y: auto;
    }

    /* 装饰：左侧统计小方块 */
    .nav-item { margin-bottom: 25px; padding: 10px 5px; background: #21262d; border-radius: 8px; border: 1px solid #30363d; }
    .nav-label { font-size: 11px; color: #8b949e; margin-bottom: 4px; }
    .nav-val { font-size: 18px; font-weight: bold; color: #58a6ff; }

    /* 中间按钮美化 */
    .stButton > button {
        border-radius: 50px !important;
        padding: 10px 24px !important;
        font-weight: 600 !important;
    }
    
    /* 预览标签高亮视觉 */
    .stCheckbox { background: #1a1a1a; padding: 10px; border-radius: 8px; border: 1px solid #333; margin-bottom: 5px; }
    </style>
""", unsafe_allow_html=True)

# --- 3. 数据同步逻辑 (保持不变) ---
def sync_git(fn, data):
    url = f"https://api.github.com/repos/{REPO}/contents/data/{fn}"
    hd = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        r = requests.get(url, headers=hd).json()
        sha = r.get('sha')
        content = base64.b64encode("\n".join(list(set(data))).encode()).decode()
        requests.put(url, headers=hd, json={"message": "sync", "content": content, "sha": sha})
    except: pass

def get_git(fn):
    url = f"https://api.github.com/repos/{REPO}/contents/data/{fn}"
    r = requests.get(url, headers={"Authorization": f"token {GITHUB_TOKEN}"})
    return base64.b64decode(r.json()['content']).decode('utf-8').splitlines() if r.status_code == 200 else []

# 初始加载
if 'db' not in st.session_state:
    st.session_state.db = {k: get_git(v) for k, v in {"主体":"subjects.txt","风格":"styles.txt","部位":"placements.txt","氛围":"vibes.txt","收藏":"favorites.txt"}.items()}
if 'is_split' not in st.session_state: st.session_state.is_split = False
if 'pre_tags' not in st.session_state: st.session_state.pre_tags = []

# --- 4. 三栏布局声明 ---
col_nav, col_mid, col_lib = st.columns([10, 55, 35])

# 👉 左：固定统计导航
with col_nav:
    st.markdown("### 🌀")
    for k in ["主体", "风格", "部位", "氛围"]:
        num = len(st.session_state.db.get(k, []))
        st.markdown(f'<div class="nav-item"><div class="nav-label">{k}</div><div class="nav-val">{num}</div></div>', unsafe_allow_html=True)

# 👉 中：流式操作区
with col_mid:
    st.title("✨ 智能提取入库")
    raw = st.text_area("输入样板提示词", height=180, placeholder="粘贴描述文本...", key="main_input")
    
    if not st.session_state.is_split:
        if st.button("🔍 开始 AI 拆分", type="primary", use_container_width=True):
            if raw:
                with st.spinner("AI 分析中..."):
                    res = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[{"role": "system", "content": "格式:分类:词|分类:词。分类限:主体,风格,部位,氛围。"}, {"role": "user", "content": raw}]
                    ).choices[0].message.content
                    st.session_state.pre_tags = [{"cat": p.split(":")[0], "val": p.split(":")[1], "ok": True} for p in res.split("|") if ":" in p]
                    st.session_state.is_split = True
                    st.rerun()
    else:
        st.subheader("确认拆解结果")
        save_list = []
        for i, t in enumerate(st.session_state.pre_tags):
            if st.checkbox(f"【{t['cat']}】{t['val']}", value=True, key=f"p_{i}"):
                save_list.append(t)
        
        c1, c2 = st.columns(2)
        if c1.button("🚀 一键入云库", type="primary", use_container_width=True):
            f_map = {"主体":"subjects.txt","风格":"styles.txt","部位":"placements.txt","氛围":"vibes.txt"}
            for item in save_list:
                if item['val'] not in st.session_state.db[item['cat']]:
                    st.session_state.db[item['cat']].append(item['val'])
                    sync_git(f_map[item['cat']], st.session_state.db[item['cat']])
            st.session_state.is_split = False
            st.session_state.pre_tags = []
            st.success("入库成功！")
            st.rerun()
        if c2.button("🧹 清空重置", use_container_width=True):
            st.session_state.is_split = False
            st.session_state.pre_tags = []
            st.rerun()

# 👉 右：资产管理仓库 (固定且独立滚动)
with col_lib:
    st.subheader("📚 资产仓库")
    view_cat = st.selectbox("当前查看分类：", ["主体", "风格", "部位", "氛围"], label_visibility="collapsed")
    fav_only = st.checkbox("❤️ 只看收藏")
    st.divider()
    
    items = st.session_state.db.get(view_cat, [])
    if fav_only: items = [i for i in items if i in st.session_state.db["收藏"]]
    
    if items:
        for word in items:
            c1, c2, c3 = st.columns([6, 1, 1])
            c1.markdown(f'<div style="background:#1f1f1f; padding:5px 10px; border-radius:6px; font-size:13px; border:1px solid #333;">{word}</div>', unsafe_allow_html=True)
            if c2.button("⭐" if word in st.session_state.db["收藏"] else "🤍", key=f"f_{word}"):
                if word in st.session_state.db["收藏"]: st.session_state.db["收藏"].remove(word)
                else: st.session_state.db["收藏"].append(word)
                sync_git("favorites.txt", st.session_state.db["收藏"]); st.rerun()
            if c3.button("🗑️", key=f"d_{word}"):
                st.session_state.db[view_cat].remove(word)
                sync_git({"主体":"subjects.txt","风格":"styles.txt","部位":"placements.txt","氛围":"vibes.txt"}[view_cat], st.session_state.db[view_cat]); st.rerun()
    else:
        st.caption("暂无内容")
