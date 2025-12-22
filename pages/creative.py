import streamlit as st
import requests, base64, random
from openai import OpenAI

# --- 1. 配置 (保持与 app.py 一致) ---
client = OpenAI(api_key=st.secrets["DEEPSEEK_KEY"], base_url="https://api.deepseek.com")
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
HF_TOKEN = st.secrets.get("HF_TOKEN", "") # 读取你刚才存的抱脸 Token
REPO = "losran/tattoo-ai-tool"
FILES = {
    "Subject": "subjects.txt", "Action": "actions.txt", 
    "Style": "styles.txt", "Mood": "moods.txt", "Usage": "usage.txt"
}

# --- 2. 工具函数 (新增图片反推) ---
def get_image_desc(image_bytes):
    """调用 Hugging Face 免费模型识别图片"""
    API_URL = "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-large"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    response = requests.post(API_URL, headers=headers, data=image_bytes)
    if response.status_code == 200:
        return response.json()[0]['generated_text']
    return None

def get_data(filename):
    url = f"https://api.github.com/repos/{REPO}/contents/data/{filename}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        return [line.strip() for line in base64.b64decode(resp.json()['content']).decode().splitlines() if line.strip()]
    return []

def polish_prompts_chinese(prompt_list):
    combined_input = "\n".join([f"方案{i+1}: {p}" for i, p in enumerate(prompt_list)])
    system_prompt = "你是一个顶级的纹身艺术顾问。将标签转化为一段优美、有画面感的中文提示词。"
    try:
        res = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": f"润色标签：\n{combined_input}"}],
            temperature=0.7
        )
        return res.choices[0].message.content
    except: return "润色失败"

# --- 3. 初始化状态 ---
for k in ['selected_prompts', 'generated_cache', 'polished_text', 'img_tags']:
    if k not in st.session_state: st.session_state[k] = [] if 'text' not in k else ""

# --- 4. 页面布局 ---
st.title("🎨 创意灵感引擎 + 📸 图片反推")
col_left, col_main, col_right = st.columns([1, 4, 2])

with col_right:
    st.subheader("📦 素材预览")
    cat_view = st.selectbox("查看维度", list(FILES.keys()))
    words = get_data(FILES[cat_view])
    with st.container(height=600):
        for w in words: st.button(w, key=f"btn_{w}", use_container_width=True)

with col_main:
    # --- 图片反推区 ---
    with st.expander("📸 上传参考图提取标签", expanded=True):
        up_file = st.file_uploader("选择纹身图", type=["jpg", "png", "jpeg"])
        if up_file:
            st.image(up_file, width=200)
            if st.button("🔍 开始反推标签", use_container_width=True):
                with st.spinner("AI 正在看图..."):
                    desc = get_image_desc(up_file.getvalue())
                    if desc:
                        # 借助 DeepSeek 把描述变成 5 维标签
                        res = client.chat.completions.create(
                            model="deepseek-chat",
                            messages=[{"role": "user", "content": f"把这段英文描述拆解为 Subject:词|Action:词|Style:词|Mood:词|Usage:词。描述：{desc}"}]
                        ).choices[0].message.content
                        st.session_state.img_tags = res
                st.success(f"反推结果：{st.session_state.img_tags}")

    st.divider()
    
    # --- 混合生成区 ---
    st.markdown("### 🎲 灵感拼装")
    num_gen = st.slider("生成几条创意？", 1, 10, 3)
    
    if st.button("🔥 一键生成创意提示词", type="primary", use_container_width=True):
        st.session_state.generated_cache = []
        db_all = {k: get_data(v) for k, v in FILES.items()}
        for i in range(num_gen):
            # 基础随机抽样
            sample = [random.choice(db_all[cat]) if db_all[cat] else f"[{cat}]" for cat in ["Subject", "Action", "Style", "Mood", "Usage"]]
            base_p = " + ".join(sample)
            # 如果有图片反推的标签，融合在一起
            final_p = f"参考图特征({st.session_state.img_tags}) + {base_p}" if st.session_state.img_tags else base_p
            st.session_state.generated_cache.append(final_p)
        st.rerun()

    # --- 后续展示与润色逻辑 (与之前一致) ---
    if st.session_state.generated_cache:
        st.subheader("💡 灵感方案库")
        cols = st.columns(2)
        for idx, prompt in enumerate(st.session_state.generated_cache):
            with cols[idx % 2]:
                is_sel = prompt in st.session_state.selected_prompts
                with st.container(border=True):
                    st.markdown(f"**方案 {idx+1}** {' ✅' if is_sel else ''}")
                    st.info(prompt)
                    if st.button("选择" if not is_sel else "取消", key=f"sel_{idx}", use_container_width=True):
                        if is_sel: st.session_state.selected_prompts.remove(prompt)
                        else: st.session_state.selected_prompts.append(prompt)
                        st.rerun()

    if st.session_state.selected_prompts:
        st.divider()
        if st.button("✨ DeepSeek 艺术润色", type="primary", use_container_width=True):
            with st.spinner("构思中..."):
                st.session_state.polished_text = polish_prompts_chinese(st.session_state.selected_prompts)
        if st.session_state.polished_text:
            st.text_area("最终中文提示词：", st.session_state.polished_text, height=200)
