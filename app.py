import streamlit as st
from openai import OpenAI
import random, requests, base64, time

# --- 1. 核心配置 ---
client = OpenAI(api_key=st.secrets["DEEPSEEK_KEY"], base_url="https://api.deepseek.com")
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO = "losran/tattoo-ai-tool"

# 页面配置：隐藏侧边栏按钮
st.set_page_config(page_title="Tattoo Pro Station", layout="wide", initial_sidebar_state="collapsed")

# --- 2. 增强型 CSS (强制固定左下角 + 隐藏顶部菜单) ---
st.markdown("""
    <style>
    /* 彻底隐藏顶部菜单栏和页眉 */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton {display:none;}
    [data-testid="stHeader"] {display:none;}

    .main { background-color: #0d0d0d; }
    .block-container { padding: 0 !important; max-width: 100% !important; }
    
    /* 左侧固定栏 */
    [data-testid="stColumn"]:nth-child(1) {
        position: fixed; left: 0; top: 0; bottom: 0;
        width: 120px !important;
        background: #161b22;
        border-right: 1px solid #333;
        z-index: 1001;
        padding-top: 20px !important;
    }

    /* 左下角看板锁死 */
    .sticky-stats {
        position: fixed; left: 10px; bottom: 20px;
        width: 100px; z-index: 1002;
    }
    .nav-item {
        background: rgba(255, 255, 255, 0.03); border: 1px solid #333;
        border-radius: 8px; padding: 8px; margin-top: 8px; text-align: center;
    }
    .nav-label { font-size: 11px; color: #888; }
    .nav-val { font-size: 16px; font-weight: bold; color: #58a6ff; }

    /* 中间操作区：腾出左边位置 */
    [data-testid="stColumn"]:nth-child(2) {
        margin-left: 140px !important; margin-right: 400px !important;
        width: auto !important; padding: 40px !important;
    }

    /* 右侧资产库 */
    [data-testid="stColumn"]:nth-child(3) {
        position: fixed; right: 0; top: 0; bottom: 0;
        width: 380px !important; background: #0d1117;
        border-left: 1px solid #333; padding: 40px 20px !important;
        z-index: 1000; overflow-y: auto;
    }

    /* 预览标签视觉 */
    .stCheckbox {
        background: #1f2428 !important; padding: 10px !important;
        border-radius: 10px !important; border: 1px solid #333 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. 数据读写逻辑 ---
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

# 状态管理
if 'db' not in st.session_state:
    st.session_state.db = {k: get_git(v) for k, v in {"主体":"subjects.txt","风格":"styles.txt","部位":"placements.txt","氛围":"vibes.txt","收藏":"favorites.txt"}.items()}
if 'is_split' not in st.session_state: st.session_state.is_split = False
if 'pre_tags' not in st.session_state: st.session_state.pre_tags = []
# 用于清空输入栏的 key
if "input_val" not in st.session_state: st.session_state.input_val = ""

# --- 4. 界面布局 ---
col_nav, col_mid, col_lib = st.columns([12, 53, 35])

# 👉 左：Logo 顶部，统计固定底部
with col_nav:
    st.markdown("### 🌀")
    stats_html = '<div class="sticky-stats">'
    for k in ["主体", "风格", "部位", "氛围"]:
        num = len(st.session_state.db.get(k, []))
        stats_html += f'<div class="nav-item"><div class="nav-label">{k}</div><div class="nav-val">{num}</div></div>'
    stats_html += '</div>'
    st.markdown(stats_html, unsafe_allow_html=True)

# 👉 中：中间工作台
with col_mid:
    st.title("✨ 智能提取入库")
    
    # 逻辑：通过更改 key 实现自动清空
    raw = st.text_area("输入样板提示词", height=150, placeholder="粘贴文本后点击拆分...", key="input_area")
    
    if not st.session_state.is_split:
        if st.button("🔍 开始 AI 拆分", type="primary", use_container_width=True):
            if raw:
                with st.spinner("AI 拆解中..."):
                    res = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[{"role": "system", "content": "格式:分类:词|分类:词。分类限:主体,风格,部位,氛围。"}, {"role": "user", "content": raw}]
                    ).choices[0].message.content
                    st.session_state.pre_tags = [{"cat": p.split(":")[0], "val": p.split(":")[1], "ok": True} for p in res.split("|") if ":" in p]
                    st.session_state.is_split = True
                    # 清空输入内容的逻辑提示：由于 Streamlit 限制，下一次 rerun 时输入栏会重置
                    st.rerun()
    else:
        st.markdown("### 📋 确认拆解结果")
        save_list = []
        for i, tag in enumerate(st.session_state.pre_tags):
            if st.checkbox(f"【{tag['cat']}】{tag['val']}", value=True, key=f"t_{i}"):
                save_list.append(tag)
        
        st.write("")
        # 按钮位置调整：一键入云库移动到下方
        c_save, c_reset = st.columns(2)
        with c_save:
            if st.button("🚀 一键入云库", type="primary", use_container_width=True):
                f_map = {"主体":"subjects.txt","风格":"styles.txt","部位":"placements.txt","氛围":"vibes.txt"}
                for t in save_list:
                    if t['val'] not in st.session_state.db[t['cat']]:
                        st.session_state.db[t['cat']].append(t['val'])
                        sync_git(f_map[t['cat']], st.session_state.db[t['cat']])
                st.session_state.is_split = False
                st.session_state.pre_tags = []
                st.success("入库完成！")
                st.rerun()
        with c_reset:
            if st.button("🧹 撤销并清空", use_container_width=True):
                st.session_state.is_split = False
                st.session_state.pre_tags = []
                st.rerun()

# 👉 右：资产仓库
with col_lib:
    st.subheader("📚 资产管理仓库")
    view_cat = st.selectbox("当前查看：", ["主体", "风格", "部位", "氛围"], label_visibility="collapsed")
    st.divider()
    
    items = st.session_state.db.get(view_cat, [])
    for word in items:
        r = st.columns([6, 1, 1])
        r[0].write(f"`{word}`")
        if r[1].button("⭐", key=f"fav_{word}"):
            pass 
        if r[2].button("🗑️", key=f"del_{word}"):
            st.session_state.db[view_cat].remove(word)
            sync_git({"主体":"subjects.txt","风格":"styles.txt","部位":"placements.txt","氛围":"vibes.txt"}[view_cat], st.session_state.db[view_cat])
            st.rerun()
