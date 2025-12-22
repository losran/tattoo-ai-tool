import streamlit as st
import requests, base64, random, time
from openai import OpenAI

# --- 1. 配置 ---
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
st.title("🎨 创意引擎")

for key in ['selected_prompts', 'generated_cache', 'polished_text', 'manual_editor']:
    if key not in st.session_state:
        st.session_state[key] = [] if 'text' not in key else ""

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
                if st.button("➕ 导入到组合输入框", use_container_width=True):
                    existing = st.session_state.manual_editor
                    st.session_state.manual_editor = f"{existing} {' '.join(selected_items)}".strip()
                    st.rerun()
                if st.button(f"🗑️ 删除所选 {len(selected_items)} 项", type="primary", use_container_width=True):
                    remaining = [w for w in words if w not in selected_items]
                    save_to_github(WAREHOUSE[cat], remaining); st.rerun()

# --- 左侧：核心生成区 ---
with col_main:
    # 1. 灵感配置 (始终显示)
    st.subheader("📝 灵感调配")
    st.session_state.manual_editor = st.text_area("手动编辑或从右侧导入关键词：", value=st.session_state.manual_editor, height=80)
    
    chaos_level = st.slider("✨ 创意混乱参数 (Chaos)", 0, 100, 50)
    
    c_n1, c_n2 = st.columns([1, 2])
    with c_n1: num = st.number_input("生成数量", 1, 15, 3)
    with c_n2:
        st.caption("快捷设置")
        q_cols = st.columns(3)
        if q_cols[0].button("3"): st.session_state.gn = 3
        if q_cols[1].button("5"): st.session_state.gn = 5
        if q_cols[2].button("10"): st.session_state.gn = 10
        if 'gn' in st.session_state: num = st.session_state.gn; del st.session_state.gn

    if st.button("🔥 激发创意组合", type="primary", use_container_width=True):
        st.session_state.polished_text = "" # 清空上一次的润色，显示筛选区
        st.session_state.generated_cache = []
        db_all = {k: get_github_data(v) for k, v in WAREHOUSE.items()}
        for _ in range(num):
            manual_words = st.session_state.manual_editor.split()
            # 简单逻辑：混乱度越高，加入的随机维度越多
            extra_count = 1 if chaos_level < 30 else (3 if chaos_level < 70 else 5)
            extra = [random.choice(db_all[random.choice(list(db_all.keys()))]) for _ in range(extra_count) if any(db_all.values())]
            st.session_state.generated_cache.append(" + ".join(manual_words + extra))
        st.rerun()

    # 📍 优化点：条件渲染“方案筛选”区
    # 只有当【有缓存结果】且【还没润色成果】时，才显示筛选列表
    if st.session_state.generated_cache and not st.session_state.get('polished_text'):
        st.divider()
        st.subheader("🎲 方案筛选")
        cols = st.columns(2)
        for idx, p in enumerate(st.session_state.generated_cache):
            with cols[idx % 2]:
                is_sel = p in st.session_state.selected_prompts
                with st.container(border=True):
                    st.markdown(f"**组合 {idx+1}** {' ✅' if is_sel else ''}")
                    st.caption(p)
                    if st.button("选中" if not is_sel else "取消", key=f"sel_{idx}", use_container_width=True):
                        if is_sel: st.session_state.selected_prompts.remove(p)
                        else: st.session_state.selected_prompts.append(p)
                        st.rerun()

        if st.session_state.selected_prompts:
            if st.button("✨ 对已选方案进行 DeepSeek 艺术润色", type="primary", use_container_width=True):
                with st.spinner("正在构思成品..."):
                    combined = "\n".join([f"方案{i+1}: {p}" for i, p in enumerate(st.session_state.selected_prompts)])
                    system = f"你是一个纹身艺术顾问。将标签转化为中文提示词。混乱度{chaos_level}/100。格式：'**方案X：** 内容'。"
                    res = client.chat.completions.create(model="deepseek-chat", messages=[{"role": "system", "content": system}, {"role": "user", "content": combined}]).choices[0].message.content
                    st.session_state.polished_text = res
                    st.rerun()

    # 📍 优化点：展示最终成果 (润色成功后，这里就是唯一主角)
    if st.session_state.get('polished_text'):
        st.divider()
        st.subheader("🎨 艺术润色成品")
        final_content = st.text_area("最终文案预览：", st.session_state.polished_text, height=300)
        
        c_btn1, c_btn2, c_btn3 = st.columns([1, 1, 1])
        with c_btn1:
            if st.button("💾 存入灵感成品库", use_container_width=True):
                current = get_github_data(GALLERY_FILE)
                new = [l.strip() for l in final_content.split('\n') if l.strip() and '方案' not in l]
                current.extend(new); save_to_github(GALLERY_FILE, current); st.success("已存档")
        with c_btn2:
            if st.button("🚀 发送到自动化跑图", type="primary", use_container_width=True):
                st.session_state.auto_input_cache = final_content
                st.switch_page("pages/02_automation.py")
        with c_btn3:
            # 加个“返回”按钮，清空结果，让筛选区重新出现
            if st.button("🔄 重新筛选/组合", use_container_width=True):
                st.session_state.polished_text = ""
                st.rerun()
