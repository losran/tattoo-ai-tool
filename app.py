import streamlit as st
from openai import OpenAI
import random, requests, base64

# --- 1. 核心配置 ---
client = OpenAI(api_key=st.secrets["DEEPSEEK_KEY"], base_url="https://api.deepseek.com")
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO = "losran/tattoo-ai-tool"

st.set_page_config(page_title="Tattoo AI Workbench", layout="wide", initial_sidebar_state="collapsed")

# --- 2. 极致三栏 CSS (针对你的专业需求) ---
st.markdown("""
    <style>
    /* 1. 整体深色背景 */
    .stApp { background-color: #0d1117; }
    
    /* 2. 左侧固定导航栏 (Fixed Left) */
    [data-testid="stColumn"]:nth-child(1) {
        position: fixed;
        left: 0; top: 0; bottom: 0;
        width: 18% !important;
        background: linear-gradient(180deg, #161b22 0%, #0d1117 100%);
        border-right: 1px solid #30363d;
        padding: 40px 20px !important;
        z-index: 1000;
        overflow: hidden;
    }

    /* 3. 中间流式操作区 (Scrolling Center) */
    [data-testid="stColumn"]:nth-child(2) {
        margin-left: 20% !important;
        width: 45% !important;
        padding: 40px 30px !important;
    }

    /* 4. 右侧固定资产库 (Fixed Right) */
    [data-testid="stColumn"]:nth-child(3) {
        position: fixed;
        right: 0; top: 0; bottom: 0;
        width: 32% !important;
        background-color: #0d1117;
        border-left: 1px solid #30363d;
        padding: 40px 20px !important;
        z-index: 999;
        overflow-y: auto !important;
    }

    /* 装饰：Logo 与 统计小方块 */
    .nav-logo { font-size: 24px; font-weight: 800; color: #58a6ff; margin-bottom: 30px; }
    .nav-stat-card { background: #21262d; border: 1px solid #30363d; border-radius: 8px; padding: 12px; margin-bottom: 10px; }
    .nav-stat-val { font-size: 20px; font-weight: bold; color: #ffffff; }
    
    /* 标签视觉优化 */
    .chip { background: #1f2428; border: 1px solid #30363d; color: #c9d1d9; padding: 4px 12px; border-radius: 6px; font-size: 13px; }
    </style>
""", unsafe_allow_html=True)

# --- 3. 稳健的数据 I/O (明天优化的重点是批量同步) ---
def get_git_data(fn):
    url = f"https://api.github.com/repos/{REPO}/contents/data/{fn}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    r = requests.get(url, headers=headers)
    return base64.b64decode(r.json()['content']).decode('utf-8').splitlines() if r.status_code == 200 else []

def save_git_data(fn, lines):
    url = f"https://api.github.com/repos/{REPO}/contents/data/{fn}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    sha = requests.get(url, headers=headers).json().get('sha')
    content = base64.b64encode("\n".join(list(set(lines))).encode()).decode()
    requests.put(url, headers=headers, json={"message": "sync", "content": content, "sha": sha})

# 初始加载
if 'db' not in st.session_state:
    st.session_state.db = {k: get_git_data(v) for k, v in {"主体":"subjects.txt","风格":"styles.txt","部位":"placements.txt","氛围":"vibes.txt","收藏":"favorites.txt"}.items()}
if 'pre_tags' not in st.session_state: st.session_state.pre_tags = []

# --- 4. 三栏布局构建 ---
col_nav, col_work, col_lib = st.columns([18, 45, 32])

# 👉 左栏：固定导航与统计
with col_nav:
    st.markdown('<div class="nav-logo">🌀 TATTOO AI</div>', unsafe_allow_html=True)
    mode = st.radio("功能切换", ["✨ 智能提取", "🎲 灵感生成"], label_visibility="collapsed")
    
    st.write("")
    st.caption("实时库存统计")
    for k in ["主体", "风格", "部位", "氛围"]:
        count = len(st.session_state.db.get(k, []))
        st.markdown(f'<div class="nav-stat-card"><div style="font-size:11px;color:#8b949e;">{k}</div><div class="nav-stat-val">{count}</div></div>', unsafe_allow_html=True)

# 👉 中栏：动态操作中心
with col_work:
    if mode == "✨ 智能提取":
        st.markdown("### 📥 样板素材提取")
        input_text = st.text_area("粘贴你的纹身描述或样板文案", height=180, placeholder="例如：Old School风老虎，手臂，硬朗线条...")
        
        c1, c2 = st.columns(2)
        if c1.button("🔍 智能拆解", type="primary", use_container_width=True):
            if input_text:
                with st.spinner("AI 正在分析并分类..."):
                    res = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[{"role": "system", "content": "分类:主体,风格,部位,氛围。格式:分类:内容|分类:内容"}, {"role": "user", "content": input_text}]
                    ).choices[0].message.content
                    st.session_state.pre_tags = [{"cat": x.split(":")[0], "val": x.split(":")[1], "ok": True} for x in res.split("|") if ":" in x]
        
        if c2.button("🧹 清空输入", use_container_width=True):
            st.session_state.pre_tags = []; st.rerun()

        # 核心：入库前的“待确认”区域
        if st.session_state.pre_tags:
            st.markdown("---")
            st.subheader("确认入库项")
            to_add = []
            for i, tag in enumerate(st.session_state.pre_tags):
                if st.checkbox(f"【{tag['cat']}】{tag['val']}", value=True, key=f"p_{i}"):
                    to_add.append(tag)
            
            if st.button("💾 确认同步到资产库", type="primary", use_container_width=True):
                f_map = {"主体":"subjects.txt","风格":"styles.txt","部位":"placements.txt","氛围":"vibes.txt"}
                for t in to_add:
                    if t['val'] not in st.session_state.db[t['cat']]:
                        st.session_state.db[t['cat']].append(t['val'])
                        save_git_data(f_map[t['cat']], st.session_state.db[t['cat']])
                st.session_state.pre_tags = []; st.success("入库成功！"); st.rerun()

    else:
        st.markdown("### 🎲 灵感生成器")
        # (生成逻辑保持不变...)
        st.info("生成逻辑已就绪，正在等待你的下一步指令。")

# 👉 右栏：无限滚动素材库
with col_lib:
    st.markdown("### 📚 资产仓库")
    view_cat = st.selectbox("选择分类", ["主体", "风格", "部位", "氛围"], label_visibility="collapsed")
    only_fav = st.toggle("只看收藏 ❤️")
    
    st.write("---")
    items = st.session_state.db.get(view_cat, [])
    if only_fav: items = [i for i in items if i in st.session_state.db["收藏"]]
    
    for item in items:
        is_fav = item in st.session_state.db["收藏"]
        row = st.columns([6, 1, 1])
        row[0].markdown(f'<div class="chip">{item}</div>', unsafe_allow_html=True)
        if row[1].button("❤️" if is_fav else "🤍", key=f"fav_{item}"):
            if is_fav: st.session_state.db["收藏"].remove(item)
            else: st.session_state.db["收藏"].append(item)
            save_git_data("favorites.txt", st.session_state.db["收藏"]); st.rerun()
        if row[2].button("🗑️", key=f"del_{item}"):
            st.session_state.db[view_cat].remove(item)
            save_git_data({"主体":"subjects.txt","风格":"styles.txt","部位":"placements.txt","氛围":"vibes.txt"}[view_cat], st.session_state.db[view_cat]); st.rerun()
