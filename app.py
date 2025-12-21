import streamlit as st
from openai import OpenAI
import random
import requests
import base64

# --- 1. 配置与安全读取 ---
client = OpenAI(api_key=st.secrets["DEEPSEEK_KEY"], base_url="https://api.deepseek.com")
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO = "losran/tattoo-ai-tool"

st.set_page_config(page_title="Tattoo Studio Pro", layout="wide", initial_sidebar_state="collapsed")

# --- 2. 视觉样式 (Figma 胶囊 + 移动端自适应) ---
st.markdown("""
    <style>
    .chip-box {
        display: inline-flex;
        align-items: center;
        background: rgba(0, 113, 227, 0.08);
        color: #0071e3 !important;
        padding: 2px 10px;
        border-radius: 100px;
        font-size: 13px;
        margin: 4px;
        border: 1px solid rgba(0, 113, 227, 0.1);
    }
    .group-header {
        font-size: 11px;
        font-weight: 700;
        color: #86868b;
        margin: 15px 0 5px 5px;
        text-transform: uppercase;
    }
    .res-card {
        background: rgba(128, 128, 128, 0.05);
        padding: 16px;
        border-radius: 12px;
        border: 1px solid rgba(128, 128, 128, 0.1);
        margin-bottom: 15px;
    }
    /* 极致对齐的删除按钮 */
    .stButton > button {
        border: none !important;
        background: transparent !important;
        color: #ff3b30 !important;
        padding: 0 !important;
        min-height: 0 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. 云端同步核心逻辑 ---
def github_sync(category, content_list):
    paths = {"主体": "data/subjects.txt", "风格": "data/styles.txt", "部位": "data/placements.txt", "氛围": "data/vibes.txt"}
    url = f"https://api.github.com/repos/{REPO}/contents/{paths[category]}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    r = requests.get(url, headers=headers).json()
    if 'sha' in r:
        new_txt = "\n".join(content_list)
        payload = {
            "message": f"Cloud Sync {category}",
            "content": base64.b64encode(new_txt.encode('utf-8')).decode('utf-8'),
            "sha": r['sha']
        }
        requests.put(url, headers=headers, json=payload)

# --- 4. 初始加载：开机从 GitHub 读取数据 ---
def load_all_assets():
    db = {"主体": [], "风格": [], "部位": [], "氛围": []}
    paths = {"主体": "data/subjects.txt", "风格": "data/styles.txt", "部位": "data/placements.txt", "氛围": "data/vibes.txt"}
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    for cat, path in paths.items():
        url = f"https://api.github.com/repos/{REPO}/contents/{path}"
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            content = base64.b64decode(r.json()['content']).decode('utf-8')
            db[cat] = [line.strip() for line in content.splitlines() if line.strip()]
    return db

if 'db' not in st.session_state:
    with st.spinner('正在同步云端资产...'):
        st.session_state.db = load_all_assets()
if 'input_box' not in st.session_state:
    st.session_state.input_box = ""

# --- 5. 侧边栏：提取入库逻辑 ---
with st.sidebar:
    st.header("📥 智能提取入库")
    # 状态绑定实现自动清空
    raw_input = st.text_area("粘贴样板描述", value=st.session_state.input_box, height=150, key="current_input")
    
    if st.button("开始拆解入库", type="primary", use_container_width=True):
        if st.session_state.current_input:
            with st.spinner('AI 正在智能分组入库...'):
                res = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "system", "content": "按格式拆解: 分类:【分组】/零件。分类仅限:主体,风格,部位,氛围。"}]
                ).choices[0].message.content
                
                # 更新本地和云端
                for item in res.split("|"):
                    if ":" in item:
                        k, v = item.split(":", 1)
                        for sec in st.session_state.db.keys():
                            if sec in k and v.strip() not in st.session_state.db[sec]:
                                st.session_state.db[sec].append(v.strip())
                                github_sync(sec, st.session_state.db[sec])
                
                st.session_state.input_box = "" # 清空
                st.success("入库成功！")
                st.rerun()

# --- 6. 主界面：看板资产管理 ---
st.title("🎨 纹身设计资产看板")

cols = st.columns(4)
sections = ["主体", "风格", "部位", "氛围"]

for i, sec in enumerate(sections):
    with cols[i]:
        st.markdown(f"### {sec}")
        items = st.session_state.db[sec]
        # 智能分组排序
        grouped = {}
        for it in items:
            g = it.split('/')[0] if '/' in it else "未分组"
            name = it.split('/')[1] if '/' in it else it
            grouped.setdefault(g, []).append(name)
            
        for g_name, g_items in grouped.items():
            st.markdown(f"<div class='group-header'>{g_name}</div>", unsafe_allow_html=True)
            for item in g_items:
                c1, c2 = st.columns([5, 1])
                with c1:
                    st.markdown(f"<div class='chip-box'>{item}</div>", unsafe_allow_html=True)
                with c2:
                    if st.button("×", key=f"del_{sec}_{item}_{random.random()}"):
                        full_name = f"{g_name}/{item}" if g_name != "未分组" else item
                        st.session_state.db[sec].remove(full_name)
                        github_sync(sec, st.session_state.db[sec]) # 同步删除
                        st.rerun()

st.markdown("<br><hr>", unsafe_allow_html=True)

# --- 7. 灵感批量生成 ---
st.header("🎲 灵感批量生成")
count = st.select_slider("选择生成数量", options=[1, 3, 5, 10], value=3)

if st.button("✨ 立即生成创意组合", use_container_width=True):
    db = st.session_state.db
    if all(len(v) > 0 for v in db.values()):
        st.balloons()
        res_cols = st.columns(2)
        for i in range(count):
            # 抽卡逻辑
            parts = [random.choice(db[k]) for k in sections]
            clean_parts = [p.split('/')[-1] for p in parts]
            s, sty, p, v = clean_parts
            
            with res_cols[i % 2]:
                st.markdown(f"""
                <div class="res-card">
                    <div style="color:#0071e3; font-size:12px; font-weight:700;">PROPOSAL {i+1}</div>
                    <div style="font-size:18px; margin:8px 0; font-weight:600;">{sty}风格 - {s}</div>
                    <div style="font-size:14px; opacity:0.8; margin-bottom:10px;">部位：{p} | 氛围：{v}</div>
                    <div style="background:rgba(0,113,227,0.05); padding:10px; border-radius:8px; font-size:11px; font-family:monospace;">
                        Prompt: {s}, {sty} tattoo style, {v}, on {p}, white background, high detail --v 6.0
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.warning("库里没货，请先提取素材！")
