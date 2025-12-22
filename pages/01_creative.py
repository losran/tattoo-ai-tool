import streamlit as st
import requests, base64, random, time
from openai import OpenAI

# --- 1. 基础配置 ---
client = OpenAI(api_key=st.secrets["DEEPSEEK_KEY"], base_url="https://api.deepseek.com")
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
HF_TOKEN = st.secrets["HF_TOKEN"]
REPO = "losran/tattoo-ai-tool"

# 路径配置
WAREHOUSE = {
    "Subject": "data/subjects.txt", "Action": "data/actions.txt", 
    "Style": "data/styles.txt", "Mood": "data/moods.txt", "Usage": "data/usage.txt"
}
GALLERY_FILE = "gallery/inspirations.txt"

# --- 2. 工具函数 ---
def get_github_data(path):
    url = f"https://api.github.com/repos/{REPO}/contents/{path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        return [line.strip() for line in base64.b64decode(resp.json()['content']).decode().splitlines() if line.strip()]
    return []

def save_to_github(path, data_list):
    url = f"https://api.github.com/repos/{REPO}/contents/{path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    get_resp = requests.get(url, headers=headers).json()
    content_str = "\n".join(list(set(data_list)))
    b64_content = base64.b64encode(content_str.encode()).decode()
    requests.put(url, headers=headers, json={"message": "update", "content": b64_content, "sha": get_resp.get('sha')})

def get_image_desc(image_bytes):
    """
    换用目前官方最稳定的模型接口，彻底解决 410 报错
    """
    API_URL = "https://api-inference.huggingface.co/models/nlpconnect/vit-gpt2-image-captioning"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    try:
        response = requests.post(API_URL, headers=headers, data=image_bytes, timeout=30)
        if response.status_code == 200:
            res = response.json()
            # 兼容不同模型的返回格式
            if isinstance(res, list): return res[0].get('generated_text')
            return res.get('generated_text')
        elif response.status_code == 503:
            st.warning("⏳ AI 还在准备中，请等 10 秒后重试...")
            return "RETRY"
        return None
    except: return None

def polish_prompts_chinese(prompt_list):
    combined_input = "\n".join([f"方案{i+1}: {p}" for i, p in enumerate(prompt_list)])
    system_prompt = "你是一个纹身艺术顾问，将标签转化为有画面感的中文提示词。"
    try:
        res = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": combined_input}]
        )
        return res.choices[0].message.content
    except: return "润色失败"

# --- 3. UI 布局 ---
st.title("🎨 创意引擎")

# 初始化状态
for key in ['selected_prompts', 'generated_cache', 'polished_text', 'img_tags']:
    if key not in st.session_state:
        st.session_state[key] = [] if 'text' not in key else ""

col_main, col_gallery = st.columns([5, 2])

with col_gallery:
    st.subheader("📦 资产预览")
    mode = st.radio("模式", ["素材仓库", "灵感成品"], horizontal=True)
    with st.container(height=600):
        if mode == "素材仓库":
            cat = st.selectbox("分类", list(WAREHOUSE.keys()))
            words = get_github_data(WAREHOUSE[cat])
            for w in words: st.button(w, key=f"w_{w}", use_container_width=True)
        else:
            insps = get_github_data(GALLERY_FILE)
            for i in insps: st.write(f"· {i}")

with col_main:
    # 图片提取区
    with st.expander("📸 参考图提取", expanded=True):
        up = st.file_uploader("上传纹身参考图", type=['jpg','png','jpeg'])
        if up:
            st.image(up, width=200)
            if st.button("🔍 开始提取特征", use_container_width=True):
                with st.spinner("AI 正在解析图片..."):
                    desc = get_image_desc(up.getvalue())
                    if desc and desc != "RETRY":
                        res = client.chat.completions.create(
                            model="deepseek-chat",
                            messages=[{"role": "user", "content": f"拆解为中文标签(Subject|Action|Style|Mood|Usage)：{desc}"}]
                        ).choices[0].message.content
                        st.session_state.img_tags = res
                        st.success(f"解析成功：{res}")

    # 生成方案区
    num = st.slider("一次生成几条创意？", 1, 10, 3)
    if st.button("🔥 一键生成方案", type="primary", use_container_width=True):
        st.session_state.generated_cache = []
        db_all = {k: get_github_data(v) for k, v in WAREHOUSE.items()}
        for i in range(num):
            sample = [random.choice(db_all[cat]) if db_all.get(cat) else " " for cat in ["Subject", "Action", "Style", "Mood", "Usage"]]
            base_p = " + ".join(sample)
            final_p = f"参考图特征({st.session_state.img_tags}) + {base_p}" if st.session_state.img_tags else base_p
            st.session_state.generated_cache.append(final_p)
        st.rerun()

    # 方案选择
    if st.session_state.generated_cache:
        cols = st.columns(2)
        for idx, prompt in enumerate(st.session_state.generated_cache):
            with cols[idx % 2]:
                is_sel = prompt in st.session_state.selected_prompts
                with st.container(border=True):
                    st.markdown(f"**方案 {idx+1}** {' ✅' if is_sel else ''}")
                    st.caption(prompt)
                    if st.button("勾选" if not is_sel else "取消", key=f"sel_{idx}", use_container_width=True):
                        if is_sel: st.session_state.selected_prompts.remove(prompt)
                        else: st.session_state.selected_prompts.append(prompt)
                        st.rerun()

    # 结果展示与跳转
    if st.session_state.get('polished_text'):
        st.success("✅ 润色完成")
        final_content = st.text_area("最终成果预览：", st.session_state.polished_text, height=200)
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("💾 存入云端灵感库", use_container_width=True):
                current = get_github_data(GALLERY_FILE)
                new_lines = [l.strip() for l in final_content.split('\n') if l.strip()]
                current.extend(new_lines)
                save_to_github(GALLERY_FILE, current)
                st.success("已存入 gallery/inspirations.txt")
        
        with c2:
            # 🚀 补齐了跳转逻辑
            if st.button("🚀 发送到自动化跑图", type="primary", use_container_width=True):
                st.session_state.auto_input_cache = final_content
                st.switch_page("pages/02_automation.py")
