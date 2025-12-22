import streamlit as st
from openai import OpenAI
import random, requests, base64, time

# --- 1. 基础配置 ---
client = OpenAI(api_key=st.secrets["DEEPSEEK_KEY"], base_url="https://api.deepseek.com")
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO = "losran/tattoo-ai-tool"

st.set_page_config(page_title="Tattoo Pro Station", layout="wide", initial_sidebar_state="collapsed")

# --- 2. 核心 CSS 布局修复 (解决按钮偏移和不可见问题) ---
st.markdown("""
    <style>
    .main { background-color: #0d0d0d; }
    .block-container { padding: 0 !important; max-width: 100% !important; }
    
    /* 左侧固定栏：增加宽度防止挤压 */
    [data-testid="stColumn"]:nth-child(1) {
        position: fixed; left: 0; top: 0; bottom: 0;
        width: 120px !important;
        background: #161b22;
        border-right: 1px solid #30363d;
        padding: 40px 10px !important;
        z-index: 1001;
    }

    /* 中间操作区：确保内容可见 */
    [data-testid="stColumn"]:nth-child(2) {
        margin-left: 140px !important;
        margin-right: 400px !important;
        width: auto !important;
        padding: 50px 30px !important;
        min-height: 100vh;
    }

    /* 右侧资产库 */
    [data-testid="stColumn"]:nth-child(3) {
        position: fixed; right: 0; top: 0; bottom: 0;
        width: 380px !important;
        background: #0d1117;
        border-left: 1px solid #30363d;
        padding: 40px 20px !important;
        z-index: 1000;
        overflow-y: auto;
    }

    /* 预览标签的视觉增强 */
    .stCheckbox {
        background: #1f2428 !important;
        padding: 12px 20px !important;
        border-radius: 10px !important;
        border: 1px solid #30363d !important;
        margin-bottom: 8px !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. 数据处理函数 ---
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
    if r.status_code == 200:
        return base64.b64decode(r.json()['content']).decode('utf-8').splitlines()
    return []

# 状态加载
if 'db' not in st.session_state:
    st.session_state.db = {k: get_git(v) for k, v in {"主体":"subjects.txt","风格":"styles.txt","部位":"placements.txt","氛围":"vibes.txt","收藏":"favorites.txt"}.items()}
if 'is_split' not in st.session_state: st.session_state.is_split = False
if 'pre_tags' not in st.session_state: st.session_state.pre_tags = []

# --- 4. 物理三栏构建 ---
col_nav, col_mid, col_lib = st.columns([12, 53, 35])

# 👉 左：固定统计 (修复文字重叠)
with col_nav:
    st.markdown("### 🌀")
    for k in ["主体", "风格", "部位", "氛围"]:
        num = len(st.session_state.db.get(k, []))
        st.write(f"**{k}**")
        st.code(f"{num}", language=None)

# 👉 中：流式操作区
with col_mid:
    st.title("✨ 智能提取入库")
    raw = st.text_area("输入样板提示词", height=150, placeholder="粘贴文本后点击拆分...", key="main_input")
    
    # 拆分前状态
    if not st.session_state.is_split:
        if st.button("🔍 开始 AI 拆分", type="primary", use_container_width=True):
            if raw:
                with st.spinner("AI 正在深度解析..."):
                    res = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[{"role": "system", "content": "格式:分类:词|分类:词。分类限:主体,风格,部位,氛围。"}, {"role": "user", "content": raw}]
                    ).choices[0].message.content
                    # 确保解析出的结果能被状态记住
                    st.session_state.pre_tags = [{"cat": p.split(":")[0], "val": p.split(":")[1], "ok": True} for p in res.split("|") if ":" in p]
                    st.session_state.is_split = True
                    st.rerun()
    
    # 拆分后状态：显示预览与入库按钮
    else:
        st.markdown("### 📋 确认拆解结果")
        st.info("勾选你想要保存的标签：")
        
        save_items = []
        # 这里强制在 col_mid 下渲染复选框
        for i, tag in enumerate(st.session_state.pre_tags):
            if st.checkbox(f"【{tag['cat']}】 {tag['val']}", value=True, key=f"tag_preview_{i}"):
                save_items.append(tag)
        
        st.write("") # 留空
        
        c_save, c_reset = st.columns(2)
        with c_save:
            if st.button("🚀 一键入云库", type="primary", use_container_width=True):
                f_map = {"主体":"subjects.txt","风格":"styles.txt","部位":"placements.txt","氛围":"vibes.txt"}
                for item in save_items:
                    if item['val'] not in st.session_state.db[item['cat']]:
                        st.session_state.db[item['cat']].append(item['val'])
                        sync_git(f_map[item['cat']], st.session_state.db[item['cat']])
                st.session_state.is_split = False
                st.session_state.pre_tags = []
                st.success("资产已同步！")
                st.rerun()
        with c_reset:
            if st.button("🧹 清空并返回", use_container_width=True):
                st.session_state.is_split = False
                st.session_state.pre_tags = []
                st.rerun()

# 👉 右：资产仓库
with col_lib:
    st.subheader("📚 资产仓库")
    view_cat = st.selectbox("当前分类：", ["主体", "风格", "部位", "氛围"], label_visibility="collapsed")
    st.divider()
    
    items = st.session_state.db.get(view_cat, [])
    for word in items:
        row = st.columns([6, 1, 1])
        row[0].write(f"`{word}`")
        if row[1].button("⭐", key=f"f_{word}"):
            pass # 收藏逻辑
        if row[2].button("🗑️", key=f"d_{word}"):
            st.session_state.db[view_cat].remove(word)
            sync_git({"主体":"subjects.txt","风格":"styles.txt","部位":"placements.txt","氛围":"vibes.txt"}[view_cat], st.session_state.db[view_cat])
            st.rerun()
