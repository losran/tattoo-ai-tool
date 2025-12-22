import streamlit as st
import requests, base64, random, time
from openai import OpenAI

# --- 1. 配置 (保持与 app.py 一致) ---
client = OpenAI(api_key=st.secrets["DEEPSEEK_KEY"], base_url="https://api.deepseek.com")
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
HF_TOKEN = st.secrets["HF_TOKEN"]
REPO = "losran/tattoo-ai-tool"
FILES = {
    "Subject": "subjects.txt", "Action": "actions.txt", 
    "Style": "styles.txt", "Mood": "moods.txt", "Usage": "usage.txt",
    "灵感库": "inspirations.txt"
}

# --- 2. 工具函数 (修复版) ---
def get_image_desc(image_bytes):
    # 换成目前最稳定的官方 BLIP 模型
    API_URL = "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-large"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    
    for i in range(3): # 尝试 3 次
        try:
            response = requests.post(API_URL, headers=headers, data=image_bytes, timeout=20)
            if response.status_code == 200:
                res_json = response.json()
                return res_json[0].get('generated_text')
            elif response.status_code == 503:
                st.warning(f"⏳ AI 正在排队起床，请等 10 秒... ({i+1}/3)")
                time.sleep(10)
                continue
            else:
                st.error(f"抱脸接口返回代码: {response.status_code}")
                return None
        except Exception as e:
            st.error(f"连接超时，正在重试... {str(e)}")
            time.sleep(2)
    return None

def get_data(filename):
    url = f"https://api.github.com/repos/{REPO}/contents/data/{filename}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        return [line.strip() for line in base64.b64decode(resp.json()['content']).decode().splitlines() if line.strip()]
    return []

def sync_data(filename, data_list):
    url = f"https://api.github.com/repos/{REPO}/contents/data/{filename}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    get_resp = requests.get(url, headers=headers).json()
    content_str = "\n".join(list(set(data_list)))
    b64_content = base64.b64encode(content_str.encode()).decode()
    requests.put(url, headers=headers, json={"message": "save inspiration", "content": b64_content, "sha": get_resp.get('sha')})

def polish_prompts_chinese(prompt_list):
    combined_input = "\n".join([f"方案{i+1}: {p}" for i, p in enumerate(prompt_list)])
    system_prompt = "你是一个顶级的纹身艺术顾问。将标签转化为优美、有画面感的中文提示词。不要废话。"
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
st.title("🎨 创意引擎 & 云端灵感库")
col_left, col_main, col_right = st.columns([1, 4, 2])

with col_right:
    st.subheader("📦 仓库预览")
    cat_view = st.selectbox("切换分类", list(FILES.keys()))
    words = get_data(FILES[cat_view])
    with st.container(height=600):
        if words:
            for w in words: st.text(w)
        else: st.caption("暂无数据")

with col_main:
    # --- 图片反推区 ---
    with st.expander("📸 参考图提取", expanded=True):
        up_file = st.file_uploader("上传图", type=["jpg", "png", "jpeg"])
        if up_file:
            st.image(up_file, width=200)
            if st.button("🔍 开始反推标签", use_container_width=True):
                with st.spinner("AI 正在解析图片，这可能需要一会儿..."):
                    desc = get_image_desc(up_file.getvalue())
                    if desc:
                        # 核心修正：如果拿到了英文描述，用 DeepSeek 拆解它
                        res = client.chat.completions.create(
                            model="deepseek-chat",
                            messages=[{"role": "user", "content": f"请把这段英文描述拆解为 Subject:词|Action:词|Style:词|Mood:词|Usage:词。描述是：{desc}"}]
                        ).choices[0].message.content
                        st.session_state.img_tags = res
                        st.success(f"解析成功：{res}")
                    else:
                        st.error("解析失败，可能是抱脸服务器开小差了，请再试一次。")

    st.divider()
    
    # --- 生成区 ---
    num_gen = st.slider("生成数量", 1, 10, 3)
    if st.button("🔥 一键生成", type="primary", use_container_width=True):
        st.session_state.generated_cache = []
        db_all = {k: get_data(v) for k, v in FILES.items() if k != "灵感库"}
        for i in range(num_gen):
            sample = [random.choice(db_all[cat]) if db_all.get(cat) else " " for cat in ["Subject", "Action", "Style", "Mood", "Usage"]]
            base_p = " + ".join(sample)
            # 融合图片标签
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

    # --- 汇总与润色 ---
    if st.session_state.selected_prompts:
        st.divider()
        if st.button("✨ DeepSeek 艺术润色", type="primary", use_container_width=True):
            with st.spinner("DeepSeek 正在构思..."):
                st.session_state.polished_text = polish_prompts_chinese(st.session_state.selected_prompts)
        
        if st.session_state.polished_text:
            st.text_area("最终成果：", st.session_state.polished_text, height=200)
            if st.button("💾 存入云端灵感库", use_container_width=True):
                current_insp = get_data(FILES["灵感库"])
                new_lines = [line.strip() for line in st.session_state.polished_text.split('\n') if line.strip()]
                current_insp.extend(new_lines)
                sync_data(FILES["灵感库"], current_insp)
                st.balloons()
