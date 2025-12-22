import streamlit as st
import requests, base64, random
from openai import OpenAI

# --- 1. 基础配置 (千万不要改动这部分) ---
client = OpenAI(api_key=st.secrets["DEEPSEEK_KEY"], base_url="https://api.deepseek.com")
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO = "losran/tattoo-ai-tool"
FILES = {
    "Subject": "subjects.txt", "Action": "actions.txt", 
    "Style": "styles.txt", "Mood": "moods.txt", "Usage": "usage.txt"
}

# --- 2. 工具函数 ---
def get_data(filename):
    url = f"https://api.github.com/repos/{REPO}/contents/data/{filename}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        return [line.strip() for line in base64.b64decode(resp.json()['content']).decode().splitlines() if line.strip()]
    return []

def polish_prompts_chinese(prompt_list):
    combined_input = "\n".join([f"方案{i+1}: {p}" for i, p in enumerate(prompt_list)])
    system_prompt = "你是一个顶级的纹身艺术顾问。将标签转化为一段优美、有画面感的中文提示词。每条方案只输出一段话，不要废话。"
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"请润色以下纹身创意标签：\n{combined_input}"}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"润色失败: {str(e)}"

# --- 3. 初始化状态 ---
if 'selected_prompts' not in st.session_state:
    st.session_state.selected_prompts = []
if 'generated_cache' not in st.session_state:
    st.session_state.generated_cache = []
if 'polished_text' not in st.session_state:
    st.session_state.polished_text = ""

# --- 4. 页面布局 ---
st.title("🎨 创意灵感引擎")
col_left, col_main, col_right = st.columns([1, 4, 2])

with col_right:
    st.subheader("📦 素材预览")
    cat_view = st.selectbox("查看维度", list(FILES.keys()))
    words = get_data(FILES[cat_view])
    with st.container(height=600):
        for w in words:
            st.button(w, key=f"btn_{w}", use_container_width=True)

with col_main:
    st.markdown("### 🎲 灵感拼装")
    num_gen = st.slider("生成几条创意？", 1, 10, 3)
    
    if st.button("🔥 一键生成创意提示词", type="primary", use_container_width=True):
        st.session_state.generated_cache = []
        db_all = {k: get_data(v) for k, v in FILES.items()}
        for i in range(num_gen):
            sample = [random.choice(db_all[cat]) if db_all[cat] else f"[{cat}]" for cat in ["Subject", "Action", "Style", "Mood", "Usage"]]
            st.session_state.generated_cache.append(" + ".join(sample))
        st.rerun()

    if st.session_state.generated_cache:
        st.subheader("💡 灵感方案库")
        cols = st.columns(2)
        for idx, prompt in enumerate(st.session_state.generated_cache):
            with cols[idx % 2]:
                is_selected = prompt in st.session_state.selected_prompts
                with st.container(border=True):
                    st.markdown(f"**方案 {idx+1}** {' ✅' if is_selected else ''}")
                    st.info(prompt)
                    btn_label = "取消选择" if is_selected else "勾选此方案"
                    if st.button(btn_label, key=f"sel_btn_{idx}", use_container_width=True):
                        if prompt in st.session_state.selected_prompts:
                            st.session_state.selected_prompts.remove(prompt)
                        else:
                            st.session_state.selected_prompts.append(prompt)
                        st.rerun()

    if st.session_state.selected_prompts:
        st.divider()
        st.markdown(f"### 🛒 已选中 ({len(st.session_state.selected_prompts)}) 条方案")
        c1, c2 = st.columns(2)
        if c1.button("✨ DeepSeek 艺术润色", type="primary", use_container_width=True):
            with st.spinner("构思中..."):
                st.session_state.polished_text = polish_prompts_chinese(st.session_state.selected_prompts)
        if c2.button("🗑️ 清空选中", use_container_width=True):
            st.session_state.selected_prompts = []
            st.session_state.polished_text = ""
            st.rerun()

        if st.session_state.polished_text:
            st.success("✅ 润色完成！")
            st.text_area("润色后的提示词：", st.session_state.polished_text, height=200)
