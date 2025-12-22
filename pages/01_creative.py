import streamlit as st
import requests, base64, random, time
from openai import OpenAI

# --- 1. 核心配置 (请确保 Secrets 已配置) ---
client = OpenAI(api_key=st.secrets["DEEPSEEK_KEY"], base_url="https://api.deepseek.com")
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO = "losran/tattoo-ai-tool"

WAREHOUSE = {
    "Subject": "data/subjects.txt", "Action": "data/actions.txt", 
    "Style": "data/styles.txt", "Mood": "data/moods.txt", "Usage": "data/usage.txt"
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
st.title("🎨 创意引擎")

# 📍 修正初始化逻辑：确保 manual_editor 是字符串不是列表 []
for key in ['selected_prompts', 'generated_cache', 'polished_text', 'manual_editor']:
    if key not in st.session_state:
        if 'editor' in key or 'text' in key:
            st.session_state[key] = ""
        else:
            st.session_state[key] = []

col_main, col_gallery = st.columns([5, 2.5])

# --- 右侧：仓库管理 (支持导入到输入框) ---
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
                st.divider()
                # 导入功能
                if st.button("➕ 导入到组合输入框", use_container_width=True):
                    existing = st.session_state.manual_editor
                    st.session_state.manual_editor = f"{existing} {' '.join(selected_items)}".strip()
                    st.rerun()
                # 删除功能
                if st.button(f"🗑️ 删除选中的 {len(selected_items)} 项", type="primary", use_container_width=True):
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
    # 1. 灵感配置
    st.subheader("📝 灵感调配")
    st.session_state.manual_editor = st.text_area("手动编辑或从右侧导入关键词：", value=st.session_state.manual_editor, height=80)
    
    chaos_level = st.slider("✨ 创意混乱参数 (Chaos Level)", 0, 100, 50)
    
    # 📍 生成数量按钮组：左按钮占 4，右数字占 1
    st.write("") 
    col_trigger, col_num = st.columns([4, 1])
    
    with col_num:
        # 数字输入框
        num = st.number_input("数量", 1, 15, 3, label_visibility="collapsed")
        
    with col_trigger:
        do_generate = st.button("🔥 激发创意组合", type="primary", use_container_width=True)
        
        if do_generate:
            st.session_state.polished_text = "" 
            st.session_state.generated_cache = []
            db_all = {k: get_github_data(v) for k, v in WAREHOUSE.items()}
            
            if not any(db_all.values()):
                st.error("仓库里没词，没法自动跑啊哥们！")
            else:
                for _ in range(num):
                    raw_input = st.session_state.get('manual_editor', "")
                    manual_words = raw_input.split() if isinstance(raw_input, str) else []
                    
                    # 📍 自动补充逻辑：混乱度决定了从仓库抓多少词 (即使 manual 为空也能跑)
                    extra_count = 2 if chaos_level < 30 else (4 if chaos_level < 70 else 6)
                    extra = []
                    for _ in range(extra_count):
                        random_cat = random.choice(list(db_all.keys()))
                        if db_all[random_cat]:
                            extra.append(random.choice(db_all[random_cat]))
                    
                    combined_p = " + ".join(filter(None, manual_words + extra))
                    st.session_state.generated_cache.append(combined_p)
                st.rerun()

    # 📍 方案筛选区 (注入高亮 CSS)
    if st.session_state.generated_cache and not st.session_state.get('polished_text'):
        st.divider()
        st.subheader("🎲 方案筛选 (点击卡片进行调配)")
        
        st.markdown("""
        <style>
        div[data-testid="stButton"] > button {
            border: 1px solid #333 !important;
            padding: 24px !important;
            height: auto !important;
            text-align: left !important;
            background-color: #1e1e1e !important;
            transition: 0.2s !important;
        }
        div[data-testid="stButton"] > button[kind="primary"] {
            border: 2px solid #ff4b4b !important;
            box-shadow: 0 0 12px rgba(255, 75, 75, 0.3) !important;
            background-color: #2a1a1a !important;
        }
        </style>
        """, unsafe_allow_html=True)

        cols = st.columns(2)
        for idx, p in enumerate(st.session_state.generated_cache):
            with cols[idx % 2]:
                is_sel = p in st.session_state.selected_prompts
                if st.button(f"方案 {idx+1}\n\n{p}", key=f"sel_{idx}", use_container_width=True, type="primary" if is_sel else "secondary"):
                    if is_sel: st.session_state.selected_prompts.remove(p)
                    else: st.session_state.selected_prompts.append(p)
                    st.rerun()

        if st.session_state.selected_prompts:
            if st.button("✨ 确认方案并开始润色", type="primary", use_container_width=True):
                with st.spinner("正在构思..."):
                    combined = "\n".join([f"方案{i+1}: {p}" for i, p in enumerate(st.session_state.selected_prompts)])
                    system = f"你是一个纹身艺术顾问。将标签转化为中文提示词。混乱度{chaos_level}/100。格式：'**方案X：** 内容'。"
                    res = client.chat.completions.create(model="deepseek-chat", messages=[{"role": "system", "content": system}, {"role": "user", "content": combined}]).choices[0].message.content
                    st.session_state.polished_text = res
                    st.rerun()

    # 最终结果展示
    if st.session_state.get('polished_text'):
        st.divider()
        st.subheader("🎨 艺术润色成品")
        final_content = st.text_area("润色文案预览：", st.session_state.polished_text, height=300)
        
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
                st.session_state.polished_text = ""; st.rerun()
