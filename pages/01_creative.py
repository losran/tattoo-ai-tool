import streamlit as st
from style_manager import apply_pro_style
import requests, base64, random, time, json, urllib.parse
from openai import OpenAI

# 📍 傻瓜调用：全站视觉一键同步
apply_pro_style()

# --- 1. 核心配置 ---
client = OpenAI(api_key=st.secrets["DEEPSEEK_KEY"], base_url="https://api.deepseek.com")
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO = "losran/tattoo-ai-tool"

WAREHOUSE = {
    "Subject": "data/subjects.txt", 
    "Action": "data/actions.txt", 
    "Style": "data/styles.txt", 
    "Mood": "data/moods.txt", 
    "Usage": "data/usage.txt"
}
GALLERY_FILE = "gallery/inspirations.txt"

# --- 2. 工具函数 ---
def get_github_data(path):
    url = f"https://api.github.com/repos/{REPO}/contents/{path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            return [line.strip() for line in base64.b64decode(resp.json()['content']).decode().splitlines() if line.strip()]
    except: pass
    return []

def save_to_github(path, data_list):
    url = f"https://api.github.com/repos/{REPO}/contents/{path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        get_resp = requests.get(url, headers=headers, timeout=10).json()
        content_str = "\n".join(list(set(data_list)))
        b64_content = base64.b64encode(content_str.encode()).decode()
        requests.put(url, headers=headers, json={"message": "update", "content": b64_content, "sha": get_resp.get('sha')}, timeout=15)
        return True
    except: return False

# --- 3. UI 布局与状态初始化 ---
st.set_page_config(layout="wide", page_title="Creative Engine")

# 初始化 Session State
for key in ['selected_prompts', 'generated_cache', 'polished_text', 'manual_editor']:
    if key not in st.session_state:
        if 'editor' in key or 'text' in key: st.session_state[key] = ""
        else: st.session_state[key] = []

