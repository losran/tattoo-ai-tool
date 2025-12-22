import streamlit as st
from style_manager import apply_pro_style

# 📍 傻瓜调用：全站视觉一键同步
apply_pro_style()
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
# 📍 定位：外观装修区 (插入在 st.title 下方)
st.markdown("""
<style>
    /* 1. 全局背景与字体 */
    .stApp {
        background-color: #0e1117;
        font-family: "PingFang SC", "Microsoft YaHei", sans-serif;
    }

    /* 2. 侧边栏美化 */
    section[data-testid="stSidebar"] {
        background-color: #161b22 !important;
        border-right: 1px solid #30363d;
    }

    /* 3. 灵感调配区 - 文本框与卡片 */
    div[data-testid="stForm"] {
        border: 1px solid #30363d !important;
        border-radius: 12px;
    }
    
    /* 文本输入框样式 */
    .stTextArea textarea {
        background-color: #0d1117 !important;
        border: 1px solid #30363d !important;
        border-radius: 8px !important;
        color: #c9d1d9 !important;
        font-size: 15px !important;
    }

    /* 4. 方案筛选卡片 (核心进化) */
    div[data-testid="stButton"] > button {
        width: 100%;
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
        border-radius: 10px !important;
        padding: 22px !important;
        text-align: left !important;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
        color: #8b949e !important;
    }

    /* 鼠标悬停 */
    div[data-testid="stButton"] > button:hover {
        border-color: #58a6ff !important;
        background-color: #1c2128 !important;
        transform: translateY(-2px);
    }

    /* 📍 选中状态 (红色高亮) */
    div[data-testid="stButton"] > button[kind="primary"] {
        border: 2px solid #ff4b4b !important;
        box-shadow: 0 4px 20px rgba(255, 75, 75, 0.15) !important;
        background-color: #211d1d !important;
        color: #ffffff !important;
    }

    /* 5. 激发按钮 (主操作) */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #ff4b4b 0%, #d62f2f 100%) !important;
        border: none !important;
        font-weight: 600 !important;
        letter-spacing: 1px;
    }

    /* 6. 右侧仓库管理列表 */
    .stCheckbox label {
        color: #8b949e !important;
        font-size: 14px !important;
    }
    div[data-testid="stVerticalBlock"] > div[style*="border: 1px solid"] {
        background-color: #0d1117 !important;
        border: 1px solid #30363d !important;
        border-radius: 8px !important;
    }
    
    /* 隐藏滚动条美化 */
    ::-webkit-scrollbar { width: 5px; }
    ::-webkit-scrollbar-track { background: #0d1117; }
    ::-webkit-scrollbar-thumb { background: #30363d; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)
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
        st.session_state.selected_prompts = []
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

# 结果预览与润色区域
        if st.session_state.selected_prompts:
            # 分割线
            st.divider()
            st.subheader("🎨 艺术润色成品")
            
            # 润色按钮逻辑
            if st.button("✨ 确认方案并开始润色", type="primary", use_container_width=True):
                with st.spinner("AI 正在注入艺术灵魂..."):
                    # 1. 拼接用户选中的原始标签
                    combined_input = "\n".join([f"方案{i+1}: {p}" for i, p in enumerate(st.session_state.selected_prompts)])
                    
                    # 2. 升级版 System Prompt：强制扩写、画面联想、流畅表达
                    system_prompt = f"""
                    你是一位【顶级纹身艺术总监】。你的任务是将用户提供的零散标签，重构为一段【画面感极强、行文流畅】的视觉描述。

                    【润色规则 - 必须遵守】：
                    1. **拒绝堆砌**：绝对禁止使用“+”号或简单的词语罗列。必须将标签串联成通顺优美的中文长句。
                    2. **细节脑补**：根据标签自动联想细节。
                       - 比如标签是“猫”，你要扩写为“一只神态慵懒的猫，毛发呈现液态金属的光泽”。
                       - 比如标签是“极简”，你要描述“线条干净利落，如同手术刀般精准”。
                    3. **混乱度(Chaos)响应**：当前混乱度参数为 {chaos_level}/100。
                       - 如果 < 30：保持克制，精准还原，注重优雅。
                       - 如果 > 70：大胆加入超现实细节、怪诞的构图、意想不到的元素碰撞（符合 Alien Mood 调性）。
                    4. **格式要求**：每行一个方案，格式严格为：'**方案X：** 你的描述...'。

                    【待润色内容】：
                    {combined_input}
                    """
                    
                    try:
                        res = client.chat.completions.create(
                            model="deepseek-chat",
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": "请开始润色。"}
                            ],
                            temperature=0.7 + (chaos_level / 200) # 让温度随混乱度动态变化
                        ).choices[0].message.content
                        
                        st.session_state.polished_text = res
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"润色失败: {e}")

            # 展示润色结果
            if st.session_state.polished_text:
                st.text_area("润色文案预览：", value=st.session_state.polished_text, height=300)
                
                # 下一步引导
                if st.button("🚀 发送到自动化脚本生成", type="secondary", use_container_width=True):
                    # 自动提取润色后的方案，存入 Tab 3 的缓存
                    st.session_state.auto_input_cache = st.session_state.polished_text
                    st.toast("已发送！请前往【自动化工具】页签生成脚本")          

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
