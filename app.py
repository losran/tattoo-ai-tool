import streamlit as st
from openai import OpenAI
import random, requests, base64, time

# --- 1. 配置与初始化 ---
client = OpenAI(api_key=st.secrets["DEEPSEEK_KEY"], base_url="https://api.deepseek.com")
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO = "losran/tattoo-ai-tool"

st.set_page_config(page_title="Tattoo Pro Station", layout="wide", initial_sidebar_state="collapsed")

# --- 2. 核心 CSS (解决排版错乱与仓库消失) ---
st.markdown("""
    <style>
    /* 隐藏所有官方干扰项 */
    #MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;} .stAppDeployButton {display:none;}
    
    .main { background-color: #0d0d0d; }
    .block-container { padding: 0 !important; max-width: 100% !important; }
    
    /* 左侧：窄边固定栏 */
    [data-testid="stColumn"]:nth-child(1) {
        position: fixed; left: 0; top: 0; bottom: 0; width: 100px !important;
        background: #161b22; border-right: 1px solid #333; z-index: 1001; padding: 20px 10px !important;
    }

    /* 左下角：资产统计看板 */
    .sticky-stats { position: fixed; left: 10px; bottom: 20px; width: 80px; z-index: 1002; }
    .nav-item { background: rgba(255, 255, 255, 0.03); border: 1px solid #333; border-radius: 8px; padding: 5px; margin-top: 5px; text-align: center; }
    .nav-label { font-size: 10px; color: #888; }
    .nav-val { font-size: 14px; font-weight: bold; color: #58a6ff; }

    /* 中间：生产工作区 (腾出左右间距) */
    [data-testid="stColumn"]:nth-child(2) {
        margin-left: 110px !important; margin-right: 360px !important;
        width: auto !important; padding: 40px 30px !important;
    }

    /* 右侧：资产仓库固定栏 (确保独立滚动) */
    [data-testid="stColumn"]:nth-child(3) {
        position: fixed; right: 0; top: 0; bottom: 0; width: 350px !important;
        background: #0d1117; border-left: 1px solid #333; padding: 30px 20px !important;
        z-index: 1000; overflow-y: auto !important;
    }

    /* 按钮美化 */
    .stButton > button { border-radius: 8px !important; font-weight: 500 !important; }
    .stCheckbox { background: #1f2428 !important; padding: 8px !important; border-radius: 8px !important; border: 1px solid #333 !important; }
    </style>
""", unsafe_allow_html=True)

# --- 3. 云端数据 I/O ---
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

# 资产状态初始化
if 'db' not in st.session_state:
    st.session_state.db = {k: get_git(v) for k, v in {"主体":"subjects.txt","风格":"styles.txt","部位":"placements.txt","氛围":"vibes.txt","收藏":"favorites.txt"}.items()}
if 'is_split' not in st.session_state: st.session_state.is_split = False
if 'pre_tags' not in st.session_state: st.session_state.pre_tags = []

# --- 4. 物理三栏构建 (锁定比例防止消失) ---
col_nav, col_mid, col_lib = st.columns([10, 55, 35])

# 👉 左：Logo 顶部，资产锁死底部
with col_nav:
    st.markdown("### 🌀")
    stats_html = '<div class="sticky-stats">'
    for k in ["主体", "风格", "部位", "氛围"]:
        num = len(st.session_state.db.get(k, []))
        stats_html += f'<div class="nav-item"><div class="nav-label">{k}</div><div class="nav-val">{num}</div></div>'
    stats_html += '</div>'
    st.markdown(stats_html, unsafe_allow_html=True)

# 👉 中：动态生产区 (工作沙盒)
with col_mid:
    st.title("✨ 智能提取入库")
    
    # 输入栏：拆分完即隐藏，保持界面清爽
    if not st.session_state.is_split:
        raw_text = st.text_area("输入样板提示词", height=200, placeholder="粘贴文本后点击拆分...", key="input_area")
        if st.button("🔍 开始 AI 智能拆分", type="primary", use_container_width=True):
            if raw_text:
                with st.spinner("AI 深度解析中..."):
                    res = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[{"role": "system", "content": "格式:分类:词|分类:词。分类限:主体,风格,部位,氛围。"}, {"role": "user", "content": raw_text}]
                    ).choices[0].message.content
                    st.session_state.pre_tags = [{"cat": p.split(":")[0], "val": p.split(":")[1], "ok": True} for p in res.split("|") if ":" in p]
                    st.session_state.is_split = True
                    st.rerun()
    else:
        # 预览确认区
        st.markdown("### 📋 确认拆解结果")
        st.info("勾选需要入库的标签：")
        save_list = []
        for i, tag in enumerate(st.session_state.pre_tags):
            if st.checkbox(f"【{tag['cat']}】{tag['val']}", value=True, key=f"t_{i}"):
                save_list.append(tag)
        
        st.write("")
        # 底部按钮区：入库与重置并排
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
                st.success("资产已同步云库！")
                st.rerun()
        with c_reset:
            if st.button("🧹 撤销并清空", use_container_width=True):
                st.session_state.is_split = False
                st.session_state.pre_tags = []
                st.rerun()

# 👉 右：资产管理仓库 (复活并强化)
with col_lib:
    st.markdown("### 📚 资产仓库")
    view_cat = st.selectbox("当前查看分类：", ["主体", "风格", "部位", "氛围"], label_visibility="collapsed")
    st.divider()
    
    items = st.session_state.db.get(view_cat, [])
    if items:
        for word in items:
            c_tag, c_fav, c_del = st.columns([6, 1, 1])
            c_tag.markdown(f'<div style="background:#1f1f1f; padding:5px 10px; border-radius:6px; font-size:13px; border:1px solid #333;">{word}</div>', unsafe_allow_html=True)
            # 收藏
            is_fav = word in st.session_state.db["收藏"]
            if c_fav.button("⭐" if is_fav else "🤍", key=f"fav_{word}"):
                if is_fav: st.session_state.db["收藏"].remove(word)
                else: st.session_state.db["收藏"].append(word)
                sync_git("favorites.txt", st.session_state.db["收藏"]); st.rerun()
            # 删除
            if c_del.button("🗑️", key=f"del_{word}"):
                st.session_state.db[view_cat].remove(word)
                sync_git({"主体":"subjects.txt","风格":"styles.txt","部位":"placements.txt","氛围":"vibes.txt"}[view_cat], st.session_state.db[view_cat]); st.rerun()
    else:
        st.caption("空空如也，快去中间进货！")