# 📍 保持你的暗黑审美 CSS
st.markdown("""
<style>
    .stApp { background-color: #0e1117; font-family: "PingFang SC", sans-serif; }
    div[data-testid="stButton"] > button {
        width: 100%; background-color: #161b22 !important;
        border: 1px solid #30363d !important; border-radius: 10px !important;
        padding: 22px !important; text-align: left !important; color: #8b949e !important;
    }
    div[data-testid="stButton"] > button[kind="primary"] {
        border: 2px solid #ff4b4b !important;
        background-color: #211d1d !important; color: #ffffff !important;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #ff4b4b 0%, #d62f2f 100%) !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("🎨 创意引擎")

col_main, col_gallery = st.columns([5, 2.5])

# --- 右侧：仓库管理 (保持不动) ---
with col_gallery:
    st.subheader("📦 仓库管理")
    mode = st.radio("模式", ["素材仓库", "灵感成品"], horizontal=True)
    if mode == "素材仓库":
        cat = st.selectbox("当前分类", list(WAREHOUSE.keys()))
        words = get_github_data(WAREHOUSE[cat])
        if words:
            selected_items = []
            with st.container(height=500, border=True):
                for w in words:
                    if st.checkbox(f" {w}", key=f"manage_{cat}_{w}"): selected_items.append(w)
            if selected_items:
                if st.button("➕ 导入到组合输入框", use_container_width=True):
                    st.session_state.manual_editor = f"{st.session_state.manual_editor} {' '.join(selected_items)}".strip()
                    st.rerun()
                if st.button(f"🗑️ 删除选中项", type="primary", use_container_width=True):
                    remaining = [w for w in words if w not in selected_items]
                    save_to_github(WAREHOUSE[cat], remaining); st.rerun()
    else:
        insps = get_github_data(GALLERY_FILE)
        if insps:
            sel_insps = []
            with st.container(height=500, border=True):
                for i in insps:
                    if st.checkbox(i, key=f"del_i_{hash(i)}"): sel_insps.append(i)
            if sel_insps and st.button("🗑️ 删除勾选灵感", type="primary"):
                remaining = [i for i in insps if i not in sel_insps]
                save_to_github(GALLERY_FILE, remaining); st.rerun()

# --- 左侧：核心生成区 ---
with col_main:
    # 1. 顶部配置
    col_cfg1, col_cfg2 = st.columns(2)
    with col_cfg1: num = st.slider("生成方案数量", 1, 10, 6)
    with col_cfg2: chaos_level = st.slider("混乱度 (Chaos)", 0, 100, 50)
    
    st.session_state.manual_editor = st.text_area("✍️ 组合输入框", value=st.session_state.manual_editor)

    # 2. 🔥 激发按钮 (放在逻辑最前面)
    if st.button("🔥 激发创意组合", type="primary", use_container_width=True):
        st.session_state.polished_text = "" 
        st.session_state.generated_cache = []
        st.session_state.selected_prompts = []
        
        db_all = {k: get_github_data(v) for k, v in WAREHOUSE.items()}
        
        if not any(db_all.values()):
            st.error("⚠️ 仓库是空的！")
        else:
            for _ in range(num):
                current_tags = st.session_state.manual_editor.split()
                # 📍 必选分类对齐仓库
                MANDATORY_KEYS = ['Subject', 'Style'] 
                SIDE_KEYS = [k for k in db_all.keys() if k not in MANDATORY_KEYS and db_all[k]]

                for key in MANDATORY_KEYS:
                    if key in db_all and db_all[key]:
                        current_tags.append(random.choice(db_all[key]))
                
                if SIDE_KEYS:
                    extra_count = 2 if chaos_level < 30 else (5 if chaos_level < 70 else 8)
                    for _ in range(extra_count):
                        rand_cat = random.choice(SIDE_KEYS)
                        current_tags.append(random.choice(db_all[rand_cat]))
                
                combined_p = " + ".join(list(dict.fromkeys(filter(None, current_tags))))
                st.session_state.generated_cache.append(combined_p)
            st.rerun()

    # 3. 🎲 方案展示与筛选 (放在生成按钮之后，确保即时渲染)
    if st.session_state.generated_cache:
        st.divider()
        st.subheader("🎲 方案筛选 (点击卡片进行调配)")
        
        cols = st.columns(2)
        for idx, p in enumerate(st.session_state.generated_cache):
            with cols[idx % 2]:
                is_sel = p in st.session_state.selected_prompts
                # 📍 这里是你的卡片按钮，高亮逻辑完全保留
                if st.button(f"方案 {idx+1}\n\n{p}", key=f"sel_{idx}", type="primary" if is_sel else "secondary"):
                    if is_sel: st.session_state.selected_prompts.remove(p)
                    else: st.session_state.selected_prompts.append(p)
                    st.rerun()

    # 4. 🎨 确认方案并开始润色 (当有选中项且未完成润色时显示)
    if st.session_state.selected_prompts and not st.session_state.polished_text:
        st.divider()
        if st.button("✨ 确认方案并开始润色", type="primary", use_container_width=True):
            with st.spinner("AI 正在注入艺术灵魂..."):
                combined_input = "\n".join([f"方案{i+1}: {p}" for i, p in enumerate(st.session_state.selected_prompts)])
                # 📍 保持你的扩写咒语
                system_prompt = f"""你是一位【资深纹身贴文案策划】。用户的输入是一组标签。你的任务是基于这些标签，**大幅扩写**成一段画面感极强、细节丰富、描述具体的中文文案。强制后缀必须自然融入“纹身贴”这三个字！当前混乱度 {chaos_level}/100。格式：**方案X：** [描述]"""
                
                try:
                    res = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": combined_input}],
                        temperature=0.7 + (chaos_level / 200)
                    ).choices[0].message.content
                    st.session_state.polished_text = res
                    st.rerun()
                except Exception as e:
                    st.error(f"润色失败: {e}")

    # 5. 展示润色成品 (保持你的存档和发送功能)
    if st.session_state.polished_text:
        st.divider()
        st.subheader("🎨 艺术润色成品")
        final_content = st.text_area("润色文案预览：", st.session_state.polished_text, height=400)
        
        c_btn1, c_btn2, c_btn3 = st.columns(3)
        with c_btn1:
            if st.button("💾 存入成品库", use_container_width=True):
                current = get_github_data(GALLERY_FILE)
                new = [l.strip() for l in final_content.split('\n') if l.strip() and '方案' not in l]
                current.extend(new); save_to_github(GALLERY_FILE, current); st.success("已存档")
        with c_btn2:
            if st.button("🚀 发送到自动化", type="primary", use_container_width=True):
                st.session_state.auto_input_cache = final_content
                st.switch_page("pages/02_automation.py")
        with c_btn3:
            if st.button("🔄 重新调配", use_container_width=True):
                st.session_state.polished_text = ""
                st.session_state.selected_prompts = []
                st.rerun()
