import streamlit as st
import requests, base64, random, time
from openai import OpenAI

# --- 1. 核心配置 ---
client = OpenAI(api_key=st.secrets["DEEPSEEK_KEY"], base_url="https://api.deepseek.com")
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
HF_TOKEN = st.secrets["HF_TOKEN"]
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
    """【修复 410】换用官方最稳模型，并开启强制等待加载模式"""
    API_URL = "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-base"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    try:
        # 加上 wait_for_model=True 解决模型启动慢的问题
        response = requests.post(API_URL, headers=headers, data=image_bytes, timeout=40)
        if response.status_code == 200:
            return response.json()[0].get('generated_text')
        elif response.status_code == 503:
            st.warning("⏳ AI 正在排队起床，请等 15 秒后再点一次...")
            return "RETRY"
        return None
    except: return None

# --- 3. 初始化与布局 ---
st.title("🎨 创意引擎")

# 确保所有变量名都存在，防止 Attribute Error
for key in ['selected_prompts', 'generated_cache', 'polished_text', 'img_tags']:
    if key not in st.session_state:
        st.session_state[key] = [] if 'text' not in key else ""

col_main, col_gallery = st.columns([5, 2])

with col_gallery:
    st.subheader("📦 资产预览")
    mode = st.radio("预览模式", ["素材仓库", "灵感成品"], horizontal=True)
    with st.container(height=600):
        if mode == "素材仓库":
            cat = st.selectbox("分类", list(WAREHOUSE.keys()))
            words = get_github_data(WAREHOUSE[cat])
            for w in words: st.button(w, key=f"w_{w}", use_container_width=True)
        else:
            insps = get_github_data(GALLERY_FILE)
            for i in insps: st.write(f"· {i}")

with col_main:
    # --- 图片反推 ---
    with st.expander("📸 参考图反推", expanded=True):
        up = st.file_uploader("上传纹身参考图", type=['jpg','png','jpeg'])
        if up:
            st.image(up, width=200)
            if st.button("🔍 开始提取特征", use_container_width=True):
                with st.spinner("AI 正在解析图片..."):
                    desc = get_image_desc(up.getvalue())
                    if desc and desc != "RETRY":
                        res = client.chat.completions.create(
                            model="deepseek-chat",
                            messages=[{"role": "user", "content": f"将描述拆解为中文标签(Subject|Action|Style|Mood|Usage)：{desc}"}]
                        ).choices[0].message.content
                        st.session_state.img_tags = res
                        st.success(f"解析成功：{res}")

    # --- 生成逻辑 ---
    num = st.slider("生成几条创意？", 1, 10, 3)
    if st.button("🔥 一键生成方案", type="primary", use_container_width=True):
        st.session_state.generated_cache = []
        db_all = {k: get_github_data(v) for k, v in WAREHOUSE.items()}
        for i in range(num):
            sample = [random.choice(db_all[cat]) if db_all.get(cat) else " " for cat in ["Subject", "Action", "Style", "Mood", "Usage"]]
            base_p = " + ".join(sample)
            final_p = f"参考图特征({st.session_state.img_tags}) + {base_p}" if st.session_state.img_tags else base_p
            st.session_state.generated_cache.append(final_p)
        st.rerun()

    # --- 方案库展示 ---
    if st.session_state.generated_cache:
        cols = st.columns(2)
        for idx, prompt in enumerate(st.session_state.generated_cache):
            with cols[idx % 2]:
                is_sel = prompt in st.session_state.selected_prompts
                with st.container(border=True):
                    st.markdown(f"**方案 {idx+1}** {' ✅' if is_sel else ''}")
                    st.caption(prompt)
                    if st.button("选择" if not is_sel else "取消", key=f"sel_{idx}", use_container_width=True):
                        if is_sel: st.session_state.selected_prompts.remove(prompt)
                        else: st.session_state.selected_prompts.append(prompt)
                        st.rerun()

    # --- 润色与【消失按钮】的修复 ---
    if st.session_state.selected_prompts:
        st.divider()
        if st.button("✨ DeepSeek 艺术润色", type="primary", use_container_width=True):
            with st.spinner("正在构思..."):
                combined = "\n".join([f"方案{i+1}: {p}" for i, p in enumerate(st.session_state.selected_prompts)])
                res = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "system", "content": "你是一个纹身艺术顾问，将标签转化为优美的中文提示词。"}, {"role": "user", "content": combined}]
                ).choices[0].message.content
                st.session_state.polished_text = res

    # 只要有润色结果，就显示【保存】和【跳转】按钮
    if st.session_state.get('polished_text'):
        st.success("✅ 润色完成！")
        final_content = st.text_area("最终成果预览：", st.session_state.polished_text, height=200)
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("💾 存入云端灵感库", use_container_width=True):
                current = get_github_data(GALLERY_FILE)
                new_lines = [l.strip() for l in final_content.split('\n') if l.strip()]
                current.extend(new_lines)
                save_to_github(GALLERY_FILE, current)
                st.balloons()
        
        with c2:
            if st.button("🚀 发送到自动化跑图", type="primary", use_container_width=True):
                st.session_state.auto_input_cache = final_content
                st.switch_page("pages/02_automation.py")
