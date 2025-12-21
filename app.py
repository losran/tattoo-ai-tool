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

# --- 2. 核心：云端同步写入逻辑 (强化容错版) ---
def github_sync_file(category, content_list):
    # 强制映射，防止 AI 返回的分类名对不上文件
    file_map = {
        "主体": "data/subjects.txt", 
        "风格": "data/styles.txt", 
        "部位": "data/placements.txt", 
        "氛围": "data/vibes.txt"
    }
    path = file_map.get(category)
    if not path: return
    
    url = f"https://api.github.com/repos/{REPO}/contents/{path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    # 获取 SHA
    res = requests.get(url, headers=headers).json()
    if 'sha' in res:
        new_txt = "\n".join(content_list)
        payload = {
            "message": f"Update {category}",
            "content": base64.b64encode(new_txt.encode('utf-8')).decode('utf-8'),
            "sha": res['sha']
        }
        # 执行写入
        requests.put(url, headers=headers, json=payload)

# --- 3. 初始加载：从 GitHub 读取现有内容 ---
def load_assets():
    db = {"主体": [], "风格": [], "部位": [], "氛围": []}
    sections = {"主体": "data/subjects.txt", "风格": "data/styles.txt", "部位": "data/placements.txt", "氛围": "data/vibes.txt"}
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    for cat, path in sections.items():
        url = f"https://api.github.com/repos/{REPO}/contents/{path}"
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            content = base64.b64decode(r.json()['content']).decode('utf-8')
            db[cat] = [line.strip() for line in content.splitlines() if line.strip()]
    return db

# 仅在第一次启动时加载
if 'db' not in st.session_state:
    st.session_state.db = load_assets()

# --- 4. 样式配置 (保持 Figma 风格) ---
st.markdown("""
    <style>
    .chip-box { display: inline-flex; align-items: center; background: rgba(0, 113, 227, 0.08); color: #0071e3 !important; padding: 2px 10px; border-radius: 100px; font-size: 13px; margin: 4px; border: 1px solid rgba(0, 113, 227, 0.1); }
    .group-header { font-size: 11px; font-weight: 700; color: #86868b; margin: 15px 0 5px 5px; text-transform: uppercase; }
    .res-card { background: rgba(128, 128, 128, 0.05); padding: 16px; border-radius: 12px; border: 1px solid rgba(128, 128, 128, 0.1); margin-bottom: 15px; }
    .stButton > button { border: none !important; background: transparent !important; color: #ff3b30 !important; padding: 0 !important; min-height: 0 !important; }
    </style>
""", unsafe_allow_html=True)

# --- 5. 侧边栏：提取逻辑 ---
with st.sidebar:
    st.header("📥 智能提取入库")
    input_text = st.text_area("粘贴样板描述", height=150, placeholder="粘贴描述文本...", key="sidebar_input")
    
    if st.button("开始拆解入库", type="primary", use_container_width=True):
        if input_text:
            with st.spinner('AI 正在拆解并同步云端...'):
                # 强化 Prompt，要求 AI 必须按精准分类输出
                res = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "system", "content": "格式: 分类:【分组】/内容。分类必选:主体,风格,部位,氛围。"}]
                ).choices[0].message.content
                
                # 核心解析与强制匹配
                for part in res.split("|"):
                    if ":" in part:
                        k, v = part.split(":", 1)
                        # 强行匹配分类
                        matched_cat = None
                        if "主体" in k: matched_cat = "主体"
                        elif "风格" in k: matched_cat = "风格"
                        elif "部位" in k: matched_cat = "部位"
                        elif "氛围" in k: matched_cat = "氛围"
                        
                        if matched_cat and v.strip() not in st.session_state.db[matched_cat]:
                            st.session_state.db[matched_cat].append(v.strip())
                            github_sync_file(matched_cat, st.session_state.db[matched_cat])
                
                st.success("入库成功！云端已同步。")
                st.rerun()

# --- 6. 主看板显示 ---
st.title("🎨 纹身设计资产看板")
cols = st.columns(4)
for i, sec in enumerate(["主体", "风格", "部位", "氛围"]):
    with cols[i]:
        st.markdown(f"### {sec}")
        # 分组逻辑
        grouped = {}
        for it in st.session_state.db[sec]:
            g = it.split('/')[0] if '/' in it else "未分组"
            name = it.split('/')[1] if '/' in it else it
            grouped.setdefault(g, []).append(name)
        
        for g_name, g_items in grouped.items():
            st.markdown(f"<div class='group-header'>{g_name}</div>", unsafe_allow_html=True)
            for item in g_items:
                c1, c2 = st.columns([5, 1])
                with c1: st.markdown(f"<div class='chip-box'>{item}</div>", unsafe_allow_html=True)
                with c2:
                    if st.button("×", key=f"del_{sec}_{item}_{random.random()}"):
                        full_name = f"{g_name}/{item}" if g_name != "未分组" else item
                        st.session_state.db[sec].remove(full_name)
                        github_sync_file(sec, st.session_state.db[sec])
                        st.rerun()

st.markdown("<br><hr>", unsafe_allow_html=True)

# --- 7. 灵感生成逻辑 (保持不变) ---
st.header("🎲 灵感批量生成")
count = st.select_slider("选择生成数量", options=[1, 3, 5, 10], value=3)
if st.button("✨ 立即生成创意组合", use_container_width=True):
    if all(len(v) > 0 for v in st.session_state.db.values()):
        st.balloons()
        res_cols = st.columns(2)
        for i in range(count):
            p_list = [random.choice(st.session_state.db[k]).split('/')[-1] for k in ["主体", "风格", "部位", "氛围"]]
            s, sty, p, v = p_list
            with res_cols[i % 2]:
                st.markdown(f'<div class="res-card"><b>PROPOSAL {i+1}</b><br>{sty}风格 - {s}<br><small>部位: {p} | 氛围: {v}</small></div>', unsafe_allow_html=True)
