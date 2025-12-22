import streamlit as st
import requests, base64, random
from openai import OpenAI

# --- 1. 核心配置 ---
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

# 初始化状态，去掉了 img_tags
for key in ['selected_prompts', 'generated_cache', 'polished_text']:
    if key not in st.session_state:
        st.session_state[key] = [] if 'text' not in key else ""

col_main, col_gallery = st.columns([5, 2])

# --- 右侧：资产预览 (素材仓库) ---
with col_gallery:
    st.subheader("📦 资产预览")
    mode = st.radio("模式", ["素材仓库", "灵感成品"], horizontal=True)
    with st.container(height=600):
        if mode == "素材仓库":
            cat = st.selectbox("分类", list(WAREHOUSE.keys()))
            words = get_github_data(WAREHOUSE[cat])
            if words:
                for w in words: st.button(w, key=f"w_{w}", use_container_width=True)
            else:
                st.caption("仓库空空如也")
        else:
            insps = get_github_data(GALLERY_FILE)
            if insps:
                for i in insps: st.write(f"· {i}")
            else:
                st.caption("灵感库为空")

# --- 左侧：核心生成区 ---
with col_main:
    st.info("💡 逻辑：从右侧仓库随机抽取标签组合，再由 DeepSeek 进行艺术化润色。")
    
    # 1. 生成设置
    num = st.slider("一次生成几条创意方案？", 1, 10, 3)
    
    if st.button("🔥 一键生成方案", type="primary", use_container_width=True):
        st.session_state.generated_cache = []
        db_all = {k: get_github_data(v) for k, v in WAREHOUSE.items()}
        
        # 检查是否有素材
        if not any(db_all.values()):
            st.error("素材库里啥也没有，先去首屏存点词进来吧！")
        else:
            for i in range(num):
                sample = []
                for cat in ["Subject", "Action", "Style", "Mood", "Usage"]:
                    if db_all.get(cat):
                        sample.append(random.choice(db_all[cat]))
                
                # 直接拼接标签作为原始提示词
                base_p = " + ".join(sample)
                st.session_state.generated_cache.append(base_p)
            st.rerun()

    # 2. 方案展示与多选
    if st.session_state.generated_cache:
        st.divider()
        st.subheader("🎲 随机组合结果")
        cols = st.columns(2)
        for idx, prompt in enumerate(st.session_state.generated_cache):
            with cols[idx % 2]:
                is_sel = prompt in st.session_state.selected_prompts
                with st.container(border=True):
                    st.markdown(f"**组合 {idx+1}** {' ✅' if is_sel else ''}")
                    st.caption(prompt)
                    if st.button("选择" if not is_sel else "取消", key=f"sel_{idx}", use_container_width=True):
                        if is_sel: st.session_state.selected_prompts.remove(prompt)
                        else: st.session_state.selected_prompts.append(prompt)
                        st.rerun()

    # 3. 润色区
    if st.session_state.selected_prompts:
        st.divider()
        if st.button("✨ DeepSeek 艺术润色", type="primary", use_container_width=True):
            with st.spinner("DeepSeek 正在构思优美的提示词..."):
                combined = "\n".join([f"方案{i+1}: {p}" for i, p in enumerate(st.session_state.selected_prompts)])
                system_prompt = (
                    "你是一个顶级纹身艺术顾问。将这些原始标签转化为有画面感、优美且符合 Midjourney/DALL-E 风格的中文提示词。"
                    "请严格按照'**方案X：** 内容'的格式输出，不要有任何其他废话。"
                )
                res = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": combined}]
                ).choices[0].message.content
                st.session_state.polished_text = res

    # 4. 最终结果预览与传送
    if st.session_state.get('polished_text'):
        st.success("✅ 润色完成")
        final_content = st.text_area("最终成果预览（可手动微调）：", st.session_state.polished_text, height=250)
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("💾 存入云端灵感库", use_container_width=True):
                current = get_github_data(GALLERY_FILE)
                # 提取正文，排除掉 **方案X：** 这种标题
                new_lines = [l.strip() for l in final_content.split('\n') if l.strip() and '方案' not in l]
                current.extend(new_lines)
                if save_to_github(GALLERY_FILE, current):
                    st.balloons()
                    st.success("已保存至 gallery/inspirations.txt")
        
        with c2:
            if st.button("🚀 发送到自动化跑图", type="primary", use_container_width=True):
                st.session_state.auto_input_cache = final_content
                st.switch_page("pages/02_automation.py")
